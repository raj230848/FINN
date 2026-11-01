"""Durable first-observed events, separate from current threshold crossings."""
from sqlalchemy import select
from ..models import SignalEvent, Announcement, Preference, Company

def record_event(db, *, event_key, ticker, mode, kind, severity, title,
                 explanation, occurred_at, source_url=None):
    if db.scalar(select(SignalEvent.id).where(SignalEvent.event_key==event_key)):
        return
    db.add(SignalEvent(event_key=event_key,ticker=ticker,mode=mode,kind=kind,
                       severity=severity,title=title,explanation=explanation,
                       occurred_at=occurred_at,source_url=source_url))
    db.flush()
    from .push import queue_event
    queue_event(db, db.scalar(select(SignalEvent).where(SignalEvent.event_key==event_key)))

def record_filing_events(db):
    pref = db.get(Preference,1)
    for row in db.scalars(select(Announcement).join(Company).where(Company.watched.is_(True))):
        if row.priority == 'low':
            continue
        if pref and pref.companies and row.ticker not in pref.companies:
            continue
        if row.priority != 'high' and not row.needs_review and not (pref and row.category in pref.categories):
            continue
        record_event(db,event_key=f'filing:{row.mode}:{row.fingerprint}',ticker=row.ticker,
                     mode=row.mode,kind='filing',severity=row.priority,title=row.title,
                     explanation=row.why_matters,occurred_at=row.published_at,source_url=row.source_url)
