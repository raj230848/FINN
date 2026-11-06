"""Refresh the public sourced feed without republishing the Sites frontend.

Only public provider data is written. Provider failures retain the prior rows
and their original timestamps. No runtime database or private settings are read.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import math
import re
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
ISSUER_HOSTS = {"INFY": {"www.infosys.com"}, "WIPRO": {"www.wipro.com"},
                "TCS": {"www.tcs.com"}, "HCLTECH": {"www.hcltech.com"}}


def valid_history(rows, today):
    if not rows:
        raise ValueError("Empty market history")
    points = []
    for row in rows:
        day = row["date"]
        close, volume = row["close"], row["volume"]
        if (day > today or day.weekday() > 4 or not math.isfinite(close)
                or close <= 0 or not isinstance(volume, int) or volume < 0):
            raise ValueError("Invalid market observation")
        points.append({"date": day.isoformat(), "close": close, "volume": volume})
    points.sort(key=lambda point: point["date"])
    if len({point["date"] for point in points}) != len(points):
        raise ValueError("Duplicate market session")
    return points[-65:]


def sync_reviewed_guidance(snapshot, manifest, now):
    """Publish reviewed issuer facts only; a feed check is not a new source review."""
    from app.services.calculations import guidance_comparison
    result = json.loads(json.dumps(snapshot))
    tickers = {company["ticker"] for company in result["companies"]}
    allowed = ISSUER_HOSTS
    grouped = {}
    for row in manifest["guidance"]:
        if row.get("ticker") in tickers:
            grouped.setdefault(row["ticker"], []).append(row)
    errors = []
    for ticker, rows in grouped.items():
        try:
            items, seen = [], set()
            for row in rows:
                if any(not isinstance(row.get(key), str) or not row[key].strip() for key in
                       ("revision", "statement_date", "target_period", "metric", "unit", "statement")):
                    raise ValueError("Missing guidance context")
                if row.get("actual") is None and (row.get("actual_url") is not None or row.get("actual_page") is not None):
                    raise ValueError("Pending outcome cannot have a reported-result link")
                for url_key, page_key in (("guidance_url", "guidance_page"), ("actual_url", "actual_page")):
                    if url_key == "actual_url" and row.get("actual") is None:
                        continue
                    source = urlsplit(row[url_key])
                    if (source.scheme != "https" or source.hostname not in allowed.get(ticker, set()) or source.username
                            or type(row[page_key]) is not int or row[page_key] < 1):
                        raise ValueError("Unverified guidance source")
                if (datetime.fromisoformat(row["statement_date"]).date() > now.date()
                        or any(isinstance(row[key], bool) or not math.isfinite(row[key]) for key in ("low", "high"))
                        or row["low"] > row["high"]):
                    raise ValueError("Invalid guidance range or date")
                if row.get("actual") is not None and (isinstance(row["actual"], bool)
                        or any(row.get(a, row.get(b)) != row.get(b) for a, b in
                            (("actual_period", "target_period"), ("actual_metric", "metric"),
                             ("actual_unit", "unit"), ("actual_basis", "basis")))):
                    raise ValueError("Reported result does not match guidance")
                key = (row["statement_date"], row["target_period"], row["metric"], row["unit"], row.get("basis"))
                if key in seen:
                    raise ValueError("Duplicate guidance revision")
                seen.add(key)
                comparison = guidance_comparison(row["low"], row["high"], row["actual"]) if row.get("actual") is not None else {"status": "pending", "deviation_pp": None, "midpoint_deviation_pp": None}
                fields = ("ticker", "revision", "statement_date", "target_period", "metric", "unit", "basis",
                          "low", "high", "actual", "statement", "guidance_url", "guidance_page", "actual_url", "actual_page")
                items.append({**{key: row[key] for key in fields if key in row}, **comparison})
            result.setdefault("guidance", {})[ticker] = {"items": sorted(items, key=lambda row: row["statement_date"]),
                "note": "Source-reviewed guidance. New disclosures appear after source review. Compare matching periods, metrics, units and currency bases. Future outcomes remain pending."}
        except (KeyError, TypeError, ValueError, OverflowError):
            errors.append(ticker)
    all_items = [row for group in result.get("guidance", {}).values() for row in group["items"]]
    result["guidance_refresh"] = {"checked_at": now.isoformat(), "source": "reviewed_primary_source_manifest",
        "automatic_discovery": False, "failed_companies": sorted(errors),
        "reviewed_companies": sum(bool(group["items"]) for group in result.get("guidance", {}).values()),
        "comparisons": len(all_items), "latest_statement_date": max((row["statement_date"] for row in all_items), default=None)}
    return result


def sync_reviewed_financials(snapshot, manifest, now):
    """Publish reviewed financial tables with matching fiscal-quarter comparisons."""
    from app.services.calculations import percent_change
    result = json.loads(json.dumps(snapshot))
    covered = {company["ticker"] for company in result["companies"]}
    grouped, errors = {}, []
    for row in manifest["financials"]:
        if row.get("ticker") in covered:
            grouped.setdefault(row["ticker"], []).append(row)
    for ticker, rows in grouped.items():
        try:
            history, seen = [], set()
            for row in rows:
                url = urlsplit(row["source_url"])
                if (url.scheme != "https" or url.hostname not in ISSUER_HOSTS.get(ticker, set()) or url.username
                        or type(row["page"]) is not int or row["page"] < 1
                        or not re.fullmatch(r"20\d{2}-Q[1-4]", row["period"])
                        or not row["basis"] or not row["currency"]):
                    raise ValueError("Invalid reviewed financial source")
                key = (row["period"], row["basis"], row["currency"])
                if key in seen:
                    raise ValueError("Duplicate financial quarter")
                seen.add(key)
                metrics = {name: row["metrics"].get(name) for name in ("revenue", "ebitda", "pbt", "pat")}
                if any(value is not None and (isinstance(value, bool) or not math.isfinite(value)) for value in metrics.values()):
                    raise ValueError("Invalid financial metric")
                if "_review_flags" in row["metrics"]:
                    flags = row["metrics"]["_review_flags"]
                    if not isinstance(flags, list) or any(not isinstance(flag, str) for flag in flags):
                        raise ValueError("Invalid accounting review notes")
                    metrics["_review_flags"] = flags
                history.append({**{key: row[key] for key in ("period", "basis", "currency", "source_url", "page")}, "metrics": metrics})
            history.sort(key=lambda row: row["period"], reverse=True)
            current = history[0]
            by_period = {row["period"]: row for row in history if row["basis"] == current["basis"] and row["currency"] == current["currency"]}
            year, quarter = int(current["period"][:4]), int(current["period"][-1])
            previous_period = f"{year}-Q{quarter-1}" if quarter > 1 else f"{year-1}-Q4"
            prior_year = f"{year-1}-Q{quarter}"
            output = []
            for metric in ("revenue", "ebitda", "pbt", "pat"):
                current_value = current["metrics"].get(metric)
                previous = by_period.get(previous_period, {}).get("metrics", {}).get(metric)
                last_year = by_period.get(prior_year, {}).get("metrics", {}).get(metric)
                output.append({"metric": metric, "current": current_value, "previous": previous, "last_year": last_year,
                    "qoq": percent_change(current_value, previous), "yoy": percent_change(current_value, last_year)})
            result.setdefault("financials", {})[ticker] = {"rows": output, "current_period": current["period"],
                "previous_period": previous_period, "last_year_period": prior_year, "basis": current["basis"], "currency": current["currency"],
                "periods": list(by_period), "history": history, "sources": history,
                "review_flags": current["metrics"].get("_review_flags", []),
                "note": "Historical reviewed figures; source review may lag new filings. EBITDA is unavailable without reviewed evidence. Comparisons require matching periods, units and accounting bases; missing quarters stay unavailable."}
        except (KeyError, TypeError, ValueError, OverflowError):
            errors.append(ticker)
    result["financials_refresh"] = {"checked_at": now.isoformat(), "automatic_discovery": False,
        "failed_companies": sorted(errors), "reviewed_companies": sum(bool(data.get("rows")) for data in result.get("financials", {}).values()),
        "reviewed_periods": {ticker: data.get("current_period") for ticker, data in result.get("financials", {}).items() if data.get("rows")}}
    return result


def refresh(snapshot, fetch_prices, fetch_announcements, classify, now, force_market=False):
    """Return a validated update, retaining each independently failed source."""
    from zoneinfo import ZoneInfo
    local = now.astimezone(ZoneInfo("Asia/Kolkata"))
    checked_at = now.isoformat()
    result = json.loads(json.dumps(snapshot))
    previous = snapshot.get("refresh_status", {})
    status = {"checked_at": checked_at, "prices": {}, "filings": {}}
    quotes = {quote["ticker"]: quote for quote in result["quotes"]}
    # Always fetch after the cutoff; during the day reuse a successfully checked
    # recent history until a new completed session could exist.
    last_price_check = previous.get("market_last_successful_at")
    recent = False
    if last_price_check:
        try:
            recent = now - datetime.fromisoformat(last_price_check.replace("Z", "+00:00")) < timedelta(hours=12)
        except (TypeError, ValueError):
            pass
    retry_tickers = {ticker for ticker, source in previous.get("prices", {}).items() if not source.get("ok")}
    full_market = force_market or not recent or (local.hour, local.minute) >= (18, 30)
    needs_market = full_market or bool(retry_tickers)

    def market(company):
        ticker = company["ticker"]
        try:
            rows = fetch_prices(ticker)
            points = valid_history(rows, local.date())
            expected_url = f"https://finance.yahoo.com/quote/{ticker}.NS/history/"
            if any(row.get("source_url") != expected_url for row in rows):
                raise ValueError("Unexpected market source")
            old = quotes[ticker].get("history", [])
            if old and points[-1]["date"] < old[-1]["date"]:
                raise ValueError("Provider returned older history")
            return ticker, points, None
        except Exception as error:
            return ticker, None, type(error).__name__

    if needs_market:
        selected = result["companies"] if full_market else [company for company in result["companies"] if company["ticker"] in retry_tickers]
        status["prices"] = {ticker: {"ok": True, "retained_completed_sessions": True} for ticker in quotes}
        with ThreadPoolExecutor(max_workers=3) as pool:
            for ticker, points, error in pool.map(market, selected):
                status["prices"][ticker] = {"ok": points is not None}
                if points is None:
                    status["prices"][ticker]["error"] = error
                    continue
                quotes[ticker].update(history=points,
                    source_url=f"https://finance.yahoo.com/quote/{ticker}.NS/history/",
                    fetched_at=checked_at)
        status["market_last_successful_at"] = checked_at if all(row["ok"] for row in status["prices"].values()) else previous.get("market_last_successful_at")
    else:
        status["prices"] = {ticker: {"ok": True, "retained_completed_sessions": True} for ticker in quotes}
        status["market_last_successful_at"] = last_price_check
    dates = sorted({point["date"] for quote in result["quotes"] for point in quote["history"]})
    result["market_sessions"] = dates
    result["market_as_of"] = dates[-1] if dates else None

    try:
        tickers = {company["ticker"] for company in result["companies"]}
        rows = fetch_announcements(tickers, days=31)
        existing = {(f["ticker"], f["source_url"], f["published_at"]): f for f in result["announcements"]}
        next_id = max(result.get("next_filing_id", 1), max((f["id"] for f in existing.values()), default=0) + 1)
        for row in rows:
            url = row["source_url"]
            parsed = urlsplit(url)
            if row["ticker"] not in tickers or parsed.scheme != "https" or parsed.hostname not in {"nsearchives.nseindia.com", "archives.nseindia.com", "www.nseindia.com"}:
                continue
            date = row["published_at"].replace(tzinfo=timezone.utc).isoformat()
            if row["published_at"].replace(tzinfo=timezone.utc) > now + timedelta(minutes=5):
                continue
            key = (row["ticker"], url, date)
            if key in existing:
                continue
            detail = classify(row["title"], row.get("text", ""))
            # Keep the public archive compact and direct the reader to the issuer.
            detail["summary"] = "Open the original NSE filing for the full disclosure."
            existing[key] = {"id": next_id, "ticker": row["ticker"], "title": row["title"],
                "published_at": date, "source_url": url, "mode": "sourced",
                "analysis_method": "FINN filing classification", **detail}
            next_id += 1
        result["next_filing_id"] = next_id
        cutoff = now - timedelta(days=31)
        result["announcements"] = sorted((f for f in existing.values()
            if datetime.fromisoformat(f["published_at"].replace("Z", "+00:00")) >= cutoff),
            key=lambda f: (f["published_at"], f["id"]), reverse=True)
        result["filings_as_of"] = checked_at
        status["filings"] = {"ok": True, "matched": len(rows)}
        status["filings_last_successful_at"] = checked_at
    except Exception as error:
        status["filings"] = {"ok": False, "error": type(error).__name__}
        status["filings_last_successful_at"] = previous.get("filings_last_successful_at")
    successes = [row["ok"] for row in status["prices"].values()] + [status["filings"]["ok"]]
    status["status"] = "complete" if all(successes) else "partial" if any(successes) else "failed"
    result["refresh_status"] = status
    result["as_of"] = checked_at
    return result


def main():
    from app.ingestion.market import fetch_prices
    from app.ingestion.exchange import fetch_announcements
    from app.services.materiality import classify
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=ROOT / "public-site/public/data/snapshot-sourced.json")
    parser.add_argument("--force-market", action="store_true", help="Check market sources even within the intraday cooldown.")
    parser.add_argument("--guidance-only", action="store_true", help="Publish reviewed guidance without checking market or filing providers.")
    args = parser.parse_args()
    snapshot = json.loads(args.file.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    result = snapshot if args.guidance_only else refresh(snapshot, fetch_prices, fetch_announcements, classify, now, args.force_market)
    manifest = json.loads((ROOT / "backend/data/primary/verified.json").read_text(encoding="utf-8"))
    result = sync_reviewed_guidance(result, manifest, now)
    result = sync_reviewed_financials(result, manifest, now)
    temporary = args.file.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(args.file)
    status = result.get("refresh_status", {})
    if args.guidance_only:
        print(json.dumps(result["guidance_refresh"]))
        return
    print(json.dumps({"status": status["status"], "market_as_of": result["market_as_of"],
        "market_sources_ok": sum(row["ok"] for row in status["prices"].values()),
        "filings_ok": status["filings"]["ok"], "checked_at": status["checked_at"]}))


if __name__ == "__main__":
    main()
