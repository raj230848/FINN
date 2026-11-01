from sqlalchemy import select, func
from ..models import Announcement, IngestionCoverage

def describe_coverage(db, mode, tickers, start, end):
    if mode == 'demo':
        return {'partial_coverage':False,'kind':'synthetic_replay',
                'message':'Fixed synthetic scenarios, not complete exchange history.'}
    windows = list(db.scalars(select(IngestionCoverage).where(IngestionCoverage.ticker.in_(tickers))))
    complete = bool(tickers)
    for ticker in tickers:
        cursor = start
        for window in sorted((w for w in windows if w.ticker==ticker),key=lambda w:w.start_at):
            if window.end_at < cursor: continue
            if window.start_at > cursor: break
            cursor = max(cursor,window.end_at)
        if cursor < end: complete = False
    first = db.scalar(select(func.min(Announcement.ingested_at)).where(Announcement.mode=='sourced',Announcement.ticker.in_(tickers)))
    latest = max((w.end_at for w in windows),default=None)
    unknown = db.scalar(select(func.count()).select_from(Announcement).where(Announcement.mode=='sourced',Announcement.ticker.in_(tickers),Announcement.ingested_at.is_(None)))
    return {'partial_coverage':not complete,'kind':'best_effort_exchange',
            'first_observed_at':first.isoformat()+'Z' if first else None,
            'last_successful_fetch_at':latest.isoformat()+'Z' if latest else None,
            'unknown_ingestion_dates':unknown,
            'message':'Requested dates are not fully covered by successful fetches; missing filings may exist.' if not complete else 'Requested dates were fetched. Exchange responses are best effort, not an exhaustive disclosure guarantee.'}
