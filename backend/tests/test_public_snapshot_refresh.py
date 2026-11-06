import importlib.util
import copy
import json
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


def guidance_manifest():
    return json.loads((ROOT / "backend/data/primary/verified.json").read_text(encoding="utf-8"))


def test_guidance_publishes_covered_reviewed_rows_and_keeps_future_outcomes_pending():
    before = fixture()
    before["companies"].append({"ticker": "WIPRO"})
    now = datetime(2026, 11, 6, 7, tzinfo=timezone.utc)
    result = module.sync_reviewed_guidance(before, guidance_manifest(), now)
    assert len(result["guidance"]["INFY"]["items"]) == 4
    wipro = result["guidance"]["WIPRO"]["items"]
    assert len(wipro) == 4
    assert [row["status"] for row in wipro] == ["achieved", "achieved", "achieved", "pending"]
    assert wipro[-1]["actual"] is None
    assert wipro[-1]["actual_url"] is None
    assert wipro[-1]["deviation_pp"] is None
    assert result["guidance_refresh"]["latest_statement_date"] == "2026-10-15"
    assert result["guidance_refresh"]["failed_companies"] == []
    assert "HCLTECH" not in result["guidance"]
    assert "guidance" not in before
    again = module.sync_reviewed_guidance(result, guidance_manifest(), now)
    assert again == result


def test_guidance_invalid_sources_periods_and_ranges_retain_previous_issuer_records():
    now = datetime(2026, 11, 6, 7, tzinfo=timezone.utc)
    before = module.sync_reviewed_guidance(fixture(), guidance_manifest(), now)
    for invalid in ({"guidance_url": "https://example.com/report.pdf"},
                    {"actual_period": "FY99"}, {"actual_metric": "Other metric"},
                    {"actual_basis": "Different currency"}, {"low": 10, "high": 1},
                    {"actual": float("nan")}, {"guidance_page": True},
                    {"statement_date": "2028-01-01"}, {"metric": ""}):
        manifest = copy.deepcopy(guidance_manifest())
        row = next(item for item in manifest["guidance"] if item["ticker"] == "INFY")
        row.update(invalid)
        result = module.sync_reviewed_guidance(before, manifest, now)
        assert result["guidance"]["INFY"] == before["guidance"]["INFY"]
        assert result["guidance_refresh"]["failed_companies"] == ["INFY"]


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
