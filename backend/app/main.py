from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import hmac
import json
import threading
from typing import Annotated
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, Path as ApiPath
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .config import ROOT, settings
from .database import Base, engine, get_db, SessionLocal
from .models import Alert, Announcement, Company, Document, Financial, Guidance, Preference, SyncRun, SignalEvent, PushRecipient, PushDelivery, Price, utcnow
from .schemas import ImportDocumentIn, Mode, PreferencesIn, ResearchIn, WatchIn, normalize_ticker, PushSubscriptionIn, PushDisableIn
from .services.push import configured as push_configured, validate_subscription, deliver_pending
from .seed import DEMO_CLOCK, seed
from .migrations import migrate_schema
from .services.coverage import describe_coverage
from .services.events import record_filing_events
from .rate_limit import allow_request
from .services.alerts import evaluate_alerts, quotes
from .services.calculations import guidance_comparison, percent_change
from .services.documents import discover_documents, ingest_url, store_document
from .services.materiality import CATEGORIES, classify
from .services.research import research
from .services.sync import run_sync, SYNC_LOCK
from .services.operations import metrics, recover_interrupted_syncs
from .services.company_directory import directory
from .services.freshness import reserve_refresh,refresh_state,scheduled_refresh,catchup_days
from .ingestion.http import SourceError
from .ingestion.market import resolve_company

def initialize():
    if settings.public_deployment and not settings.finn_api_token:
        raise RuntimeError("Public deployment requires a backend API token.")
    Base.metadata.create_all(engine)
    migrate_schema(engine)
    with SessionLocal() as db:
        recover_interrupted_syncs(db)
        seed(db)
        # Apply improved rules to retained source rows without overwriting
        # reviewed/model analysis or changing the fixed synthetic replay.
        for row in db.scalars(select(Announcement).where(Announcement.mode=='sourced')):
            if row.analysis_method.startswith('Deterministic'):
                for name, value in classify(row.title, row.text).items():
                    setattr(row, name, value)
        # Bundled original public documents make the demo reproducible offline.
        catalog = ROOT/'data'/'primary'/'catalog.json'
        if catalog.exists():
            for row in json.loads(catalog.read_text(encoding='utf-8')):
                if db.scalar(select(Document.id).where(Document.source_url==row['url'])):
                    continue
                path = ROOT/'data'/'primary'/row['file']
                if path.exists():
                    company = db.get(Company,row['ticker'])
                    company.verified = True
                    store_document(db,company,row['title'],row['period'],row['kind'],row['url'],path.read_bytes())
            db.commit()
        evaluate_alerts(db,'demo')
        record_filing_events(db)
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize()
    scheduler = None
    if settings.enable_scheduler or push_configured():
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(timezone='Asia/Kolkata')
        if settings.enable_scheduler:
            scheduler.add_job(scheduled_refresh,'interval',minutes=max(settings.sync_interval_minutes,30),max_instances=1,coalesce=True)
        if push_configured():
            scheduler.add_job(deliver_pending,'interval',seconds=30,max_instances=1,coalesce=True)
        scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)

app = FastAPI(title='FINN | Investment intelligence',version='1.0.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins.split(','),allow_credentials=False,allow_methods=['GET','POST','PUT','PATCH'],allow_headers=['Content-Type','Authorization'])

@app.middleware('http')
async def token_guard(request: Request, call_next):
    if settings.finn_api_token and request.url.path.startswith('/api/') and request.url.path != '/api/health':
        supplied = request.headers.get('authorization','').removeprefix('Bearer ')
        if not hmac.compare_digest(supplied.encode('utf-8'),settings.finn_api_token.encode('utf-8')):
            metrics.record('api', 'unauthorized')
            return JSONResponse(status_code=401,content={'detail':'API token required.'})
    if settings.public_deployment and (request.method == 'POST' or request.url.path=='/api/company-search'):
        path = request.url.path
        operation,limit = ('search',100) if path=='/api/company-search' else ('research',10) if path=='/api/research' else ('sync',2) if path=='/api/sync' else ('import',3) if path=='/api/documents' or path.endswith('/discover') else ('other',60)
        if operation!='other' and not allow_request(request.client.host if request.client else 'unknown',operation,limit):
            metrics.record('api', 'rate_limited')
            return JSONResponse(status_code=429,headers={'Retry-After':'60'},content={'detail':'Request limit reached. Please try again in a minute.'})
    return await call_next(request)

@app.exception_handler(SourceError)
async def source_error(request, exc):
    return JSONResponse(status_code=422,content={'detail':str(exc)})

DB = Annotated[Session, Depends(get_db)]
RecordId = Annotated[int, ApiPath(ge=1,le=9223372036854775807)]

def symbol(value: str):
    try:
        return normalize_ticker(value)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc

def require_company(db, ticker):
    company = db.get(Company,symbol(ticker))
    if not company:
        raise HTTPException(404,'Company not indexed. Use Discover to verify the NSE ticker and find primary documents.')
    return company

def serial(obj):
    result = {c.name:getattr(obj,c.name) for c in obj.__table__.columns}
    for k,v in result.items():
        if isinstance(v,datetime):
            result[k] = v.isoformat()+'Z'
        elif hasattr(v,'isoformat'):
            result[k] = v.isoformat()
    return result

@app.get('/api/health')
def health():
    return {'status':'ok','version':'1.0.0','ai_configured':bool(settings.gemini_api_key),'ai_provider':'gemini','ai_model':settings.gemini_model,'access_protected':bool(settings.finn_api_token),'scheduler_enabled':settings.enable_scheduler,'demo_clock':DEMO_CLOCK.isoformat()+'Z'}

@app.get('/api/operations')
def operations(db: DB):
    latest = db.scalar(select(SyncRun).order_by(SyncRun.id.desc()).limit(1))
    latest_bars = select(Price.ticker, func.max(Price.date).label('session')).join(Company, Price.ticker==Company.ticker).where(Price.mode=='sourced', Company.watched.is_(True)).group_by(Price.ticker).subquery()
    oldest_fetch, newest_session, covered = db.execute(select(func.min(Price.fetched_at), func.max(Price.date), func.count()).join(latest_bars, (Price.ticker==latest_bars.c.ticker)&(Price.date==latest_bars.c.session)).where(Price.mode=='sourced')).one()
    watched_count = db.scalar(select(func.count()).select_from(Company).where(Company.watched.is_(True)))
    age = max(0, int((utcnow()-oldest_fetch).total_seconds())) if oldest_fetch else None
    delivery_counts = dict(db.execute(select(PushDelivery.state, func.count()).group_by(PushDelivery.state)).all())
    return {'as_of': utcnow().isoformat()+'Z', 'metrics': metrics.snapshot(),
            'sources': {'status': 'not_fetched' if age is None else 'partial' if covered<watched_count else 'stale' if age>86400 else 'recent_fetch', 'covered_companies': covered, 'watched_companies': watched_count, 'oldest_market_fetch': oldest_fetch.isoformat()+'Z' if oldest_fetch else None, 'latest_market_session': newest_session.isoformat() if newest_session else None, 'age_seconds': age, 'note': 'Fetch age is not quote age. EOD session dates and partial filing coverage remain authoritative.'},
            'last_sync': serial(latest) if latest else None,
            'push': {'configured': push_configured(), 'delivery_counts': delivery_counts, 'note': 'Sent means provider acceptance, not confirmed device display.'},
            'worker_model': 'one backend worker; shared desk', 'scheduler_enabled': settings.enable_scheduler}

@app.get('/api/companies')
def companies(db: DB, q: str = ''):
    stmt = select(Company).order_by(Company.watched.desc(),Company.ticker)
    if q:
        stmt = stmt.where(Company.ticker.icontains(q,autoescape=True) | Company.name.icontains(q,autoescape=True))
    return [serial(c) for c in db.scalars(stmt.limit(100))]

@app.get('/api/company-search')
def company_search(background: BackgroundTasks,db: DB,q: str=Query('',max_length=100),limit: int=Query(8,ge=1,le=20)):
    sectors={c.ticker:c.sector for c in db.scalars(select(Company))}
    result=directory.search(q,limit,sectors)
    if result['stale']:background.add_task(directory.refresh)
    return result

@app.patch('/api/companies/{ticker}')
def watch(ticker: str, body: WatchIn, db: DB):
    company = require_company(db,ticker)
    company.watched = body.watched
    db.flush()
    for mode in ('demo','sourced'):
        evaluate_alerts(db,mode)
    db.commit()
    return serial(company)

@app.get('/api/dashboard')
def dashboard(db: DB, mode: Mode = 'demo'):
    pref = db.get(Preference,1)
    monitored = quotes(db,mode,pref.lookback)
    watched = [q['ticker'] for q in monitored]
    clock = DEMO_CLOCK if mode=='demo' else datetime.now(timezone.utc).replace(tzinfo=None)
    filings = list(db.scalars(select(Announcement).where(Announcement.mode==mode,Announcement.ticker.in_(watched),Announcement.published_at>=clock-timedelta(hours=24),Announcement.published_at<=clock)))
    alerts = list(db.scalars(select(Alert).where(Alert.mode==mode,Alert.ticker.in_(watched))))
    latest = db.scalar(select(SyncRun).order_by(SyncRun.id.desc()).limit(1))
    high = sum(x.priority=='high' for x in filings)
    routine = sum(x.priority=='low' for x in filings)
    volumes = sum(x.kind=='volume' for x in alerts)
    return {'mode':mode,'as_of':clock.isoformat()+'Z','companies':monitored,'stats':{'companies':len(monitored),'high_priority':high,'volume_alerts':volumes,'price_alerts':sum(x.kind=='price' for x in alerts),'routine':routine,'total_filings':len(filings),'coverage':sum(x['close'] is not None for x in monitored)},'digest':f'{high} high-priority disclosures and {volumes} unusual-volume signals across your watchlist. {routine} routine filings are tucked away.' if filings or alerts else 'No sourced signals yet. Refresh sources to retrieve completed trading sessions and exchange disclosures.','last_sync':serial(latest) if latest else None,'ai_configured':bool(settings.gemini_api_key),'scheduler_enabled':settings.enable_scheduler,'freshness':refresh_state(db)}

@app.get('/api/announcements')
def announcements(db: DB, mode: Mode='demo', window: str='24h', ticker: str|None=None, category: str|None=None, priority: str|None=None, include_routine: bool=False, start: datetime|None=None, end: datetime|None=None, offset: int=Query(0,ge=0), limit: int=Query(100,ge=1,le=300)):
    clock = DEMO_CLOCK if mode=='demo' else datetime.now(timezone.utc).replace(tzinfo=None)
    if window not in {'24h','7d','30d','custom'}:
        raise HTTPException(422,'Choose 24h, 7d, 30d or custom.')
    if category and category not in CATEGORIES:raise HTTPException(422,'Choose a supported filing category.')
    if priority and priority not in {'high','medium','low'}:raise HTTPException(422,'Choose high, medium or low priority.')
    if window=='custom':
        if not start or not end:
            raise HTTPException(422,'Custom date range requires start and end timestamps.')
        start = start.astimezone(timezone.utc).replace(tzinfo=None) if start.tzinfo else start
        end = end.astimezone(timezone.utc).replace(tzinfo=None) if end.tzinfo else end
        if start>end or end-start>timedelta(days=366):
            raise HTTPException(422,'Start must precede end; maximum range is 366 days.')
    else:
        start,end = clock-timedelta(hours={'24h':24,'7d':168,'30d':720}[window]),clock
    watched = select(Company.ticker).where(Company.watched.is_(True))
    stmt = select(Announcement).where(Announcement.mode==mode,Announcement.ticker.in_(watched),Announcement.published_at>=start,Announcement.published_at<=end)
    if ticker:
        stmt = stmt.where(Announcement.ticker==symbol(ticker))
    if category:
        stmt = stmt.where(Announcement.category==category)
    if priority:
        stmt = stmt.where(Announcement.priority==priority)
    routine_count = db.scalar(select(func.count()).select_from(stmt.where(Announcement.priority=='low').subquery()))
    if not include_routine:
        stmt = stmt.where(Announcement.priority!='low')
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = [serial(a) for a in db.scalars(stmt.order_by(Announcement.score.desc(),Announcement.published_at.desc(),Announcement.id.desc()).offset(offset).limit(limit))]
    monitored = list(db.scalars(watched))
    if ticker:monitored=[t for t in monitored if t==symbol(ticker)]
    return {'items':items,'routine_count':routine_count,'start':start.isoformat()+'Z','end':end.isoformat()+'Z','mode':mode,
            'total':total,'offset':offset,'has_more':offset+len(items)<total,
            'next_offset':offset+len(items) if offset+len(items)<total else None,
            'coverage':describe_coverage(db,mode,monitored,start,end)}

@app.get('/api/alerts')
def alerts(db: DB, mode: Mode='demo'):
    return [serial(a) for a in db.scalars(select(Alert).where(Alert.mode==mode).order_by(Alert.date.desc(),Alert.value.desc()))]

@app.get('/api/notifications')
def notifications(db: DB, mode: Mode='demo', unread_only: bool=False, offset: int=Query(0,ge=0), limit: int=Query(50,ge=1,le=100)):
    base = select(SignalEvent).where(SignalEvent.mode==mode)
    unread = db.scalar(select(func.count()).select_from(base.where(SignalEvent.read_at.is_(None)).subquery()))
    if unread_only: base = base.where(SignalEvent.read_at.is_(None))
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    items = [serial(e) for e in db.scalars(base.order_by(SignalEvent.created_at.desc(),SignalEvent.id.desc()).offset(offset).limit(limit))]
    return {'items':items,'unread_count':unread,'total':total,'has_more':offset+len(items)<total}

@app.get('/api/push/config')
def push_config():
    return {'available':push_configured(),'public_key':settings.vapid_public_key if push_configured() else None}

@app.post('/api/push/subscribe')
def subscribe_push(body: PushSubscriptionIn,db: DB):
    if not push_configured():raise HTTPException(503,'Browser push is not configured on this server.')
    try:subscription=validate_subscription(body.subscription)
    except ValueError as error:raise HTTPException(422,str(error)) from None
    recipient=db.get(PushRecipient,body.device_id)
    if not recipient:
        recipient=PushRecipient(id=body.device_id,subscription=subscription);db.add(recipient)
    else:
        from .models import utcnow
        if not recipient.enabled:recipient.enabled_at=utcnow()
        recipient.subscription=subscription;recipient.enabled=True
    db.commit()
    return {'enabled':True,'enabled_at':recipient.enabled_at.isoformat()+'Z'}

@app.post('/api/push/unsubscribe')
def unsubscribe_push(body: PushDisableIn,db: DB):
    from sqlalchemy import update
    recipient=db.get(PushRecipient,body.device_id)
    if recipient:recipient.enabled=False
    db.execute(update(PushDelivery).where(PushDelivery.recipient_id==body.device_id,PushDelivery.state.in_(['pending','retry'])).values(state='cancelled'))
    db.commit()
    return {'enabled':False}

@app.get('/api/push/status')
def push_status(db: DB,device_id: str=Query(pattern=r'^[A-Za-z0-9_-]{32,64}$')):
    recipient=db.get(PushRecipient,device_id)
    return {'enabled':bool(recipient and recipient.enabled),'delivered':db.scalar(select(func.count()).select_from(PushDelivery).where(PushDelivery.recipient_id==device_id,PushDelivery.state=='sent'))}

@app.get('/api/announcements/{filing_id}/context')
def filing_context(filing_id: RecordId,db: DB):
    import re
    row=db.get(Announcement,filing_id)
    if not row:raise HTTPException(404,'Filing not found.')
    if row.mode=='demo':return {'status':'demo','message':'Simulated filing. No executive background or reported result is asserted.'}
    text=row.title+' '+row.text
    if row.category=='management_change':
        found=re.search(r'brief profile|professional background|previously served|years of experience',row.text,re.I)
        if found:return {'status':'source_excerpt','message':'Issuer-provided excerpt. Person identity and current role still require review of the original filing.','excerpt':row.text[max(0,found.start()-100):found.start()+650],'source_url':row.source_url}
        return {'status':'requires_review','message':'No attributable executive background is present in the exchange description. Review the original filing; no biography or identity was inferred.','source_url':row.source_url}
    if row.category=='results':
        match=re.search(r'\bQ([1-4])\s*FY\s*(20\d{2}|\d{2})\b',text,re.I)
        period=f'{int(match[2]) if len(match[2])==4 else 2000+int(match[2])}-Q{match[1]}' if match else None
        if period and db.scalar(select(Financial.id).where(Financial.ticker==row.ticker,Financial.period==period)):
            return {'status':'reviewed_comparison','comparison_period':period,'message':f'Reviewed {period} numbers are available. Open financial research to check the original period, basis and sources.','source_url':row.source_url}
        return {'status':'requires_review','message':'The filing description has no matched reviewed quarter. Select a reviewed period in financial research; no historical snapshot is represented as this filing’s results.','source_url':row.source_url}
    return {'status':'source_only','message':'Read the original filing to assess the terms and materiality.','source_url':row.source_url}

@app.post('/api/notifications/read-all')
def read_all_notifications(db: DB, mode: Mode='demo'):
    from sqlalchemy import update
    from .models import utcnow
    db.execute(update(SignalEvent).where(SignalEvent.mode==mode,SignalEvent.read_at.is_(None)).values(read_at=utcnow()))
    db.commit()
    return {'status':'read'}

@app.post('/api/notifications/{event_id}/read')
def read_notification(event_id: RecordId, db: DB):
    from .models import utcnow
    event = db.get(SignalEvent,event_id)
    if not event: raise HTTPException(404,'Notification not found.')
    if event.read_at is None: event.read_at = utcnow()
    db.commit()
    return serial(event)

@app.get('/api/preferences')
def preferences(db: DB):
    return {**serial(db.get(Preference,1)),'available_categories':CATEGORIES}

@app.put('/api/preferences')
def update_preferences(body: PreferencesIn, db: DB):
    if not set(body.categories)<=set(CATEGORIES):
        raise HTTPException(422,'Unknown announcement category.')
    if body.companies:
        known = set(db.scalars(select(Company.ticker)))
        if not set(body.companies)<=known:
            raise HTTPException(422,'Verify companies with Discover before monitoring them.')
    pref = db.get(Preference,1)
    for key,value in body.model_dump().items():
        setattr(pref,key,value)
    db.flush()
    for mode in ('demo','sourced'):
        evaluate_alerts(db,mode)
    db.commit()
    return serial(pref)

@app.post('/api/sync',status_code=202)
def sync(background: BackgroundTasks, db: DB, filing_days: int | None=Query(None,ge=1,le=31),only_if_stale: bool=False):
    if SYNC_LOCK.locked() and not db.scalar(select(SyncRun.id).where(SyncRun.completed_at.is_(None))):
        raise HTTPException(409,'A source refresh is already running. The cached snapshot is still available.')
    result,created=reserve_refresh(db,only_if_stale)
    if created:background.add_task(run_sync,result['id'],filing_days or (catchup_days(db) if only_if_stale else None),smart=only_if_stale)
    if result['id'] is None:return JSONResponse(status_code=200,content=result)
    return result

@app.get('/api/sync/{run_id}')
def sync_status(run_id: RecordId, db: DB):
    row = db.get(SyncRun,run_id)
    if not row:
        raise HTTPException(404,'Refresh not found.')
    return serial(row)

@app.post('/api/companies/{ticker}/discover')
def discover(ticker: str, db: DB):
    ticker = symbol(ticker)
    company = db.get(Company,ticker)
    if not company or not company.verified:
        resolved = resolve_company(ticker)
        if not company:
            company = Company(**resolved,watched=False)
            db.add(company)
        else:
            for key,value in resolved.items():
                setattr(company,key,value)
        db.commit()
    try:
        candidates = discover_documents(company)
        return {'company':serial(company),'documents':candidates,'message':'Primary links only. Select Import to download and index a document.' if candidates else 'No permitted primary PDF links were discoverable. Import a document URL from the issuer website or an NSE/BSE archive.'}
    except SourceError as exc:
        return {'company':serial(company),'documents':[],'message':str(exc)}

@app.get('/api/companies/{ticker}/documents')
def documents(ticker: str, db: DB):
    company = require_company(db,ticker)
    return [serial(d) for d in db.scalars(select(Document).where(Document.ticker==company.ticker).order_by(Document.id.desc()))]

@app.post('/api/documents')
def import_document(body: ImportDocumentIn, db: DB):
    company = require_company(db,body.ticker)
    doc = ingest_url(db,company,body.title,body.period,body.kind,body.url)
    db.commit()
    return serial(doc)

@app.post('/api/research')
def ask(body: ResearchIn, db: DB):
    require_company(db,body.ticker)
    result = research(db,body.ticker,body.question,body.use_ai,refresh=body.refresh)
    db.commit()
    return result

@app.get('/api/companies/{ticker}/financials')
def financials(ticker: str, db: DB, period: str | None=Query(None,pattern=r'^20\d{2}-Q[1-4]$')):
    company = require_company(db,ticker)
    rows = list(db.scalars(select(Financial).where(Financial.ticker==company.ticker,Financial.mode=='sourced').order_by(Financial.period.desc())))
    if not rows:
        return {'rows':[],'message':'No reviewed quarterly metrics are indexed. Research can retrieve source passages; numeric tables are never guessed.'}
    current = next((r for r in rows if r.period==period),None) if period else rows[0]
    if not current:raise HTTPException(404,'That quarter has not been reviewed for this issuer.')
    by_period = {r.period:r for r in rows if r.basis==current.basis and r.currency==current.currency}
    # Period format YYYY-Qn uses Indian financial-year ending year.
    year, quarter = int(current.period[:4]),int(current.period[-1])
    previous_period = f'{year}-Q{quarter-1}' if quarter>1 else f'{year-1}-Q4'
    previous, last_year = by_period.get(previous_period),by_period.get(f'{year-1}-Q{quarter}')
    output = []
    for metric in ('revenue','ebitda','pbt','pat'):
        val = current.metrics.get(metric)
        prev = previous.metrics.get(metric) if previous else None
        yoy = last_year.metrics.get(metric) if last_year else None
        output.append({'metric':metric,'current':val,'previous':prev,'last_year':yoy,'qoq':percent_change(val,prev),'yoy':percent_change(val,yoy),'calculated':False})
    return {'rows':output,'current_period':current.period,'previous_period':previous_period,'last_year_period':f'{year-1}-Q{quarter}','basis':current.basis,'currency':current.currency,'periods':list(by_period),'review_flags':current.metrics.get('_review_flags',[]),'sources':[serial(r) for r in rows],'history':[{'period':r.period,'metrics':r.metrics,'basis':r.basis,'currency':r.currency,'source_url':r.source_url,'page':r.page} for r in rows if r.basis==current.basis and r.currency==current.currency],'note':'EBITDA is unavailable unless explicitly reported or supported by a reviewed reconciliation. Growth uses absolute prior values for negative bases; zero bases are unavailable. Missing quarters are not replaced by the next available quarter.'}

@app.get('/api/companies/{ticker}/guidance')
def guidance(ticker: str, db: DB):
    company = require_company(db,ticker)
    rows = [g.data for g in db.scalars(select(Guidance).where(Guidance.ticker==company.ticker).order_by(Guidance.id))]
    items=[]
    for row in rows:
        if any(row.get(a,row.get(b))!=row.get(b) for a,b in [('actual_period','target_period'),('actual_metric','metric'),('actual_unit','unit'),('actual_basis','basis')]):
            continue
        comparison=guidance_comparison(row['low'],row['high'],row['actual']) if row.get('actual') is not None else {'status':'pending','deviation_pp':None,'midpoint_deviation_pp':None}
        items.append({**row,**comparison})
    return {'items':items,'distinct_targets':len({(r['target_period'],r['metric'],r.get('basis'),r['unit']) for r in items}),'note':'Compare matching metrics, units, accounting/currency bases and target periods. Revisions share one target; distinct quarterly targets are counted separately. Future outcomes remain pending. No executive intent or credibility score is inferred.'}
