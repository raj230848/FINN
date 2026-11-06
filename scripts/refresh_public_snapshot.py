"""Refresh the public sourced feed without republishing the Sites frontend.

Only public provider data is written. Provider failures retain the prior rows
and their original timestamps. No runtime database or private settings are read.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


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
        rows = fetch_announcements(tickers, days=7)
        existing = {(f["ticker"], f["source_url"], f["published_at"]): f for f in result["announcements"]}
        next_id = max((f["id"] for f in existing.values()), default=0) + 1
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
    args = parser.parse_args()
    snapshot = json.loads(args.file.read_text(encoding="utf-8"))
    result = refresh(snapshot, fetch_prices, fetch_announcements, classify, datetime.now(timezone.utc), args.force_market)
    temporary = args.file.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(args.file)
    status = result["refresh_status"]
    print(json.dumps({"status": status["status"], "market_as_of": result["market_as_of"],
        "market_sources_ok": sum(row["ok"] for row in status["prices"].values()),
        "filings_ok": status["filings"]["ok"], "checked_at": status["checked_at"]}))


if __name__ == "__main__":
    main()
