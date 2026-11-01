"""Protected production-route audit using disposable local credentials only."""
import json
import os
import time
from datetime import datetime,timezone
from pathlib import Path
import httpx

base='http://127.0.0.1:3004';code=os.environ['AUDIT_ACCESS_CODE']
rows=[]
with httpx.Client(base_url=base,timeout=30) as client:
    def call(method,path,expected,*,body=None,raw=None,origin=base,label=None):
        headers={'Origin':origin} if origin else {}
        if raw is not None:headers['Content-Type']='application/json'
        start=time.monotonic()
        response=client.request(method,path,headers=headers,json=body) if raw is None else client.request(method,path,headers=headers,content=raw)
        row={'method':method,'path':path,'scenario':label or path,'http_status':response.status_code,'expected_status':expected,'passed':response.status_code==expected,'elapsed_ms':round((time.monotonic()-start)*1000)}
        if method=='POST' and path=='/api/session' and response.status_code==200:
            cookie=response.headers.get('set-cookie','').lower();row['http_only']='httponly' in cookie;row['same_site_strict']='samesite=strict' in cookie
        rows.append(row);return response
    call('GET','/api/companies',401,origin=None,label='anonymous proxy blocked')
    call('GET','/api/session',405,label='unsupported session method')
    call('POST','/api/session',403,body={'access_code':code},origin='https://untrusted.invalid',label='cross-origin sign-in blocked')
    call('POST','/api/session',401,body={'access_code':'wrong'},label='wrong access code')
    call('POST','/api/session',400,raw=b'{broken',label='invalid JSON')
    call('POST','/api/session',413,raw=b'{"access_code":"'+b'x'*2100+b'"}',label='oversized sign-in body')
    call('POST','/api/session',413,raw=iter([b'{"access_code":"',b'x'*2100,b'"}']),label='chunked oversized sign-in body')
    call('POST','/api/session',200,body={'access_code':code},label='valid sign-in')
    call('GET','/api/companies',200,label='authenticated GET proxy')
    preferences=client.get('/api/preferences').json();body={k:preferences[k] for k in ('price_threshold','volume_multiplier','lookback','companies','categories')}
    call('PUT','/api/preferences',200,body=body,label='authenticated PUT proxy')
    call('PATCH','/api/companies/INFY',200,body={'watched':True},label='authenticated PATCH proxy')
    call('POST','/api/research',200,body={'ticker':'CERA','question':'What is revenue?','use_ai':False},label='authenticated POST proxy')
    if os.environ.get('AUDIT_RATE_CHECK')=='1':
        statuses=[];retry=None
        for _ in range(12):
            response=client.post('/api/research',headers={'Origin':base},json={'ticker':'CERA','question':'What is revenue?','use_ai':False})
            statuses.append(response.status_code)
            if response.status_code==429:retry=response.headers.get('retry-after');break
        rows.append({'method':'POST','path':'/api/research','scenario':'backend rate limit and Retry-After through proxy','http_status':statuses[-1],'expected_status':429,'passed':statuses[-1]==429 and retry=='60','retry_after':retry,'attempt_statuses':statuses})
    call('POST','/api/notifications/read-all?mode=demo',403,origin='https://untrusted.invalid',label='cross-origin mutation blocked')
    call('DELETE','/api/session',403,origin='https://untrusted.invalid',label='cross-origin logout blocked')
    call('DELETE','/api/session',200,label='same-origin logout')
    call('GET','/api/companies',401,origin=None,label='cookie invalidated after logout')
    rate=[]
    for _ in range(12):
        response=client.post('/api/session',headers={'Origin':base},json={'access_code':'wrong'})
        rate.append(response.status_code)
        if response.status_code==429:break
    rows.append({'method':'POST','path':'/api/session','scenario':'failed-login throttle','http_status':rate[-1],'expected_status':429,'passed':rate[-1]==429,'attempt_statuses':rate})
report={'checked_at':datetime.now(timezone.utc).isoformat(),'target':base,'scope':'local protected production-mode server; not a public HTTPS deployment','checks':rows,'summary':{'passed':sum(r['passed'] for r in rows),'failed':sum(not r['passed'] for r in rows)},'exported_operations_verified':['GET proxy','POST proxy','PUT proxy','PATCH proxy','POST session','DELETE session']}
out=Path('artifacts/comprehensive-audit/frontend-http.json');out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary']))
