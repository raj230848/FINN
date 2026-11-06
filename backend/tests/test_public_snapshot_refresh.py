import importlib.util
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("public_refresh", ROOT / "scripts/refresh_public_snapshot.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    return {
        "companies": [{"ticker": "INFY"}],
        "quotes": [{"ticker": "INFY", "history": [{"date": "2026-11-03", "close": 100, "volume": 20}],
                    "fetched_at": "2026-11-03T12:00:00+00:00"}],
        "announcements": [], "filings_as_of": "2026-11-03T12:00:00+00:00",
    }


def test_public_refresh_retains_each_failed_source_and_its_original_dates():
    before = fixture()
    def fail(*args, **kwargs):
        raise RuntimeError("provider unavailable")
    updated = module.refresh(before, fail, fail, lambda *_: {}, datetime(2026, 11, 6, 15, tzinfo=timezone.utc))
    assert updated["quotes"] == before["quotes"]
    assert updated["filings_as_of"] == before["filings_as_of"]
    assert updated["refresh_status"]["status"] == "failed"
    assert "checked_at" in updated["refresh_status"]
    assert "refresh_status" not in before


def test_public_refresh_updates_prices_and_preserves_failed_filings():
    before = fixture()
    def prices(ticker):
        return [{"date": date(2026, 11, 5), "close": 112, "volume": 42,
                 "source_url": f"https://finance.yahoo.com/quote/{ticker}.NS/history/"}]
    def fail(*args, **kwargs):
        raise RuntimeError("blocked")
    updated = module.refresh(before, prices, fail, lambda *_: {}, datetime(2026, 11, 6, 10, tzinfo=timezone.utc))
    assert updated["market_as_of"] == "2026-11-05"
    assert updated["quotes"][0]["history"][0]["close"] == 112
    assert updated["filings_as_of"] == before["filings_as_of"]
    assert updated["refresh_status"]["status"] == "partial"


def test_public_refresh_rejects_older_history():
    def older(ticker):
        return [{"date": date(2026, 11, 2), "close": 112, "volume": 42,
                 "source_url": f"https://finance.yahoo.com/quote/{ticker}.NS/history/"}]
    before = fixture()
    updated = module.refresh(before, older, lambda *_a, **_k: [], lambda *_: {}, datetime(2026, 11, 6, 15, tzinfo=timezone.utc))
    assert updated["quotes"] == before["quotes"]
    assert updated["refresh_status"]["prices"]["INFY"]["ok"] is False


def test_public_refresh_preserves_filing_ids_on_retry():
    def filings(*args, **kwargs):
        return [{"ticker": "INFY", "title": "Quarterly results", "source_url": "https://nsearchives.nseindia.com/corporate/result.pdf",
                 "published_at": datetime(2026, 11, 5, 10), "text": ""}]
    def fail(*args, **kwargs):
        raise RuntimeError("unavailable")
    now = datetime(2026, 11, 6, 15, tzinfo=timezone.utc)
    once = module.refresh(fixture(), fail, filings, lambda *_: {}, now)
    twice = module.refresh(once, fail, filings, lambda *_: {}, now)
    assert len(twice["announcements"]) == 1
    assert once["announcements"][0]["id"] == twice["announcements"][0]["id"]


def test_recent_success_does_not_hide_failed_ticker_retries():
    before = fixture()
    before["refresh_status"] = {
        "market_last_successful_at": "2026-11-06T06:00:00+00:00",
        "prices": {"INFY": {"ok": False}},
    }
    calls = []
    def prices(ticker):
        calls.append(ticker)
        return [{"date": date(2026, 11, 5), "close": 112, "volume": 42,
                 "source_url": f"https://finance.yahoo.com/quote/{ticker}.NS/history/"}]
    updated = module.refresh(before, prices, lambda *_a, **_k: [], lambda *_: {}, datetime(2026, 11, 6, 7, tzinfo=timezone.utc))
    assert calls == ["INFY"]
    assert updated["refresh_status"]["prices"]["INFY"]["ok"] is True
    assert updated["market_as_of"] == "2026-11-05"
