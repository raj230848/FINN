import json
from datetime import datetime, timedelta
import httpx
import pymupdf
import pytest
from sqlalchemy import create_engine, text, select, func
from app.ai import client as provider
from app.config import settings
from app.migrations import migrate_schema
from app.models import SignalEvent, Preference, IngestionCoverage, Company
from app.schemas import AnalysisOut
from app.services.alerts import evaluate_alerts
from app.services.coverage import describe_coverage
from app.services.materiality import classify
from app.services.sync import save_announcements

@pytest.mark.parametrize('headline,category',[
    ('Resignation of Chief Financial Officer','management_change'),
    ('Appointment of Independent Director','management_change'),
    ('Cessation of company secretary','management_change'),
    ('Retirement of Managing Director','management_change'),
    ('Change in Key Managerial Personnel','management_change'),
    ('Promoter acquires 1 lakh shares','insider_trading'),
    ('Shares sold by designated person','insider_trading'),
    ('Disclosure under PIT Regulations','insider_trading'),
    ('Merger of subsidiary approved','M&A'),
    ('Scheme of amalgamation','M&A'),
    ('Regulatory penalty imposed','litigation'),
    ('Rights issue approved','fund_raise'),
    ('Audited consolidated financial results','results'),
    ('QIP allotment approved','fund_raise'),
    ('Downgrade of long-term credit rating','credit_rating'),
    ('Reaffirmation of credit rating','credit_rating'),
    ('Interim dividend declared','dividend'),
    ('Stock split approved','bonus_split'),
    ('Sub-division of equity shares','bonus_split'),
    ('New plant capacity expansion','capex'),
    ('Earnings call transcript','earnings_call'),
    ('Schedule of analyst meet','investor_meetings'),
    ('Press release on new product','press_release'),
    ('Postal ballot voting notice','postal_ballot'),
    ('Annual general meeting notice','agm_egm'),
    ('Promoter share pledging disclosure','pledging'),
    ('Compliance certificate for transfer facility','unclassified'),
])
def test_materiality_varied_wording(headline,category):
    assert classify(headline)['category']==category

def test_uncertain_material_items_are_not_hidden():
    result=classify('Outcome of Board Meeting','A material restructuring matter was discussed; details require review.')
    assert result['needs_review'] and result['priority']!='low'
    assert classify('Board meeting to consider financial results')['priority']=='low'
    assert classify('Resignation of Chief Financial Officer')['priority']=='high'

def test_identity_uses_attachment_id_and_content(db):
    a=dict(ticker='INFY',title='Outcome of Board Meeting',published_at=datetime(2026,10,30,4),source_url='https://nsearchives.nseindia.com/a.pdf',text='First outcome')
    b={**a,'source_url':'https://nsearchives.nseindia.com/b.pdf'}
    assert save_announcements(db,[a,b])==2
    assert save_announcements(db,[{**a,'source_url':a['source_url']+'?utm_source=nse#page=1','published_at':a['published_at']+timedelta(hours=1)}])==0
    assert save_announcements(db,[{**a,'source_filing_id':'new-exchange-id'}])==1
    assert save_announcements(db,[{**a,'text':'Amended outcome with different terms'}])==1
    assert save_announcements(db,[a])==0

def test_sqlite_transition_preserves_legacy_data_and_unknown_observed_date(tmp_path):
    engine=create_engine(f'sqlite:///{tmp_path / "legacy.db"}')
    with engine.begin() as c:
        c.execute(text('CREATE TABLE announcements (id INTEGER PRIMARY KEY,ticker TEXT,title TEXT,published_at DATETIME,mode TEXT,source_url TEXT,text TEXT,fingerprint TEXT UNIQUE)'))
        c.execute(text("INSERT INTO announcements VALUES (1,'INFY','Results','2026-10-30 04:00:00','sourced','https://example.com/a.pdf','Reported data','old-key')"))
    migrate_schema(engine);migrate_schema(engine)
    with engine.connect() as c:
        row=c.execute(text('SELECT * FROM announcements')).mappings().one()
        assert row['text']=='Reported data' and row['ingested_at'] is None
        assert row['content_checksum'] and row['fingerprint']!='old-key'
        assert c.execute(text('SELECT count(*) FROM schema_migrations')).scalar()==1

def test_notification_history_survives_recalculation_and_read_state(client,db):
    initial=client.get('/api/notifications').json()
    assert initial['unread_count']==5
    first=initial['items'][0]['id']
    assert client.post(f'/api/notifications/{first}/read').status_code==200
    pref=db.get(Preference,1);pref.price_threshold=20;pref.volume_multiplier=10
    evaluate_alerts(db,'demo');db.commit()
    assert client.get('/api/alerts').json()==[]
    assert client.get('/api/notifications').json()['unread_count']==4
    assert db.scalar(select(func.count()).select_from(SignalEvent))==5
    pref.price_threshold=5;pref.volume_multiplier=2
    evaluate_alerts(db,'demo');db.commit()
    assert db.scalar(select(func.count()).select_from(SignalEvent))==5
    client.post('/api/notifications/read-all?mode=demo')
    assert client.get('/api/notifications').json()['unread_count']==0
    assert client.get('/api/notifications?mode=sourced').json()['items']==[]

def test_sourced_pagination_and_coverage_are_explicit(client,db):
    now=datetime.utcnow()
    rows=[dict(ticker='INFY',title='Quarterly financial results',published_at=now-timedelta(minutes=i),source_url=f'https://nsearchives.nseindia.com/{i}.pdf',text='Reported consolidated results') for i in range(105)]
    save_announcements(db,rows);db.commit()
    first=client.get('/api/announcements?mode=sourced&limit=100').json()
    second=client.get('/api/announcements?mode=sourced&limit=100&offset=100').json()
    assert first['total']==105 and first['has_more'] and first['next_offset']==100
    assert len(second['items'])==5 and not second['has_more']
    assert not {r['id'] for r in first['items']} & {r['id'] for r in second['items']}
    assert first['coverage']['partial_coverage'] is True
    assert first['coverage']['first_observed_at']
    assert client.get('/api/announcements?limit=301').status_code==422

def test_coverage_detects_gaps_and_missing_companies(db):
    start=datetime(2026,10,1);end=start+timedelta(days=30)
    db.add(IngestionCoverage(ticker='INFY',start_at=start,end_at=end));db.flush()
    assert not describe_coverage(db,'sourced',['INFY'],start,end)['partial_coverage']
    assert describe_coverage(db,'sourced',['INFY','TCS'],start,end)['partial_coverage']
    assert describe_coverage(db,'sourced',['INFY'],start-timedelta(days=1),end)['partial_coverage']

def install_transport(monkeypatch, handler):
    real=httpx.Client
    monkeypatch.setattr(settings,'gemini_api_key','test-only-not-a-real-key')
    monkeypatch.setattr(provider.httpx,'Client',lambda **kwargs:real(transport=httpx.MockTransport(handler),**kwargs))
    monkeypatch.setattr(provider.time,'sleep',lambda _:None)

def response(content):
    return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':json.dumps(content)}}],'usage':{'total_tokens':42}})

def test_gemini_boundary_uses_requested_model_and_schema(monkeypatch):
    calls=[]
    def handler(request):
        calls.append(request);body=json.loads(request.content)
        assert request.url==provider.GEMINI_URL
        assert body['model']=='gemini-3.5-flash-lite'
        assert body['response_format']['type']=='json_schema' and body['max_tokens']==1600
        return response({'answer':'The report supports this statement [1].','evidence_ids':[1],'limitations':[]})
    install_transport(monkeypatch,handler)
    assert provider.structured_call('Evidence only',{'evidence':[]},AnalysisOut).evidence_ids==[1]
    assert len(calls)==1

@pytest.mark.parametrize('status,expected_calls',[(401,1),(403,1),(404,1),(429,3),(503,3)])
def test_provider_failure_is_bounded_and_redacted(monkeypatch,status,expected_calls):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(status,json={'error':'test-only-not-a-real-key'},headers={'Retry-After':'999'})
    install_transport(monkeypatch,handler)
    with pytest.raises(provider.ProviderError) as error:provider.structured_call('Evidence only',{},AnalysisOut)
    assert len(calls)==expected_calls and 'test-only' not in str(error.value)

def test_retry_success_invalid_json_and_timeout(monkeypatch):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(429) if len(calls)<3 else response({'answer':'The source supports this statement [1].','evidence_ids':[1],'limitations':[]})
    install_transport(monkeypatch,handler)
    assert provider.structured_call('Evidence only',{},AnalysisOut).evidence_ids==[1]
    assert len(calls)==3
    calls.clear()
    def invalid(request):
        calls.append(request);return httpx.Response(200,json={'choices':[{'message':{'content':'not JSON'}}]})
    real=provider.httpx.Client  # Existing factory wraps a genuine MockTransport client.
    monkeypatch.undo()
    install_transport(monkeypatch,invalid)
    with pytest.raises(provider.ProviderError):provider.structured_call('Evidence only',{},AnalysisOut)
    assert len(calls)==1

def test_claim_validation_and_transient_fallback_not_cached(db,monkeypatch):
    from app.services import research as module
    from app.services.documents import store_document
    pdf=pymupdf.open();page=pdf.new_page();page.insert_text((40,60),'Infosys revenue grew 4.2 percent.\n'+('Cash flow and revenue outlook.\n'*10))
    store_document(db,db.get(Company,'INFY'),'Reviewed test report','FY25','results','https://www.infosys.com/roadmap-test.pdf',pdf.tobytes())
    evidence=module.retrieve(db,'INFY','What is revenue outlook?')
    citation=evidence[0]['id']
    monkeypatch.setattr(settings,'gemini_api_key','test-key')
    attempts=[]
    def generate(*args,**kwargs):
        from app.schemas import GroundingReviewOut, SynthesisOut, SynthesisClaim
        if args[2] is GroundingReviewOut:return GroundingReviewOut(supported=True,reason='Exact reported value',unsupported_claims=[])
        attempts.append(1)
        if len(attempts)==1: raise provider.ProviderError('Temporary failure')
        return SynthesisOut(claims=[SynthesisClaim(text='Revenue grew 4.2 percent.',evidence_ids=[citation])])
    monkeypatch.setattr(module,'structured_call',generate)
    assert module.research(db,'INFY','What is revenue outlook?',True)['method']=='extractive'
    assert module.research(db,'INFY','What is revenue outlook?',True)['method']=='grounded_ai'
    assert len(attempts)==2
    with pytest.raises(ValueError):module.validate_claims(f'Revenue grew 99 percent [{citation}].',evidence)
    with pytest.raises(ValueError):module.validate_claims(f'Revenue grew 4.2 percent [{citation}]. Management is guaranteed to outperform.',evidence)

def test_transport_timeouts_are_bounded(monkeypatch):
    attempts=[]
    def timeout(request):
        attempts.append(1)
        raise httpx.ReadTimeout('private transport details must not escape',request=request)
    install_transport(monkeypatch,timeout)
    with pytest.raises(provider.ProviderError) as error:provider.structured_call('Evidence only',{},AnalysisOut)
    assert len(attempts)==3 and 'private transport' not in str(error.value)


def test_proposed_appointment_is_reviewable_without_claiming_completion():
    result = classify('Intimation of Board Meeting to consider appointment of CFO')
    assert result['category'] == 'management_change'
    assert result['priority'] == 'medium' and result['needs_review']
    completed = classify('Board meeting approved appointment of CFO')
    assert completed['priority'] == 'high' and not completed['needs_review']

def test_public_expensive_routes_require_token_and_rate_limit(client,monkeypatch):
    from app.rate_limit import _requests
    _requests.clear()
    monkeypatch.setattr(settings,'public_deployment',True)
    monkeypatch.setattr(settings,'finn_api_token','test-backend-token')
    assert client.post('/api/research',json={'ticker':'WIPRO','question':'What is the outlook?','use_ai':False}).status_code==401
    for _ in range(10):
        assert client.post('/api/research',headers={'Authorization':'Bearer test-backend-token'},json={'ticker':'WIPRO','question':'What is the outlook?','use_ai':False}).status_code==200
    response=client.post('/api/research',headers={'Authorization':'Bearer test-backend-token'},json={'ticker':'WIPRO','question':'What is the outlook?','use_ai':False})
    assert response.status_code==429 and response.headers['Retry-After']=='60'
    _requests.clear()
