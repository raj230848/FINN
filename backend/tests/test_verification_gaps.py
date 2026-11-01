"""Acceptance gaps: process recovery, status visibility and hosted configuration."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
import importlib.util

import pytest
from sqlalchemy import select

from app import main
from app.ai import client as provider
from app.config import settings
from app.models import Company, Price, SyncRun, utcnow
from app.services.operations import ProcessMetrics, recover_interrupted_syncs


def test_restart_marks_unfinished_jobs_without_losing_partial_results(db):
    partial={'prices':{'INFY':{'ok':True,'sessions':123}},'status':'running'}
    interrupted=SyncRun(result=partial)
    completed=SyncRun(result={'status':'complete'},completed_at=utcnow())
    db.add_all([interrupted,completed]);db.commit()
    assert recover_interrupted_syncs(db)==1
    db.commit()
    assert interrupted.result['status']=='interrupted'
    assert interrupted.result['prices']==partial['prices']
    assert interrupted.completed_at
    assert completed.result=={'status':'complete'}
    assert recover_interrupted_syncs(db)==0


def test_metrics_are_bounded_thread_safe_and_reject_arbitrary_text():
    metric=ProcessMetrics()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda _:metric.record('gemini','success',tokens=12,duration_ms=30),range(100)))
    metric.record('private prompt','private key')
    metric.record('gemini','invalid_response',tokens='private text',attempts=True)
    result=metric.snapshot()
    assert result['counts']=={'gemini.success':100,'gemini.invalid_response':1}
    assert 'tokens' not in result['last']['gemini']
    assert 'attempts' not in result['last']['gemini']
    result['counts'].clear()
    assert metric.snapshot()['counts']['gemini.success']==100


def test_model_failure_increments_sanitized_metric(monkeypatch):
    metric=ProcessMetrics();monkeypatch.setattr(provider,'metrics',metric)
    monkeypatch.setattr(settings,'gemini_api_key','')
    with pytest.raises(provider.ProviderError):provider.structured_call('private prompt',{},main.ResearchIn)
    assert metric.snapshot()['counts']=={'gemini.not_configured':1}
    assert 'private prompt' not in str(metric.snapshot())


def test_operations_requires_backend_auth_and_has_no_credentials(client,monkeypatch):
    monkeypatch.setattr(settings,'finn_api_token','test-protected-token')
    assert client.get('/api/operations').status_code==401
    response=client.get('/api/operations',headers={'Authorization':'Bearer test-protected-token'})
    assert response.status_code==200
    assert 'test-protected-token' not in response.text
    assert response.json()['sources']['status']=='not_fetched'


def test_status_uses_latest_session_not_old_history_and_marks_missing_feeds(client,db):
    for company in db.scalars(select(Company)):
        company.watched=company.ticker=='INFY'
    db.add_all([Price(ticker='INFY',date=date(2025,1,1),close=100,volume=1,mode='sourced',source_url='https://example.com',fetched_at=utcnow()-timedelta(days=50)),Price(ticker='INFY',date=date(2026,10,30),close=120,volume=2,mode='sourced',source_url='https://example.com',fetched_at=utcnow())]);db.commit()
    status=client.get('/api/operations').json()['sources']
    assert status['status']=='recent_fetch'
    assert status['latest_market_session']=='2026-10-30'
    db.get(Company,'TCS').watched=True;db.commit()
    status=client.get('/api/operations').json()['sources']
    assert status['status']=='partial'
    assert status['covered_companies']==1 and status['watched_companies']==2


@pytest.fixture
def hosted_launcher():
    path=Path(__file__).resolve().parents[2]/'scripts/start_hosted.py'
    spec=importlib.util.spec_from_file_location('start_hosted',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def hosted_env(tmp_path):
    return {'FINN_API_TOKEN':'x'*32,'FINN_ACCESS_TOKEN':'a'*24,'FINN_SESSION_SECRET':'s'*32,'DATABASE_URL':'sqlite:///'+(tmp_path/'runtime.db').as_posix()}


def test_one_origin_hosting_keeps_backend_private(hosted_launcher,tmp_path):
    env,port=hosted_launcher.deployment_environment(hosted_env(tmp_path))
    assert env['BACKEND_URL']=='http://127.0.0.1:8000'
    assert env['FINN_PUBLIC_MODE']==env['PUBLIC_DEPLOYMENT']=='true'
    assert env['HOSTNAME']=='0.0.0.0' and port==8000


@pytest.mark.parametrize('key,value',[('FINN_API_TOKEN','short'),('FINN_ACCESS_TOKEN',''),('FINN_SESSION_SECRET','short'),('DATABASE_URL','sqlite:///relative.db'),('PORT','8000'),('PORT','70000')])
def test_unsafe_host_configuration_fails_before_start(hosted_launcher,tmp_path,key,value):
    env=hosted_env(tmp_path);env[key]=value
    with pytest.raises(ValueError):hosted_launcher.deployment_environment(env)
