from sqlalchemy import select, func
from app.config import settings
from app.models import Alert, Company
from app.services.alerts import evaluate_alerts

def test_dashboard_real_backend_contract(client):
    data=client.get('/api/dashboard').json()
    assert data['stats']['companies']==18
    assert data['stats']['volume_alerts']>=3
    assert len(data['companies'])==18
    assert data['mode']=='demo'
    sourced=client.get('/api/dashboard?mode=sourced').json()
    assert sourced['stats']['coverage']==0
    assert all(c['close'] is None for c in sourced['companies'])

def test_preferences_persist_and_recalculate_without_duplicates(client,db):
    body={'price_threshold':10,'volume_multiplier':4,'lookback':20,'companies':[],'categories':['results']}
    assert client.put('/api/preferences',json=body).status_code==200
    assert client.get('/api/preferences').json()['price_threshold']==10
    assert client.get('/api/alerts').json()==[]
    body.update(price_threshold=5,volume_multiplier=2)
    client.put('/api/preferences',json=body)
    count=len(client.get('/api/alerts').json())
    evaluate_alerts(db,'demo');db.commit()
    assert db.scalar(select(func.count()).select_from(Alert))==count
    assert client.put('/api/preferences',json={**body,'lookback':0}).status_code==422
    assert client.put('/api/preferences',json={**body,'categories':['invented']}).status_code==422

def test_watchlist_changes_monitoring(client):
    assert client.patch('/api/companies/INFY',json={'watched':False}).json()['watched'] is False
    assert client.get('/api/dashboard').json()['stats']['companies']==17

def test_unseen_ticker_discovery_generalises(client,monkeypatch):
    from app import main
    monkeypatch.setattr(main,'resolve_company',lambda t: {'ticker':t,'name':'Unseen Company Limited','sector':'Test sector','website':'https://example.com','verified':True})
    monkeypatch.setattr(main,'discover_documents',lambda c: [])
    response=client.post('/api/companies/UNSEEN/discover')
    assert response.status_code==200
    assert response.json()['company']['ticker']=='UNSEEN'
    result=client.post('/api/research',json={'ticker':'UNSEEN.NS','question':'What is the growth outlook?','use_ai':False}).json()
    assert result['method']=='insufficient_evidence' and result['evidence']==[]
    assert 'do not establish' in result['answer']

def test_provider_errors_and_invalid_inputs(client,monkeypatch):
    from app import main
    from app.ingestion.http import SourceError
    def unavailable(t): raise SourceError('Provider blocked this request. No company data substituted.')
    monkeypatch.setattr(main,'resolve_company',unavailable)
    assert client.post('/api/companies/NOTREAL/discover').status_code==422
    assert client.post('/api/research',json={'ticker':'http://localhost','question':'test'}).status_code==422
    assert client.post('/api/research',json={'ticker':'NOTINDEXED','question':'What is revenue?'}).status_code==404
    assert client.get('/api/sync/999999').status_code==404

def test_optional_shared_api_token(client,monkeypatch):
    monkeypatch.setattr(settings,'finn_api_token','test-token')
    assert client.get('/api/health').status_code==200
    assert client.get('/api/companies').status_code==401
    assert client.get('/api/companies',headers={'Authorization':'Bearer test-token'}).status_code==200
