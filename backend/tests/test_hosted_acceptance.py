import importlib.util
import json
from pathlib import Path

import httpx
import pytest

path=Path(__file__).resolve().parents[2]/'scripts/verify_hosted.py'
spec=importlib.util.spec_from_file_location('verify_hosted',path)
hosted=importlib.util.module_from_spec(spec);spec.loader.exec_module(hosted)


@pytest.mark.parametrize('url',['http://public.example','https://user:secret@example.com','https://example.com/?token=secret','https://example.com/path','https://example.com:notaport'])
def test_hosted_acceptance_rejects_unsafe_origins(url):
    with pytest.raises(ValueError):hosted.target_origin(url)


def test_remote_mutations_require_explicit_qa_scope():
    with pytest.raises(ValueError,match='isolated'):
        hosted.verify('https://finn.example','not-published',refresh=True)


def test_acceptance_never_calls_optional_provider_without_flags_or_leaks_code():
    calls=[];logged_in=False
    def handle(request):
        nonlocal logged_in
        calls.append((request.method,request.url.path))
        p=request.url.path
        if p=='/':return httpx.Response(200,text='FINN')
        if p=='/api/ready':return httpx.Response(200,json={'status':'ready'})
        if p=='/api/session':
            logged_in=request.method=='POST'
            return httpx.Response(200,json={'ok':True},headers={'set-cookie':'finn_session=private-test-cookie; Path=/; HttpOnly; Secure; SameSite=Strict'})
        if not logged_in:return httpx.Response(401,json={'detail':'Sign in'})
        values={
            '/api/health':{'status':'ok','ai_configured':True},
            '/api/dashboard':{'companies':[],'last_sync':None,'as_of':'2026-11-01'},
            '/api/operations':{'sources':{},'metrics':{},'push':{}},
            '/api/companies':[],
            '/api/announcements':{'items':[],'coverage':{}},
            '/api/notifications':{'items':[],'unread_count':0},
            '/api/preferences':{'price_threshold':5,'volume_multiplier':2,'lookback':20,'companies':[],'categories':[]},
            '/api/push/config':{'available':False},'/api/push/status':{'enabled':False},
        }
        return httpx.Response(200,json=values.get(p,[]))
    report=hosted.verify('https://finn.example','private-test-code',transport=httpx.MockTransport(handle))
    assert report['summary']['failed']==0
    assert report['summary']['business_operations']==25
    assert report['summary']['operations_not_verified']>0
    assert not any(m=='POST' and p!='/api/session' for m,p in calls)
    encoded=json.dumps(report)
    assert 'private-test-code' not in encoded and 'private-test-cookie' not in encoded


def test_readiness_failure_is_not_reported_as_success():
    report=hosted.verify('https://finn.example','',transport=httpx.MockTransport(lambda _:httpx.Response(503,json={'status':'unavailable'})))
    assert report['summary']['failed']>0
