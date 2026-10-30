"""Reproducible public-source feasibility check; no credentials required."""
from concurrent.futures import ThreadPoolExecutor
import httpx

URLS = [
    'https://www.infosys.com/investors/reports-filings/quarterly-results/2024-2025/q4/documents/ifrs-inr-press-release.pdf',
    'https://www.nseindia.com/api/corporate-announcements?index=equities',
    'https://www.screener.in/company/INFY/consolidated/',
    'https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv',
    'https://www.tcs.com/who-we-are/newsroom/press-release/tcs-financial-results-q4-fy-2025',
    'https://www.persistent.com/wp-content/uploads/2025/06/persistent-annual-report-2025.pdf',
]

def check(url):
    try:
        r = httpx.get(url, timeout=18, headers={'User-Agent':'Mozilla/5.0'}, follow_redirects=True)
        print(r.status_code, len(r.content), url, flush=True)
    except Exception as exc:
        print(type(exc).__name__, url, flush=True)

if __name__ == '__main__':
    list(ThreadPoolExecutor(4).map(check, URLS))
