import math
import yfinance as yf
from .http import SourceError
from ..schemas import normalize_ticker
from ..services.calculations import complete_session

def fetch_prices(ticker: str) -> list[dict]:
    ticker = normalize_ticker(ticker)
    try:
        frame = yf.Ticker(ticker + '.NS').history(period='6mo', interval='1d', auto_adjust=True, timeout=12)
    except Exception as exc:
        raise SourceError(f'Yahoo Finance could not provide {ticker}.NS ({type(exc).__name__}).') from exc
    if frame.empty:
        raise SourceError(f'No market data returned for {ticker}.NS. Check the NSE symbol or retry after provider rate limits clear.')
    rows = []
    for stamp, row in frame.iterrows():
        day = stamp.date()
        close, volume = float(row['Close']), float(row['Volume'])
        if complete_session(day) and math.isfinite(close) and close > 0 and math.isfinite(volume) and volume >= 0:
            rows.append({'date': day, 'close': close, 'volume': int(volume), 'source_url': f'https://finance.yahoo.com/quote/{ticker}.NS/history/'})
    if len(rows) < 2:
        raise SourceError('Not enough completed trading sessions. Today is excluded until 18:30 IST.')
    return rows

def resolve_company(ticker: str) -> dict:
    """Identifiers only. Yahoo's fundamentals are never research evidence."""
    ticker = normalize_ticker(ticker)
    try:
        obj = yf.Ticker(ticker + '.NS')
        info = obj.get_info()
        if info.get('quoteType') != 'EQUITY' or info.get('currency') != 'INR' or not info.get('longName'):
            raise SourceError('The provider did not verify this symbol as an Indian equity.')
        if info.get('exchange') not in ('NSI', 'NSE'):
            raise SourceError('This prototype accepts NSE equities only.')
        return {'ticker': ticker, 'name': info['longName'], 'sector': info.get('sector', 'Unclassified'), 'website': info.get('website', ''), 'verified': True}
    except SourceError:
        raise
    except Exception as exc:
        raise SourceError(f'Cannot verify NSE ticker {ticker}: {type(exc).__name__}. No company profile was invented.') from exc
