"""Regression boundaries found by the complete endpoint/LLM audit."""
import json
from types import SimpleNamespace
import httpx
import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from app import main
from app.ai import client as provider
from app.config import settings
from app.models import Company,Document,Announcement,ResearchCache,IngestionCoverage,utcnow
from app.schemas import AnalysisOut,ClassificationOut
from app.ingestion.http import SourceError,validate_url
from app.services.documents import store_document
from app.services.research import fiscal_years,matches_period

@pytest.fixture(autouse=True)
def isolate_credentials(monkeypatch):
    monkeypatch.setattr(settings,'gemini_api_key','')
    monkeypatch.setattr(settings,'finn_api_token','')
    monkeypatch.setattr(settings,'public_deployment',False)

@pytest.mark.parametrize('path',['/api/announcements/999999999999999999999999999999/context','/api/sync/999999999999999999999999999999'])
def test_audit_regression_huge_record_ids_are_validation_errors(client,path):
    scoped=TestClient(main.app,raise_server_exceptions=False)
    assert scoped.get(path).status_code==422

def test_audit_regression_whitespace_question_is_invalid(client):
    assert client.post('/api/research',json={'ticker':'INFY','question':'     ','use_ai':False}).status_code==422

@pytest.mark.parametrize('query',['category=not-a-category','priority=urgent'])
def test_audit_regression_unknown_filing_filters_are_invalid(client,query):
    assert client.get('/api/announcements?'+query).status_code==422

@pytest.mark.parametrize('url',['https://www.infosys.com:notaport/report.pdf','https://[invalid/report.pdf'])
def test_audit_regression_malformed_url_is_source_error(url):
    with pytest.raises(SourceError):validate_url(url,{'infosys.com'})

def test_audit_regression_generic_services_word_is_not_issuer_identity(db):
    pdf=pymupdf.open();p=pdf.new_page();p.insert_text((40,60),'Infosys Limited annual report.\n'+('We provide consulting services and technology services.\n'*10))
    with pytest.raises(SourceError):store_document(db,db.get(Company,'TCS'),'Incorrect issuer test','FY25','annual_report','https://nsearchives.nseindia.com/wrong-issuer.pdf',pdf.tobytes())

@pytest.mark.parametrize('question,expected', [('FY2024-2025',{2025}),('FY2024-25',{2025}),('Q2FY25',{2025}),('FY25Q2',{2025})])
def test_audit_regression_fiscal_aliases_use_ending_year(question,expected):
    assert fiscal_years(question)==expected

@pytest.mark.parametrize('malformed',[{'choices':[1]},{'choices':[{'message':None}]},{'choices':None}])
def test_audit_regression_malformed_provider_envelope_is_sanitized(monkeypatch,malformed):
    real=httpx.Client
    monkeypatch.setattr(settings,'gemini_api_key','test-only')
    monkeypatch.setattr(provider.httpx,'Client',lambda **kwargs:real(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=malformed)),**kwargs))
    with pytest.raises(provider.ProviderError):provider.structured_call('Evidence only',{},AnalysisOut)

API_CASES=[
 ('GET','/api/health','/api/health',200,None),
 ('GET','/api/operations','/api/operations',200,None),
 ('GET','/api/company-search','/api/company-search?q=Infosys',200,None),
 ('GET','/api/companies','/api/companies',200,None),
 ('PATCH','/api/companies/{ticker}','/api/companies/INFY',200,{'watched':True}),
 ('GET','/api/dashboard','/api/dashboard',200,None),
 ('GET','/api/announcements','/api/announcements',200,None),
 ('GET','/api/alerts','/api/alerts',200,None),
 ('GET','/api/notifications','/api/notifications',200,None),
 ('GET','/api/push/config','/api/push/config',200,None),
 ('POST','/api/push/subscribe','/api/push/subscribe',200,'subscription'),
 ('POST','/api/push/unsubscribe','/api/push/unsubscribe',200,{'device_id':'d'*32}),
 ('GET','/api/push/status','/api/push/status?device_id='+'d'*32,200,None),
 ('GET','/api/announcements/{filing_id}/context','/api/announcements/1/context',200,None),
 ('POST','/api/notifications/read-all','/api/notifications/read-all',200,None),
 ('POST','/api/notifications/{event_id}/read','/api/notifications/1/read',200,None),
 ('GET','/api/preferences','/api/preferences',200,None),
 ('PUT','/api/preferences','/api/preferences',200,{'price_threshold':5,'volume_multiplier':2,'lookback':20,'companies':[],'categories':[]}),
 ('POST','/api/sync','/api/sync',202,None),
 ('GET','/api/sync/{run_id}','/api/sync/1',200,None),
 ('POST','/api/companies/{ticker}/discover','/api/companies/AUDITCO/discover',200,None),
 ('GET','/api/companies/{ticker}/documents','/api/companies/INFY/documents',200,None),
 ('POST','/api/documents','/api/documents',200,{'ticker':'INFY','title':'Audit issuer report','period':'FY25','kind':'results','url':'https://www.infosys.com/audit.pdf'}),
 ('POST','/api/research','/api/research',200,{'ticker':'INFY','question':'What is revenue?','use_ai':False}),
 ('GET','/api/companies/{ticker}/financials','/api/companies/INFY/financials',200,None),
 ('GET','/api/companies/{ticker}/guidance','/api/companies/INFY/guidance',200,None),
]

@pytest.fixture
def endpoint_context(db,monkeypatch):
    import base64
    from app.models import SyncRun
    from app.services.documents import store_document
    pdf=pymupdf.open();page=pdf.new_page();page.insert_text((40,60),'Infosys Limited FY25 report.\n'+('Revenue grew 4.2 percent.\n'*20));content=pdf.tobytes()
    store_document(db,db.get(Company,'INFY'),'Audit issuer report','FY25','results','https://www.infosys.com/audit.pdf',content)
    db.add(SyncRun(completed_at=utcnow(),result={'status':'complete','controlled_fixture':True}));db.commit()
    monkeypatch.setattr(main,'resolve_company',lambda t:{'ticker':t,'name':'Audit Company Limited','website':'https://example.com','sector':'Test','verified':True})
    monkeypatch.setattr(main,'discover_documents',lambda c:[])
    monkeypatch.setattr(main,'ingest_url',lambda session,company,title,period,kind,url:store_document(session,company,title,period,kind,url,content))
    def complete(run_id,days=None,**kwargs):
        row=db.get(SyncRun,run_id);row.completed_at=utcnow();row.result={'status':'complete','controlled_fixture':True};db.commit()
    monkeypatch.setattr(main,'run_sync',complete)
    for name,value in [('vapid_private_key','test-only-private'),('vapid_public_key','test-only-public'),('vapid_subject','mailto:audit@example.invalid')]:monkeypatch.setattr(settings,name,value)
    encode=lambda b:base64.urlsafe_b64encode(b).decode().rstrip('=')
    return {'device_id':'d'*32,'subscription':{'endpoint':'https://fcm.googleapis.com/fcm/send/audit-only','keys':{'p256dh':encode(b'\x04'+b'x'*64),'auth':encode(b'x'*16)}}}

@pytest.mark.parametrize('method,template,path,expected,body',API_CASES,ids=[m+' '+t for m,t,*_ in API_CASES])
def test_all_business_endpoints(method,template,path,expected,body,client,endpoint_context):
    if body=='subscription':body=endpoint_context
    response=client.request(method,path,json=body) if body is not None else client.request(method,path)
    assert response.status_code==expected,response.text
    assert response.headers['content-type'].startswith('application/json')

def test_endpoint_inventory_has_no_uncovered_business_routes():
    actual={(method.upper(),path) for path,value in main.app.openapi()['paths'].items() for method in value if method in ('get','post','put','patch','delete')}
    assert actual=={(m,t) for m,t,*_ in API_CASES}

NEGATIVE_CASES=[
 ('GET','/api/dashboard?mode=wrong',None,422),('GET','/api/alerts?mode=wrong',None,422),
 ('GET','/api/notifications?offset=-1',None,422),('GET','/api/notifications?limit=101',None,422),
 ('GET','/api/announcements?limit=301',None,422),('GET','/api/announcements?window=custom',None,422),
 ('GET','/api/announcements?window=custom&start=2026-11-02&end=2026-11-01',None,422),
 ('GET','/api/announcements?window=custom&start=2020-01-01&end=2026-11-01',None,422),
 ('GET','/api/announcements/0/context',None,422),('GET','/api/announcements/999999/context',None,404),
 ('POST','/api/notifications/999999/read',None,404),('GET','/api/sync/999999',None,404),
 ('POST','/api/sync?filing_days=32',None,422),('POST','/api/sync?filing_days=0',None,422),
 ('GET','/api/push/status?device_id=short',None,422),
 ('POST','/api/push/subscribe',{'device_id':'x'*32,'subscription':{}},503),
 ('PATCH','/api/companies/UNKNOWN',{'watched':True},404),
 ('GET','/api/companies/UNKNOWN/documents',None,404),
 ('GET','/api/companies/INFY/financials?period=2025-Q9',None,422),
 ('GET','/api/companies/INFY/financials?period=2020-Q1',None,404),
 ('POST','/api/research',{'ticker':'UNKNOWN','question':'What is revenue?','use_ai':False},404),
 ('POST','/api/research',{'ticker':'INFY','question':'x'*1201},422),
 ('POST','/api/research',{'ticker':'https://localhost','question':'test'},422),
 ('PUT','/api/preferences',{'price_threshold':0},422),('PUT','/api/preferences',{'volume_multiplier':1},422),
 ('PUT','/api/preferences',{'lookback':61},422),('PUT','/api/preferences',{'categories':['invented']},422),
 ('PUT','/api/preferences',{'companies':['UNKNOWN']},422),
 ('POST','/api/documents',{'ticker':'INFY','title':'   ','period':'FY25','kind':'results','url':'https://www.infosys.com/a.pdf'},422),
 ('POST','/api/health',None,405),
]

@pytest.mark.parametrize('method,path,body,expected',NEGATIVE_CASES,ids=[str(i)+' '+m+' '+p for i,(m,p,*_) in enumerate(NEGATIVE_CASES)])
def test_endpoint_negative_cases(method,path,body,expected,client):
    response=client.request(method,path,json=body) if body is not None else client.request(method,path)
    assert response.status_code==expected,response.text

def test_non_ascii_bearer_is_rejected_without_server_error(client,monkeypatch):
    monkeypatch.setattr(settings,'finn_api_token','test-backend-token')
    scoped=TestClient(main.app,raise_server_exceptions=False)
    assert scoped.get('/api/companies',headers=[(b'authorization',b'Bearer \xc3\xa9')]).status_code==401

def test_filtered_coverage_uses_selected_company_only(client,db):
    from datetime import timedelta
    now=utcnow();db.add(IngestionCoverage(ticker='INFY',start_at=now-timedelta(days=3),end_at=now+timedelta(hours=1)));db.commit()
    assert not client.get('/api/announcements?mode=sourced&ticker=INFY').json()['coverage']['partial_coverage']
    assert client.get('/api/announcements?mode=sourced').json()['coverage']['partial_coverage']

def test_no_watchlist_is_not_falsely_reported_as_fetched_history(client,db):
    for c in db.scalars(select(Company)):c.watched=False
    db.commit();coverage=client.get('/api/announcements?mode=sourced').json()['coverage']
    assert coverage['kind']=='empty_watchlist' and not coverage['partial_coverage']

@pytest.mark.parametrize('invalid_id',[True,1.5,'1'])
def test_llm_citation_identifiers_must_be_integer_tokens(invalid_id):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):AnalysisOut(answer='Source supports the answer.',evidence_ids=[invalid_id])

def test_classifier_rejects_invented_numeric_summary(db,monkeypatch):
    from app.services import sync
    monkeypatch.setattr(settings,'gemini_api_key','test-only')
    monkeypatch.setattr(sync,'structured_call',lambda *a:ClassificationOut(category='M&A',summary='The subsidiary transfer is worth 999 billion.',why_matters='Review the transfer terms.',confidence='high',evidence_quote='material restructuring'))
    sync.save_announcements(db,[{'ticker':'INFY','title':'Outcome of Board Meeting','text':'The board approved a material restructuring.','published_at':utcnow(),'source_url':'https://nsearchives.nseindia.com/audit-classifier.pdf'}]);db.commit()
    row=db.scalar(select(Announcement).where(Announcement.mode=='sourced'))
    assert 'unavailable or unverified' in row.analysis_method and '999' not in row.summary

@pytest.mark.parametrize('envelope',[
    None,[],{}, {'choices':[]},
    {'choices':[{'finish_reason':'length','message':{'content':'{}'}}]},
    {'choices':[{'finish_reason':'content_filter','message':{'content':'{}'}}]},
    {'choices':[{'message':{'content':''}}]},
    {'choices':[{'message':{'content':['not a text response']}}]},
    {'choices':[{'message':{'content':'x'*18001}}]},
    {'choices':[{'message':{'content':'not JSON'}}]},
    {'choices':[{'message':{'content':'{"answer":"short","evidence_ids":[]}'}}]},
])
def test_provider_rejects_empty_truncated_refused_or_wrong_schema_reply(monkeypatch,envelope):
    real=httpx.Client;monkeypatch.setattr(settings,'gemini_api_key','test-only')
    monkeypatch.setattr(provider.httpx,'Client',lambda **kwargs:real(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=envelope)),**kwargs))
    with pytest.raises(provider.ProviderError):provider.structured_call('Evidence only',{},AnalysisOut)

def test_usage_metadata_cannot_log_arbitrary_provider_text(monkeypatch,caplog):
    import logging
    real=httpx.Client;monkeypatch.setattr(settings,'gemini_api_key','test-only')
    response={'choices':[{'message':{'content':json.dumps({'answer':'The source supports this claim.','evidence_ids':[1]})}}],'usage':{'total_tokens':'PRIVATE_RESPONSE_CANARY'}}
    monkeypatch.setattr(provider.httpx,'Client',lambda **kwargs:real(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=response)),**kwargs))
    caplog.set_level(logging.INFO,logger='uvicorn.error.finn.ai')
    provider.structured_call('Evidence only',{},AnalysisOut)
    assert 'PRIVATE_RESPONSE_CANARY' not in caplog.text and 'tokens=unknown' in caplog.text

def test_no_key_and_oversized_input_never_open_a_provider_connection(monkeypatch):
    def forbidden(**kwargs):raise AssertionError('Provider transport must not be opened')
    monkeypatch.setattr(provider.httpx,'Client',forbidden)
    with pytest.raises(provider.ProviderError):provider.structured_call('Evidence only',{},AnalysisOut)
    monkeypatch.setattr(settings,'gemini_api_key','test-only')
    with pytest.raises(provider.ProviderError):provider.structured_call('Evidence only',{'source':'x'*48001},AnalysisOut)

@pytest.mark.parametrize('ip',['127.0.0.1','10.0.0.1','169.254.169.254','192.0.2.1','::1','fc00::1'])
def test_source_resolver_rejects_non_global_addresses(monkeypatch,ip):
    import socket
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(2,1,6,'',(ip,443))])
    with pytest.raises(SourceError):validate_url('https://www.infosys.com/report.pdf',{'infosys.com'})

def test_source_fetch_checks_each_redirect_and_download_size(monkeypatch):
    from app.ingestion import http as source
    import socket
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(2,1,6,'',('8.8.8.8',443))])
    real=httpx.Client
    monkeypatch.setattr(source.httpx,'Client',lambda **kwargs:real(transport=httpx.MockTransport(lambda _:httpx.Response(302,headers={'location':'http://127.0.0.1/secret'})),**kwargs))
    with pytest.raises(SourceError):source.fetch_public('https://www.infosys.com/report.pdf',{'infosys.com'})
    monkeypatch.setattr(source.httpx,'Client',lambda **kwargs:real(transport=httpx.MockTransport(lambda _:httpx.Response(200,content=b'12345')),**kwargs))
    with pytest.raises(SourceError,match='4-byte'):source.fetch_public('https://www.infosys.com/report.pdf',{'infosys.com'},max_bytes=4)

def test_encrypted_and_over_limit_pdfs_are_not_indexed(monkeypatch):
    from app.services.documents import extract_pages
    pdf=pymupdf.open();pdf.new_page()
    encrypted=pdf.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,user_pw='test-only-password',owner_pw='test-only-owner')
    with pytest.raises(SourceError,match='encrypted'):extract_pages(encrypted)
    large=pymupdf.open()
    for _ in range(601):large.new_page()
    monkeypatch.setattr(settings,'document_max_pages',600)
    with pytest.raises(SourceError,match='configured limit is 600'):extract_pages(large.tobytes())

def test_sync_partial_failures_keep_source_errors_and_release_lock(db,monkeypatch):
    from datetime import date
    from app.services import sync
    from app.models import SyncRun,Price
    monkeypatch.setattr(sync,'SessionLocal',lambda:db)
    def prices(ticker):
        if ticker!='INFY':raise SourceError('Controlled provider unavailability')
        return [{'date':date(2026,10,29),'close':100,'volume':1000,'source_url':'https://finance.yahoo.com/quote/INFY.NS/history/'},{'date':date(2026,10,30),'close':105,'volume':2000,'source_url':'https://finance.yahoo.com/quote/INFY.NS/history/'}]
    def unavailable(*a,**k):raise SourceError('Controlled exchange unavailability')
    monkeypatch.setattr(sync,'fetch_prices',prices);monkeypatch.setattr(sync,'fetch_announcements',unavailable)
    sync.run_sync()
    row=db.scalar(select(SyncRun));assert row.result['status']=='partial' and not row.result['announcements']['ok']
    assert row.result['prices']['INFY']['ok'] and row.completed_at is not None and not sync.SYNC_LOCK.locked()
    assert db.scalar(select(func.count()).select_from(Price).where(Price.mode=='sourced'))==2

def test_sync_busy_is_conflict_and_public_startup_requires_token(client,monkeypatch):
    main.SYNC_LOCK.acquire()
    try:assert client.post('/api/sync').status_code==409
    finally:main.SYNC_LOCK.release()
    monkeypatch.setattr(settings,'public_deployment',True)
    with pytest.raises(RuntimeError,match='token'):main.initialize()
