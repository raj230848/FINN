from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone,date
import json
from threading import Event,Thread
from sqlalchemy import select,func
from sqlalchemy.orm import sessionmaker
import pytest

from app import main
from app.config import settings
from app.models import Price,SyncRun,Company,utcnow
from app.services import company_directory as directory_module
from app.services.company_directory import CompanyDirectory,SOURCE_URL,parse_listing
from app.services.freshness import reserve_refresh,refresh_state,market_fetch_needed


@pytest.fixture
def directory(tmp_path):
    path=tmp_path/'bundled.json'
    path.write_text(json.dumps({'source_url':SOURCE_URL,'retrieved_at':datetime.now(timezone.utc).isoformat(),'entries':[
        {'ticker':'HCLTECH','name':'HCL Technologies Limited'}, {'ticker':'INFY','name':'Infosys Limited'},
        {'ticker':'NAUKRI','name':'Info Edge (India) Limited'}, {'ticker':'RELIANCE','name':'Reliance Industries Limited'},
        {'ticker':'HINDUNILVR','name':'Hindustan Unilever Limited'}]}),encoding='utf-8')
    return CompanyDirectory(path,tmp_path/'cached.json')


@pytest.mark.parametrize('query',['HCL Technologies','HCLTECH','HCL Tech','hcl technologies ltd','HCLTECH.NS'])
def test_name_and_ticker_identify_same_verified_company(directory,query):
    result=directory.search(query)
    assert result['items'][0]['ticker']=='HCLTECH'
    assert result['items'][0]['name']=='HCL Technologies Limited'
    assert result['items'][0]['verified'] and result['source_date']


def test_directory_supports_out_of_portfolio_partial_and_ambiguous_names(directory):
    assert directory.search('NAUKRI')['items'][0]['ticker']=='NAUKRI'
    assert {r['ticker'] for r in directory.search('Info')['items']}=={'INFY','NAUKRI'}
    assert directory.search('Infosys')['items'][0]['ticker']=='INFY'
    assert directory.search('Hindustan Uni')['items'][0]['ticker']=='HINDUNILVR'


@pytest.mark.parametrize('query',['Google','NASDAQ:GOOGL','<script>','x',''])
def test_unknown_input_never_invents_a_listing(directory,query):
    assert directory.search(query)['items']==[]
    assert directory.search(query)['message']


def test_directory_endpoint_validates_bounds_and_is_protected(client,monkeypatch,directory):
    monkeypatch.setattr(main,'directory',directory)
    assert client.get('/api/company-search?q=Infosys').json()['items'][0]['ticker']=='INFY'
    for query in ('q='+'a'*101,'q=Info&limit=0','q=Info&limit=21'):
        assert client.get('/api/company-search?'+query).status_code==422
    monkeypatch.setattr(settings,'finn_api_token','directory-private-token')
    assert client.get('/api/company-search?q=Info').status_code==401


def test_failed_directory_refresh_preserves_last_known_identity(directory,monkeypatch):
    original=directory.load();original['retrieved_at']='2020-01-01T00:00:00+00:00'
    def failed(*args,**kwargs):raise ValueError('provider failure')
    monkeypatch.setattr(directory_module,'fetch_public',failed)
    assert directory.refresh() is False
    result=directory.search('HCL Tech')
    assert result['items'][0]['ticker']=='HCLTECH' and result['stale'] and result['warning']
    assert directory.refresh() is False


def test_directory_update_does_not_block_cached_search(directory,monkeypatch):
    directory.load();started=Event();release=Event()
    def paused(*args,**kwargs):
        started.set();release.wait(3);raise ValueError('unavailable')
    monkeypatch.setattr(directory_module,'fetch_public',paused)
    thread=Thread(target=directory.refresh);thread.start();assert started.wait(1)
    try:assert directory.search('Infosys')['items'][0]['ticker']=='INFY'
    finally:release.set();thread.join(3)


@pytest.mark.parametrize('content',[b'not,a,directory\n1,2,3',b'SYMBOL,NAME OF COMPANY,SERIES\nFAKE,Wrong,EQ'])
def test_invalid_or_incomplete_directory_cannot_replace_source(content):
    with pytest.raises(ValueError):parse_listing(content)


def test_refresh_reservation_is_shared_across_two_sessions(db):
    factory=sessionmaker(bind=db.bind,expire_on_commit=False)
    def request(_):
        with factory() as session:return reserve_refresh(session,only_if_stale=True)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(request,range(2)))
    assert sum(created for _,created in results)==1
    assert len({result['id'] for result,_ in results})==1
    assert db.scalar(select(func.count()).select_from(SyncRun))==1


def test_recent_snapshot_and_failed_attempt_have_server_cooldowns(db):
    now=utcnow();run=SyncRun(started_at=now,completed_at=now,result={'status':'complete'})
    db.add(run);db.commit()
    assert not refresh_state(db,now)['should_refresh']
    assert reserve_refresh(db,only_if_stale=True,now=now)[0]['id'] is None
    run.result={'status':'partial','prices':{'INFY':{'ok':False}}};db.commit()
    assert refresh_state(db,now)['state']=='retry_later'
    assert not refresh_state(db,now+timedelta(minutes=4))['should_refresh']
    assert refresh_state(db,now+timedelta(minutes=6))['should_refresh']


def test_smart_market_fetch_waits_for_cutoff_and_probes_once_after_close(db):
    now=datetime(2026,11,2,10) # 15:30 IST, incomplete for our 18:30 buffer.
    for day in (date(2026,10,29),date(2026,10,30)):
        db.add(Price(ticker='INFY',date=day,close=100,volume=10,mode='sourced',source_url='https://example.com',fetched_at=now))
    db.commit()
    assert not market_fetch_needed(db,'INFY',now)
    assert market_fetch_needed(db,'INFY',datetime(2026,11,2,13,1))
    for row in db.scalars(select(Price).where(Price.ticker=='INFY',Price.mode=='sourced')):row.fetched_at=datetime(2026,11,2,13,2)
    db.commit()
    assert not market_fetch_needed(db,'INFY',datetime(2026,11,2,15))


def test_empty_watchlist_does_not_trigger_automatic_external_work(db):
    for company in db.scalars(select(Company)):company.watched=False
    db.commit()
    assert refresh_state(db)['state']=='empty_watchlist'
    assert reserve_refresh(db,only_if_stale=True)[1] is False


def test_returning_after_long_gap_uses_bounded_catchup(db):
    from app.services.freshness import catchup_days
    from app.models import IngestionCoverage
    now=utcnow()
    db.add(IngestionCoverage(ticker='INFY',start_at=now-timedelta(days=45),end_at=now-timedelta(days=40),completed_at=now-timedelta(days=40)));db.commit()
    assert catchup_days(db,now)==31


def test_automatic_sync_reuses_fresh_eod_and_does_not_call_gemini(db,monkeypatch):
    from app.services import sync
    for company in db.scalars(select(Company)):company.watched=company.ticker=='INFY'
    for day in (date(2026,10,29),date(2026,10,30)):
        db.add(Price(ticker='INFY',date=day,close=100,volume=10,mode='sourced',source_url='https://example.com',fetched_at=utcnow()))
    run=SyncRun(result={'status':'queued'});db.add(run);db.commit()
    monkeypatch.setattr(sync,'SessionLocal',sessionmaker(bind=db.bind,expire_on_commit=False))
    from app.services import freshness
    monkeypatch.setattr(freshness,'market_fetch_needed',lambda *args:False)
    monkeypatch.setattr(sync,'fetch_prices',lambda *_:pytest.fail('Fresh EOD must not be downloaded again'))
    monkeypatch.setattr(sync,'fetch_announcements',lambda *args,**kwargs:[])
    calls=[]
    monkeypatch.setattr(sync,'save_announcements',lambda *args,**kwargs:calls.append(kwargs['use_ai']) or 0)
    sync.run_sync(run.id,smart=True)
    db.refresh(run)
    assert run.result['status']=='complete' and run.result['prices']['INFY']['skipped']
    assert calls==[False]


def test_unexpected_sync_failure_releases_lock_and_does_not_remain_running(db,monkeypatch):
    from app.services import sync
    run=SyncRun(result={'status':'queued'});db.add(run);db.commit()
    monkeypatch.setattr(sync,'SessionLocal',sessionmaker(bind=db.bind,expire_on_commit=False))
    monkeypatch.setattr(sync,'fetch_prices',lambda *_:[])
    monkeypatch.setattr(sync,'fetch_announcements',lambda *args,**kwargs:[])
    def failed(*args):raise RuntimeError('private failure detail')
    monkeypatch.setattr(sync,'evaluate_alerts',failed)
    sync.run_sync(run.id)
    db.refresh(run)
    assert run.completed_at and run.result['status']=='failed'
    assert 'private failure detail' not in str(run.result)
    assert not sync.SYNC_LOCK.locked()
