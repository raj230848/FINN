"""One-worker refresh reservation, shared freshness and bounded failure cooldown."""
from datetime import datetime, timedelta, timezone
from threading import Lock
from zoneinfo import ZoneInfo
from sqlalchemy import select,func
from ..config import settings
from ..models import Company,Price,SyncRun,IngestionCoverage,utcnow

RESERVATION_LOCK=Lock()


def refresh_state(db,now=None):
    now=now or utcnow();interval=max(30,settings.sync_interval_minutes)
    latest=db.scalar(select(SyncRun).order_by(SyncRun.id.desc()).limit(1))
    if not db.scalar(select(func.count()).select_from(Company).where(Company.watched.is_(True))):
        return {'state':'empty_watchlist','run_id':None,'should_refresh':False,'next_check_at':None}
    successful=db.scalar(select(SyncRun).where(SyncRun.completed_at.is_not(None)).order_by(SyncRun.id.desc()).limit(1))
    if latest and latest.completed_at is None:
        return {'state':'in_progress','run_id':latest.id,'should_refresh':False,'next_check_at':None}
    delay=interval
    if latest and latest.result.get('status') in ('partial','failed'):
        recent=list(db.scalars(select(SyncRun).order_by(SyncRun.id.desc()).limit(4)))
        failures=0
        for row in recent:
            if row.result.get('status') not in ('partial','failed'):break
            failures+=1
        delay=min(interval,5*2**max(0,failures-1))
    next_at=latest.completed_at+timedelta(minutes=delay) if latest and latest.completed_at else None
    missing=db.scalar(select(func.count()).select_from(Company).where(Company.watched.is_(True),~Company.ticker.in_(select(Price.ticker).where(Price.mode=='sourced'))))
    due=not next_at or now>=next_at
    # Cooldown applies even with missing data, so failing providers cannot cause a tab storm.
    return {'state':'due' if due else 'retry_later' if latest and latest.result.get('status') in ('partial','failed') else 'fresh','run_id':None,'should_refresh':due,'next_check_at':next_at.isoformat()+'Z' if next_at else None,'missing_companies':missing,'last_completed_at':successful.completed_at.isoformat()+'Z' if successful else None,'interval_minutes':interval}


def reserve_refresh(db,only_if_stale=False,now=None):
    with RESERVATION_LOCK:
        state=refresh_state(db,now)
        if state['state']=='in_progress':return {'id':state['run_id'],'status':'running','reused':True},False
        if only_if_stale and not state['should_refresh']:return {'id':None,'status':state['state'],'freshness':state},False
        run=SyncRun(result={'status':'queued','automatic':only_if_stale});db.add(run);db.commit()
        return {'id':run.id,'status':'queued','reused':False},True


def market_fetch_needed(db,ticker,now=None):
    now=now or utcnow()
    rows=list(db.scalars(select(Price).where(Price.ticker==ticker,Price.mode=='sourced').order_by(Price.date.desc()).limit(2)))
    if len(rows)<2:return True
    latest=rows[0]
    if now-latest.fetched_at>timedelta(hours=24):return True
    local=now.replace(tzinfo=timezone.utc).astimezone(ZoneInfo('Asia/Kolkata'))
    cutoff=local.replace(hour=18,minute=30,second=0,microsecond=0)
    return local>=cutoff and latest.fetched_at<cutoff.astimezone(timezone.utc).replace(tzinfo=None)


def catchup_days(db,now=None):
    now=now or utcnow()
    last=db.scalar(select(func.max(IngestionCoverage.completed_at)))
    base=max(1,min(31,settings.filing_lookback_days))
    return min(31,max(base,(now-last).days+1)) if last else base


def scheduled_refresh():
    from ..database import SessionLocal
    from .sync import run_sync,SYNC_LOCK
    if SYNC_LOCK.locked():return
    with SessionLocal() as db:
        result,created=reserve_refresh(db,only_if_stale=True)
        days=catchup_days(db)
    if created:run_sync(result['id'],filing_days=days,smart=True)
