from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import hmac
import json
import threading
from typing import Annotated
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .config import ROOT, settings
from .database import Base, engine, get_db, SessionLocal
from .models import Alert, Announcement, Company, Document, Financial, Guidance, Preference, SyncRun
from .schemas import ImportDocumentIn, Mode, PreferencesIn, ResearchIn, WatchIn, normalize_ticker
from .seed import DEMO_CLOCK, seed
from .services.alerts import evaluate_alerts, quotes
from .services.calculations import guidance_comparison, percent_change
from .services.documents import discover_documents, ingest_url, store_document
from .services.materiality import CATEGORIES
from .services.research import research
from .services.sync import run_sync, SYNC_LOCK
from .ingestion.http import SourceError
from .ingestion.market import resolve_company

def initialize():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
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
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize()
    scheduler = None
    if settings.enable_scheduler:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(timezone='Asia/Kolkata')
        scheduler.add_job(run_sync,'interval',minutes=max(settings.sync_interval_minutes,30),max_instances=1,coalesce=True)
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
        if not hmac.compare_digest(supplied,settings.finn_api_token):
            return JSONResponse(status_code=401,content={'detail':'API token required.'})
    return await call_next(request)

@app.exception_handler(SourceError)
async def source_error(request, exc):
    return JSONResponse(status_code=422,content={'detail':str(exc)})

DB = Annotated[Session, Depends(get_db)]

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
    return {'status':'ok','version':'1.0.0','ai_configured':bool(settings.openai_api_key),'scheduler_enabled':settings.enable_scheduler,'demo_clock':DEMO_CLOCK.isoformat()+'Z'}

@app.get('/api/companies')
def companies(db: DB, q: str = ''):
    stmt = select(Company).order_by(Company.watched.desc(),Company.ticker)
    if q:
        stmt = stmt.where(Company.ticker.icontains(q,autoescape=True) | Company.name.icontains(q,autoescape=True))
    return [serial(c) for c in db.scalars(stmt.limit(100))]

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
    return {'mode':mode,'as_of':clock.isoformat()+'Z','companies':monitored,'stats':{'companies':len(monitored),'high_priority':high,'volume_alerts':volumes,'price_alerts':sum(x.kind=='price' for x in alerts),'routine':routine,'total_filings':len(filings),'coverage':sum(x['close'] is not None for x in monitored)},'digest':f'{high} high-priority disclosures and {volumes} unusual-volume signals across your watchlist. {routine} routine filings are tucked away.' if filings or alerts else 'No sourced signals yet. Refresh sources to retrieve completed trading sessions and exchange disclosures.','last_sync':serial(latest) if latest else None,'ai_configured':bool(settings.openai_api_key),'scheduler_enabled':settings.enable_scheduler}

@app.get('/api/announcements')
def announcements(db: DB, mode: Mode='demo', window: str='24h', ticker: str|None=None, category: str|None=None, priority: str|None=None, include_routine: bool=False, start: datetime|None=None, end: datetime|None=None):
    clock = DEMO_CLOCK if mode=='demo' else datetime.now(timezone.utc).replace(tzinfo=None)
    if window not in {'24h','7d','30d','custom'}:
        raise HTTPException(422,'Choose 24h, 7d, 30d or custom.')
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
    return {'items':[serial(a) for a in db.scalars(stmt.order_by(Announcement.score.desc(),Announcement.published_at.desc()).limit(300))],'routine_count':routine_count,'start':start.isoformat()+'Z','end':end.isoformat()+'Z','mode':mode}

@app.get('/api/alerts')
def alerts(db: DB, mode: Mode='demo'):
    return [serial(a) for a in db.scalars(select(Alert).where(Alert.mode==mode).order_by(Alert.date.desc(),Alert.value.desc()))]

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
def sync(background: BackgroundTasks, db: DB):
    latest = db.scalar(select(SyncRun).where(SyncRun.completed_at.is_(None)).order_by(SyncRun.id.desc()).limit(1))
    if SYNC_LOCK.locked() or (latest and datetime.now(timezone.utc).replace(tzinfo=None)-latest.started_at<timedelta(minutes=10)):
        raise HTTPException(409,'A source refresh is already running.')
    row = SyncRun(result={'status':'queued'})
    db.add(row)
    db.commit()
    background.add_task(run_sync,row.id)
    return {'id':row.id,'status':'queued'}

@app.get('/api/sync/{run_id}')
def sync_status(run_id: int, db: DB):
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
    result = research(db,body.ticker,body.question,body.use_ai)
    db.commit()
    return result

@app.get('/api/companies/{ticker}/financials')
def financials(ticker: str, db: DB):
    company = require_company(db,ticker)
    rows = list(db.scalars(select(Financial).where(Financial.ticker==company.ticker,Financial.mode=='sourced').order_by(Financial.period.desc())))
    if not rows:
        return {'rows':[],'message':'No reviewed quarterly metrics are indexed. Research can retrieve source passages; numeric tables are never guessed.'}
    current = rows[0]
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
    return {'rows':output,'current_period':current.period,'previous_period':previous_period,'last_year_period':f'{year-1}-Q{quarter}','basis':current.basis,'currency':current.currency,'sources':[serial(r) for r in rows],'note':'EBITDA is unavailable unless explicitly reported or supported by a reviewed reconciliation. Growth uses absolute prior values for negative bases; zero bases are unavailable.'}

@app.get('/api/companies/{ticker}/guidance')
def guidance(ticker: str, db: DB):
    company = require_company(db,ticker)
    rows = [g.data for g in db.scalars(select(Guidance).where(Guidance.ticker==company.ticker).order_by(Guidance.id))]
    return {'items':[{**r,**guidance_comparison(r['low'],r['high'],r['actual'])} for r in rows],'note':'Compare the same metric, currency basis and target period. Each revision is assessed against the same final full-year result; revisions are not four independent promises.'}
