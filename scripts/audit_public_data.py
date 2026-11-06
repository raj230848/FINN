"""Read-only public-data audit. Never reads .env, runtime databases or credentials."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "public-site/public/data/snapshot-sourced.json")
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts/audit-2026-11-06/data-audit.json")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "backend/data/primary/verified.json").read_text(encoding="utf-8"))
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "market_as_of": data.get("market_as_of"),
              "filings_as_of": data.get("filings_as_of"), "sections": {}, "limits": []}
    quotes = data["quotes"]
    report["sections"]["market"] = {"companies": len(quotes), "observations": sum(len(q["history"]) for q in quotes),
        "sessions": {q["ticker"]: q["history"][-1]["date"] if q["history"] else None for q in quotes},
        "source": "Yahoo Finance adjusted daily history; completed sessions only", "live_comparison": []}
    announcements = data["announcements"]
    report["sections"]["signals"] = {"count": len(announcements), "unsourced_records": sum(f["mode"] != "sourced" or not f.get("source_url") for f in announcements),
        "duplicate_ids": len(announcements)-len({f["id"] for f in announcements}),
        "latest": max((f["published_at"] for f in announcements), default=None), "source_comparison": None,
        "classification": "Deterministic headline classification; not a prediction or verified financial impact."}
    financials = {}
    for ticker, block in data["financials"].items():
        if not block.get("rows"):
            continue
        rows = [r for r in manifest["financials"] if r["ticker"] == ticker]
        latest = max(rows, key=lambda row: row["period"])
        differences = [r["metric"] for r in block["rows"] if r["current"] != latest["metrics"].get(r["metric"])]
        financials[ticker] = {"period": block.get("current_period"), "latest_reviewed_period": latest["period"],
            "currency": block["currency"], "differences": differences, "history_count": len(block.get("history", [])),
            "freshness": "Reviewed historical coverage; newer unreviewed issuer reports may exist."}
    report["sections"]["financials"] = financials
    report["sections"]["guidance"] = {ticker: {"count": len(group["items"]), "latest_statement": max(r["statement_date"] for r in group["items"]),
        "pending": sum(r["actual"] is None for r in group["items"])} for ticker, group in data["guidance"].items() if group["items"]}
    extracts = json.loads((ROOT / "public-site/public/data/research.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "backend/data/primary/catalog.json").read_text(encoding="utf-8"))
    catalog_by_url = {row["url"]: row for row in catalog}
    def normalize(text):
        return re.sub(r"[^a-z0-9]", "", text.lower())
    import fitz
    evidence = []
    for extract in extracts:
        url = extract["url"].split("#")[0]
        source = catalog_by_url.get(url)
        status = "not_reverified"
        if source and (ROOT / "backend/data/primary" / source["file"]).exists():
            path = ROOT / "backend/data/primary" / source["file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != source["checksum"]:
                status = "checksum_mismatch"
            elif path.suffix == ".pdf":
                with fitz.open(path) as pdf:
                    text = pdf[extract["page"]-1].get_text()
                    status = "page_text_matches" if normalize(extract["excerpt"]) in normalize(text) else "text_requires_review"
            else:
                from bs4 import BeautifulSoup
                text = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").get_text(" ")
                status = "page_text_matches" if normalize(extract["excerpt"]) in normalize(text) else "text_requires_review"
        evidence.append({"ticker": extract["ticker"], "topic": extract["topic"], "page": extract["page"], "source": url, "status": status})
    report["sections"]["research"] = {"extracts": len(extracts), "covered_issuers": sorted({r["ticker"] for r in extracts}),
        "evidence_checks": evidence, "ai_model_connected_on_public_site": False,
        "freshness": "Prepared historical extracts, not automatically updated issuer research."}
    report["sections"]["watchlist_saved_notifications"] = {"persistence": "Device-local browser storage", "notifications": "Source-dated first-observed events; not background push delivery."}
    if args.live:
        from app.ingestion.market import fetch_prices
        from app.ingestion.exchange import fetch_announcements
        def compare(quote):
            try:
                rows = {row["date"].isoformat(): row for row in fetch_prices(quote["ticker"])}
                mismatches, compared = [], 0
                for point in quote["history"]:
                    if point["date"] not in rows:
                        mismatches.append({"date": point["date"], "reason": "source_session_missing"})
                        continue
                    compared += 1
                    row = rows[point["date"]]
                    if abs(row["close"] - point["close"]) > .011 or row["volume"] != point["volume"]:
                        mismatches.append({"date": point["date"], "reason": "source_price_or_volume_differs"})
                return {"ticker": quote["ticker"], "status": "matched" if not mismatches else "differs", "compared": compared, "mismatches": mismatches,
                    "provider_latest_session": max(rows, default=None)}
            except Exception as error:
                return {"ticker": quote["ticker"], "status": "provider_unavailable", "error": type(error).__name__}
        with ThreadPoolExecutor(max_workers=3) as pool:
            report["sections"]["market"]["live_comparison"] = list(pool.map(compare, quotes))
        try:
            rows = fetch_announcements({company["ticker"] for company in data["companies"]}, days=31)
            keys = {(r["ticker"], r["source_url"], r["published_at"].replace(tzinfo=timezone.utc)) for r in rows}
            matches = sum((f["ticker"], f["source_url"], datetime.fromisoformat(f["published_at"].replace("Z", "+00:00"))) in keys for f in announcements)
            report["sections"]["signals"]["source_comparison"] = {"provider_rows": len(rows), "snapshot_rows_matched": matches,
                "unmatched": len(announcements)-matches, "note": "NSE response may change between checks; unmatched rows require review."}
        except Exception as error:
            report["sections"]["signals"]["source_comparison"] = {"status": "provider_unavailable", "error": type(error).__name__}
    report["limits"] = ["Re-fetching Yahoo verifies reproducibility against that provider, not independent exchange-price certification.",
        "A stored primary URL alone does not establish that every source PDF has been read in full during this audit.",
        "Historical financials, guidance and research are not guaranteed to include the latest issuer disclosure."]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"report": str(args.out), "market": [(r["ticker"], r["status"]) for r in report["sections"]["market"]["live_comparison"]],
        "filings": report["sections"]["signals"]["source_comparison"], "research_text_checks": {state: sum(e["status"] == state for e in evidence) for state in sorted({e["status"] for e in evidence})}}))


if __name__ == "__main__":
    main()
