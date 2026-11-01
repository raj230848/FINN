"""Explicit, bounded HTTP/provider audit against a disposable FINN database.

Never target the user's normal database: this exercises read state, preferences,
discovery, sync and imports. Credentials are read from env and never reported.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
parser=argparse.ArgumentParser()
parser.add_argument('--base-url',default='http://127.0.0.1:8002')
parser.add_argument('--out',default=str(ROOT/'artifacts/comprehensive-audit/live-http.json'))
args=parser.parse_args()
if args.base_url not in ('http://127.0.0.1:8002','http://localhost:8002'):parser.error('This mutation audit is restricted to the isolated local audit server on port 8002.')
token=os.environ.get('AUDIT_BACKEND_TOKEN','')
report={'checked_at':datetime.now(timezone.utc).isoformat(),'target':args.base_url,'database':'private disposable copy','operations':[],'observations':{}}
client=httpx.Client(base_url=args.base_url,headers={'Authorization':'Bearer '+token},timeout=55)

def call(method,path,template=None,body=None,expected=200,label=None,blocked=None):
    started=time.monotonic();r=client.request(method,path,json=body) if body is not None else client.request(method,path)
    row={'method':method,'route':template or path.split('?')[0],'scenario':label or 'live happy path','http_status':r.status_code,'expected_status':expected,'elapsed_ms':round((time.monotonic()-started)*1000)}
    row['status']='passed' if r.status_code==expected else 'configuration_blocked' if blocked and r.status_code==blocked else 'failed'
    report['operations'].append(row)
    try:data=r.json()
    except ValueError:data=None
    return r,data

try:
    for path in ['/docs','/redoc','/openapi.json','/docs/oauth2-redirect']:call('GET',path,label='framework documentation')
    _,health=call('GET','/api/health');report['observations']['health']=health
    _,companies=call('GET','/api/companies');report['observations']['watched_companies']=sum(c['watched'] for c in companies)
    for mode in ('demo','sourced'):call('GET','/api/dashboard?mode='+mode,'/api/dashboard')
    for window in ('24h','7d','30d'):
        _,feed=call('GET','/api/announcements?mode=sourced&window='+window,'/api/announcements')
        report['observations']['digest_'+window]={'total':feed['total'],'coverage':feed['coverage']}
    call('GET','/api/alerts?mode=sourced','/api/alerts')
    _,notifications=call('GET','/api/notifications?mode=sourced','/api/notifications')
    if notifications['items']:call('POST',f'/api/notifications/{notifications["items"][0]["id"]}/read','/api/notifications/{event_id}/read')
    call('POST','/api/notifications/read-all?mode=sourced','/api/notifications/read-all')
    _,zero=call('GET','/api/notifications?mode=sourced','/api/notifications',label='read-all persisted')
    report['observations']['read_all_unread_count']=zero['unread_count']
    _,feed=call('GET','/api/announcements?mode=sourced&window=30d','/api/announcements',label='source context sample')
    if feed['items']:call('GET',f'/api/announcements/{feed["items"][0]["id"]}/context','/api/announcements/{filing_id}/context')
    _,prefs=call('GET','/api/preferences');original={k:prefs[k] for k in ('price_threshold','volume_multiplier','lookback','companies','categories')}
    try:
        call('PUT','/api/preferences',body={**original,'price_threshold':0.1,'volume_multiplier':1.1})
        _,first=call('GET','/api/notifications?mode=sourced','/api/notifications',label='low threshold event count')
        call('PUT','/api/preferences',body={**original,'price_threshold':0.1,'volume_multiplier':1.1},label='repeat calculation')
        _,second=call('GET','/api/notifications?mode=sourced','/api/notifications',label='deduplication check')
        report['observations']['duplicate_events_after_repeat']=second['total']-first['total']
    finally:call('PUT','/api/preferences',body=original,label='restore QA preferences')
    watched=next(c for c in companies if c['ticker']=='INFY')['watched']
    try:call('PATCH','/api/companies/INFY','/api/companies/{ticker}',{'watched':False})
    finally:call('PATCH','/api/companies/INFY','/api/companies/{ticker}',{'watched':watched},label='restore watched state')
    _,push=call('GET','/api/push/config');report['observations']['push_configured']=push['available']
    device='a'*32
    call('POST','/api/push/subscribe',body={'device_id':device,'subscription':{}},expected=200,blocked=503,label='push requires configuration; no subscription sent')
    call('GET','/api/push/status?device_id='+device,'/api/push/status')
    call('POST','/api/push/unsubscribe',body={'device_id':device})
    print('Running real one-day Yahoo/NSE refresh…',flush=True)
    _,run=call('POST','/api/sync?filing_days=1','/api/sync',expected=202)
    if run and 'id' in run:
        run_id=run['id'];_,state=call('GET',f'/api/sync/{run_id}','/api/sync/{run_id}')
        deadline=time.monotonic()+300
        while not state.get('completed_at') and time.monotonic()<deadline:
            time.sleep(2);state=client.get(f'/api/sync/{run_id}').json()
        report['observations']['real_sync']=state.get('result',{})
        report['observations']['sync_completed']=bool(state.get('completed_at'))
    print('Checking unseen-issuer discovery and primary import…',flush=True)
    _,discovery=call('POST','/api/companies/HCLTECH/discover','/api/companies/{ticker}/discover',blocked=422)
    if discovery and discovery.get('company'):
        ticker=discovery['company']['ticker'];candidates=sorted(discovery['documents'],key=lambda d:d['kind']!='transcript')
        report['observations']['new_issuer']={'ticker':ticker,'candidate_count':len(candidates),'resolved':True}
        for candidate in candidates[:2]:
            _,doc=call('POST','/api/documents',body={'ticker':ticker,**candidate},label='live new-issuer primary import',blocked=422)
            if doc and 'id' in doc:
                report['observations']['new_issuer']['imported']={'id':doc['id'],'title':doc['title'],'source_url':doc['source_url'],'pages':doc['page_count']};break
        call('GET',f'/api/companies/{ticker}/documents','/api/companies/{ticker}/documents')
        _,answer=call('POST','/api/research',body={'ticker':ticker,'question':'What is the business and revenue outlook?','use_ai':False},label='unseen issuer extractive research')
        report['observations']['new_issuer']['research_method']=answer.get('method')
        report['observations']['new_issuer']['citations']=len(answer.get('evidence',[]))
    # A known reviewed primary URL independently exercises import if discovery is blocked.
    call('POST','/api/documents',body={'ticker':'WIPRO','title':'Wipro consolidated IFRS Q2 FY27','period':'Q2 FY27','kind':'results','url':'https://www.wipro.com/content/dam/nexus/en/investor/quarterly-results/2026-2027/q2fy27/consolidated-financial-statement-q2fy27.pdf'},label='live reviewed primary import',blocked=422)
    for path in ('financials','guidance'):call('GET','/api/companies/WIPRO/'+path,'/api/companies/{ticker}/'+path)
    # API auth failures are tested with a separate unauthenticated client.
    with httpx.Client(base_url=args.base_url,timeout=15) as anonymous:
        status=anonymous.get('/api/companies').status_code
        report['operations'].append({'method':'GET','route':'/api/companies','scenario':'anonymous backend access','expected_status':401,'http_status':status,'status':'passed' if status==401 else 'failed'})
    for method,path,expected in [('GET','/api/sync/99999999999999999999999',422),('GET','/api/announcements?priority=urgent',422),('POST','/api/notifications/999999/read',404)]:call(method,path,expected=expected,label='live invalid-input boundary')
    call('POST','/api/research',body={'ticker':'CERA','question':'What is the revenue outlook?','use_ai':True},label='no indexed evidence')
finally:
    client.close()
    report['summary']={'passed':sum(r['status']=='passed' for r in report['operations']),'failed':sum(r['status']=='failed' for r in report['operations']),'configuration_blocked':sum(r['status']=='configuration_blocked' for r in report['operations'])}
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(out),'summary':report['summary']},indent=2),flush=True)
