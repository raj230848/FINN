import base64
from datetime import timedelta
from types import SimpleNamespace
import pytest
from sqlalchemy import select,func
from app.models import PushRecipient,PushDelivery,SignalEvent,Financial,Guidance,Company,utcnow
from app.services.push import validate_subscription,process_pending,queue_event
from app.services.sync import save_announcements
from app.services.materiality import classify
from app.services.research import validate_claims,matches_period
from app.schemas import GroundingReviewOut,AnalysisOut,SynthesisOut,SynthesisClaim
from app.config import settings

def subscription():
    enc=lambda value:base64.urlsafe_b64encode(value).decode().rstrip('=')
    return {'endpoint':'https://fcm.googleapis.com/fcm/send/test-only','keys':{'p256dh':enc(b'\x04'+b'x'*64),'auth':enc(b'x'*16)}}

def add_event(db):
    save_announcements(db,[{'ticker':'INFY','title':'Resignation of Chief Financial Officer','published_at':utcnow(),'source_url':'https://nsearchives.nseindia.com/test-new-cfo.pdf','text':'CFO resignation effective next month.'}]);db.commit()
    return db.scalar(select(SignalEvent).where(SignalEvent.mode=='sourced'))

def test_push_opt_in_history_retry_and_opt_out(db):
    existing=add_event(db)
    recipient=PushRecipient(id='a'*32,subscription=subscription(),enabled_at=utcnow()-timedelta(seconds=1));db.add(recipient);db.commit()
    queue_event(db,existing);queue_event(db,existing);db.commit()
    assert db.scalar(select(func.count()).select_from(PushDelivery))==1
    sent=[]
    assert process_pending(db,sender=lambda s,p:sent.append(p))==1
    assert process_pending(db,sender=lambda s,p:sent.append(p))==0
    assert len(sent)==1 and sent[0]['event_id']==existing.id
    recipient.enabled=False;db.commit()
    save_announcements(db,[{'ticker':'TCS','title':'Appointment of CFO','published_at':utcnow(),'source_url':'https://nsearchives.nseindia.com/another-cfo.pdf','text':'CFO appointed with effect from tomorrow.'}]);db.commit()
    assert db.scalar(select(func.count()).select_from(PushDelivery))==1

def test_push_retry_is_bounded_and_disabled_recipient_cancels(db):
    db.add(PushRecipient(id='a'*32,subscription=subscription(),enabled_at=utcnow()-timedelta(seconds=5)));db.commit();add_event(db)
    calls=[]
    def fail(*args):calls.append(1);raise RuntimeError('private endpoint must not be logged')
    now=utcnow();process_pending(db,sender=fail,now=now)
    delivery=db.scalar(select(PushDelivery));assert delivery.state=='retry' and delivery.attempts==1
    process_pending(db,sender=fail,now=now);assert len(calls)==1
    db.get(PushRecipient,'a'*32).enabled=False;db.commit()
    process_pending(db,sender=fail,now=now+timedelta(minutes=3));assert delivery.state=='cancelled' and len(calls)==1

def test_push_rejects_private_or_untrusted_endpoints_and_short_keys():
    assert validate_subscription(subscription())['endpoint'].startswith('https://fcm.googleapis.com/')
    for endpoint in ['http://127.0.0.1/','https://evil.example/','https://fcm.googleapis.com.evil.example/','https://user:pass@fcm.googleapis.com/']:
        with pytest.raises(ValueError):validate_subscription({**subscription(),'endpoint':endpoint})
    with pytest.raises(ValueError):validate_subscription({**subscription(),'keys':{'p256dh':'a','auth':'b'}})

def test_push_enable_does_not_replay_history_or_send_demo(db):
    existing=add_event(db)
    db.add(PushRecipient(id='b'*32,subscription=subscription(),enabled_at=utcnow()+timedelta(seconds=1)));db.commit()
    queue_event(db,existing);db.commit()
    assert db.scalar(select(func.count()).select_from(PushDelivery))==0

def test_push_respects_selected_tickers_and_categories(db):
    from app.models import Preference
    pref=db.get(Preference,1);pref.companies=['TCS']
    db.add(PushRecipient(id='c'*32,subscription=subscription(),enabled_at=utcnow()-timedelta(seconds=5)));db.commit()
    add_event(db)
    assert db.scalar(select(func.count()).select_from(PushDelivery))==0
    pref.companies=['INFY'];pref.categories=['results'];db.commit()
    save_announcements(db,[{'ticker':'INFY','title':'Appointment of CFO','published_at':utcnow(),'source_url':'https://nsearchives.nseindia.com/category-test.pdf','text':'New CFO appointed.'}]);db.commit()
    assert db.scalar(select(func.count()).select_from(PushDelivery))==0
    save_announcements(db,[{'ticker':'INFY','title':'Quarterly financial results','published_at':utcnow(),'source_url':'https://nsearchives.nseindia.com/results-test.pdf','text':'Consolidated quarterly financial results.'}]);db.commit()
    assert db.scalar(select(func.count()).select_from(PushDelivery))==1

def test_wipro_five_quarters_pending_guidance_and_accounting_notes(client,db):
    result=client.get('/api/companies/WIPRO/financials').json()
    assert len(result['periods'])==5 and result['current_period']=='2027-Q2'
    metrics={r['metric']:r for r in result['rows']}
    assert metrics['revenue']['current']==247527 and metrics['revenue']['previous']==244786 and metrics['revenue']['last_year']==226973
    assert metrics['pat']['current']==31997 and metrics['ebitda']['current'] is None
    prior=client.get('/api/companies/WIPRO/financials?period=2026-Q3').json()
    assert any('3,028' in flag for flag in prior['review_flags'])
    assert client.get('/api/companies/WIPRO/financials?period=2020-Q1').status_code==404
    guidance=client.get('/api/companies/WIPRO/guidance').json()
    assert guidance['distinct_targets']==4 and guidance['items'][-1]['status']=='pending'
    assert guidance['items'][-1]['actual_url'] is None and guidance['items'][-1]['deviation_pp'] is None
    assert [g['status'] for g in guidance['items'][:3]]==['achieved']*3
    db.add(Guidance(ticker='WIPRO',data={**guidance['items'][0],'actual_period':'FY99'}));db.commit()
    assert len(client.get('/api/companies/WIPRO/guidance').json()['items'])==4

def test_claim_numbers_must_exist_in_the_actual_cited_passage():
    evidence=[{'id':1,'excerpt':'Revenue grew 4.2 percent.'},{'id':2,'excerpt':'Cash flow is 99 million.'}]
    with pytest.raises(ValueError):validate_claims('Revenue grew 99 percent [1].',evidence)
    validate_claims('Revenue grew 4.2 percent [1].',evidence)

def test_reported_range_separators_and_decimal_format_keep_the_same_values():
    evidence=[{'id':1,'excerpt':'Revenue growth outlook is 4.5%-5.0%, with operating margin of 20%-22%.'}]
    validate_claims('Revenue growth guidance is 4.5% to 5%, with margin of 20% to 22% [1].',evidence)
    with pytest.raises(ValueError):validate_claims('Revenue growth guidance is -4.5% to 5% [1].',evidence)

def test_period_aware_retrieval_filters_wrong_year_and_quarter():
    doc=SimpleNamespace(title='Company results',period='Q2 FY26')
    chunk=SimpleNamespace(text='Revenue outlook for FY26.')
    assert matches_period('What is Q2 FY26 revenue?',chunk,doc)
    assert not matches_period('What is Q3 FY25 revenue?',chunk,doc)
    assert not matches_period('What is FY25 revenue?',chunk,doc)

def test_recording_is_not_relabelled_as_new_results():
    result=classify('Analysts/Institutional Investor Meet/Con. Call Updates','Audio recording of the discussion on the Unaudited Financial Results is available.')
    assert result['category']=='earnings_call' and result['priority']=='medium'

def test_colon_does_not_bypass_claim_citations():
    with pytest.raises(ValueError):validate_claims('Management is guaranteed to outperform:',[{'id':1,'excerpt':'Reported historical results.'}])

def test_missing_quarters_and_currency_mismatch_stay_unavailable(client,db):
    current=db.scalar(select(Financial).where(Financial.ticker=='WIPRO',Financial.period=='2027-Q1'))
    current.currency='USD million';db.commit()
    result=client.get('/api/companies/WIPRO/financials').json()
    assert result['rows'][0]['previous'] is None and result['rows'][0]['qoq'] is None
    gap=client.get('/api/companies/WIPRO/financials?period=2026-Q2').json()
    assert gap['rows'][0]['previous'] is None and gap['rows'][0]['qoq'] is None

def test_false_but_cited_claim_fails_model_support_review(db,monkeypatch):
    import pymupdf
    from app.services import research as module
    from app.services.documents import store_document
    doc=pymupdf.open();p=doc.new_page();p.insert_text((40,60),'Infosys revenue grew 4.2 percent.\n'+('Revenue and cash flow.\n'*20))
    store_document(db,db.get(Company,'INFY'),'Issuer results','FY25','results','https://www.infosys.com/claim-review.pdf',doc.tobytes())
    citation=module.retrieve(db,'INFY','What is revenue growth?')[0]['id']
    monkeypatch.setattr(settings,'gemini_api_key','test-only')
    def generate(system,payload,schema,**kwargs):
        if schema is GroundingReviewOut:return GroundingReviewOut(supported=False,unsupported_claims=['Direction reversed'],reason='Source says grew; claim says fell.')
        return SynthesisOut(claims=[SynthesisClaim(text='Revenue fell 4.2 percent.',evidence_ids=[citation])])
    monkeypatch.setattr(module,'structured_call',generate)
    assert module.research(db,'INFY','What is revenue growth?',True)['method']=='extractive'

def test_explicit_refresh_calls_provider_again_and_replaces_one_cache_row(db,monkeypatch):
    import pymupdf
    from app.models import ResearchCache
    from app.services import research as module
    from app.services.documents import store_document
    pdf=pymupdf.open();page=pdf.new_page();page.insert_text((40,60),'Infosys revenue grew 4.2 percent.\n'+('Revenue outlook and cash flow.\n'*20))
    store_document(db,db.get(Company,'INFY'),'Refresh test report','FY25','results','https://www.infosys.com/refresh-check.pdf',pdf.tobytes())
    citation=module.retrieve(db,'INFY','What is revenue growth?')[0]['id'];calls=[]
    monkeypatch.setattr(settings,'gemini_api_key','test-only')
    def generate(system,payload,schema,**kwargs):
        calls.append(schema)
        if schema is GroundingReviewOut:return GroundingReviewOut(supported=True,reason='Reported fact')
        return SynthesisOut(claims=[SynthesisClaim(text='Revenue grew 4.2 percent.',evidence_ids=[citation])])
    monkeypatch.setattr(module,'structured_call',generate)
    assert not module.research(db,'INFY','What is revenue growth?',True)['cached']
    assert module.research(db,'INFY','What is revenue growth?',True)['cached']
    assert not module.research(db,'INFY','What is revenue growth?',True,refresh=True)['cached']
    assert len(calls)==4 and db.scalar(select(func.count()).select_from(ResearchCache))==1

@pytest.mark.parametrize('headline', ['Receipt of order worth INR 500 crore','Award of contract for infrastructure project','Letter of award received for power project'])
def test_material_order_examples_do_not_hide_as_routine(headline):
    assert classify(headline)['priority']!='low'
