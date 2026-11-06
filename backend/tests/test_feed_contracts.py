"""Controlled provider payloads complement the separate real-network audit."""
from datetime import date, datetime
from types import SimpleNamespace

import httpx
import pandas as pd
import pytest

from app.ingestion import exchange, market
from app.ingestion.http import SourceError


def nse_response(monkeypatch, payload=None, status=200, invalid_json=False):
    real = httpx.Client
    def handler(request):
        if request.url.path == '/':
            return httpx.Response(200)
        if invalid_json:
            return httpx.Response(200, text='not json')
        return httpx.Response(status, json=payload)
    monkeypatch.setattr(exchange.httpx, 'Client', lambda **kw: real(transport=httpx.MockTransport(handler), **kw))


@pytest.mark.parametrize('days', [0, 32])
def test_exchange_window_bounds(days):
    with pytest.raises(ValueError):
        exchange.fetch_announcements({'INFY'}, days)


@pytest.mark.parametrize('payload,status,invalid_json', [({}, 200, False), ([None], 200, False), ([1], 200, False), ([], 403, False), ([], 200, True)])
def test_exchange_bad_envelope_is_source_error(monkeypatch, payload, status, invalid_json):
    nse_response(monkeypatch, payload, status, invalid_json)
    with pytest.raises(SourceError):
        exchange.fetch_announcements({'INFY'})


@pytest.mark.parametrize('stamp', ['30-Oct-2026 12:30:00', '30-10-2026 12:30:00', '2026-10-30 12:30:00', '30-Oct-2026 12:30'])
def test_exchange_supported_dates_and_primary_identity(monkeypatch, stamp):
    nse_response(monkeypatch, [{'symbol': 'infy', 'an_dt': stamp, 'desc': 'Results', 'seq_id': 123}])
    rows = exchange.fetch_announcements({'INFY'})
    assert len(rows) == 1
    assert rows[0]['published_at'] == datetime(2026, 10, 30, 7)
    assert rows[0]['source_filing_id'] == '123'
    assert rows[0]['source_url'] == exchange.ANNOUNCEMENTS_PAGE


def test_exchange_never_invents_date_or_title(monkeypatch):
    nse_response(monkeypatch, [
        {'symbol': 'TCS', 'an_dt': '30-Oct-2026 12:30', 'desc': 'Other issuer'},
        {'symbol': 'INFY', 'an_dt': 'invalid', 'desc': 'No date'},
        {'symbol': 'INFY', 'an_dt': '30-Oct-2026 12:30', 'desc': ''},
    ])
    assert exchange.fetch_announcements({'INFY'}) == []


def market_frame(monkeypatch, frame):
    monkeypatch.setattr(market.yf, 'Ticker', lambda _: SimpleNamespace(history=lambda **kw: frame))
    monkeypatch.setattr(market, 'complete_session', lambda day: day <= date(2026, 10, 30))


def test_prices_exclude_incomplete_and_nonfinite_rows(monkeypatch):
    frame = pd.DataFrame({'Close': [10, 12, float('nan'), -1, 15, 20], 'Volume': [100, 200, 1, 2, -1, 500]}, index=pd.date_range('2026-10-26', periods=6))
    market_frame(monkeypatch, frame)
    rows = market.fetch_prices('infy')
    assert [r['close'] for r in rows] == [10, 12]
    assert all('INFY.NS' in r['source_url'] for r in rows)


@pytest.mark.parametrize('frame', [pd.DataFrame(), pd.DataFrame({'Close': [10]}, index=pd.date_range('2026-10-30', periods=1)), pd.DataFrame({'Close': ['bad', 12], 'Volume': [10, 20]}, index=pd.date_range('2026-10-29', periods=2)), pd.DataFrame({'Close': [10, 12], 'Volume': [10, 20]}, index=['bad', 'also bad'])])
def test_malformed_or_insufficient_prices_are_source_errors(monkeypatch, frame):
    market_frame(monkeypatch, frame)
    with pytest.raises(SourceError):
        market.fetch_prices('INFY')


def test_market_network_failure_is_sanitized(monkeypatch):
    def fail(_):
        raise RuntimeError('sensitive provider detail')
    monkeypatch.setattr(market.yf, 'Ticker', fail)
    with pytest.raises(SourceError, match='RuntimeError') as error:
        market.fetch_prices('INFY')
    assert 'sensitive' not in str(error.value)


@pytest.mark.parametrize('info', [{'quoteType': 'ETF'}, {'quoteType': 'EQUITY', 'currency': 'USD', 'longName': 'Issuer'}, {'quoteType': 'EQUITY', 'currency': 'INR', 'longName': 'Issuer', 'exchange': 'BSE'}, None])
def test_unverified_company_is_rejected(monkeypatch, info):
    monkeypatch.setattr(market.yf, 'Ticker', lambda _: SimpleNamespace(get_info=lambda: info))
    with pytest.raises(SourceError):
        market.resolve_company('INFY')


def test_verified_nse_company_metadata(monkeypatch):
    monkeypatch.setattr(market.yf, 'Ticker', lambda _: SimpleNamespace(get_info=lambda: {'quoteType': 'EQUITY', 'currency': 'INR', 'longName': 'Infosys Limited', 'exchange': 'NSI'}))
    assert market.resolve_company('infy') == {'ticker': 'INFY', 'name': 'Infosys Limited', 'sector': 'Unclassified', 'website': '', 'verified': True}


@pytest.mark.parametrize('attachment',['-','',None,'N/A'])
def test_exchange_missing_attachment_links_to_real_exchange_page(monkeypatch,attachment):
    nse_response(monkeypatch,[{'symbol':'INFY','an_dt':'30-Oct-2026 12:30','desc':'Exchange update','attchmntFile':attachment}])
    row=exchange.fetch_announcements({'INFY'})[0]
    assert row['source_url']==exchange.ANNOUNCEMENTS_PAGE
