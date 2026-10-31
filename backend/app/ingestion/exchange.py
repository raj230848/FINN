from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import httpx
from .http import HEADERS, SourceError

ANNOUNCEMENTS_PAGE = 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'

def fetch_announcements(tickers: set[str], days: int = 7) -> list[dict]:
    if not 1 <= days <= 31:
        raise ValueError('Announcement windows must be between 1 and 31 days.')
    now = datetime.now(ZoneInfo('Asia/Kolkata'))
    try:
        with httpx.Client(headers={**HEADERS, 'Accept': 'application/json', 'Referer': ANNOUNCEMENTS_PAGE}, timeout=15, follow_redirects=True) as client:
            # NSE uses cookies established on its public site. Honour blocking;
            # no CAPTCHA bypass or unbounded retries.
            client.get('https://www.nseindia.com/')
            response = client.get('https://www.nseindia.com/api/corporate-announcements', params={'index':'equities','from_date':(now-timedelta(days=days)).strftime('%d-%m-%Y'),'to_date':now.strftime('%d-%m-%Y')})
            if response.status_code != 200:
                raise SourceError(f'NSE announcements returned HTTP {response.status_code}; automated access is restricted. Cached filings remain available.')
            raw = response.json()
            if not isinstance(raw, list):
                raise SourceError('NSE returned an unexpected response format.')
    except (httpx.HTTPError, ValueError) as exc:
        if isinstance(exc, SourceError):
            raise
        raise SourceError(f'NSE announcements unavailable ({type(exc).__name__}).') from exc
    results = []
    for row in raw:
        ticker = str(row.get('symbol', '')).upper()
        if ticker not in tickers:
            continue
        date_value = row.get('an_dt') or row.get('sort_date') or ''
        parsed = None
        for fmt in ('%d-%b-%Y %H:%M:%S','%d-%m-%Y %H:%M:%S','%Y-%m-%d %H:%M:%S','%d-%b-%Y %H:%M'):
            try:
                parsed = datetime.strptime(date_value, fmt).replace(tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(ZoneInfo('UTC')).replace(tzinfo=None)
                break
            except (ValueError, TypeError):
                continue
        if parsed is None:
            continue  # Never assign the fetch date to an undated filing.
        title = str(row.get('desc') or row.get('attchmntText') or '').strip()
        if not title:
            continue
        filing_id = row.get('seq_id') or row.get('an_seq') or row.get('broadcast_id') or row.get('id')
        results.append({'ticker':ticker,'title':title,'published_at':parsed,
                        'source_filing_id':str(filing_id)[:160] if filing_id is not None else None,
                        'source_url':row.get('attchmntFile') or ANNOUNCEMENTS_PAGE,
                        'text':str(row.get('attchmntText') or '')})
    return results
