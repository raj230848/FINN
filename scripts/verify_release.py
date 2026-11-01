"""Reproducible live acceptance report. Never saves keys, cookies or excerpts.

Use --refresh for real ingestion, --gemini for two paid provider-backed questions,
and --threshold-check ONLY against a disposable acceptance-test database.
"""
import argparse
import json
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.config import settings

parser=argparse.ArgumentParser()
parser.add_argument('--backend-url',default='http://127.0.0.1:8000')
parser.add_argument('--frontend-url')
parser.add_argument('--refresh',action='store_true')
parser.add_argument('--gemini',action='store_true')
parser.add_argument('--threshold-check',action='store_true')
parser.add_argument('--out',default=str(ROOT/'artifacts/release-acceptance.json'))
args=parser.parse_args()
for address in filter(None,[args.backend_url,args.frontend_url]):
    url=urlparse(address)
    if url.username or url.password or url.query or url.fragment or (url.scheme!='https' and url.hostname not in ('127.0.0.1','localhost')):
        parser.error('Use HTTPS hosting URLs or local loopback URLs, without credentials/query parameters.')

report={'checked_at':datetime.now(timezone.utc).isoformat(),'target':{'backend':args.backend_url,'frontend':args.frontend_url,'disposable_threshold_check':args.threshold_check},'checks':{},'limits':[]}
headers={'Authorization':f'Bearer {settings.finn_api_token}'} if settings.finn_api_token else {}
with httpx.Client(base_url=args.backend_url.rstrip('/')+'/api/',headers=headers,timeout=55) as client:
    def call(method,path,**kwargs):
        response=client.request(method,path,**kwargs);response.raise_for_status();return response.json()
    health=call('GET','health')
    report['checks']['backend']={'status':'passed','provider':health.get('ai_provider'),'model':health.get('ai_model'),'ai_configured':health.get('ai_configured'),'access_protected':health.get('access_protected')}
    if args.refresh:
        run=call('POST','sync?filing_days=30');deadline=time.monotonic()+300
        while time.monotonic()<deadline:
            current=call('GET',f'sync/{run["id"]}')
            if current.get('completed_at'):break
            time.sleep(2)
        else:raise RuntimeError('Refresh did not finish within five minutes; inspect the persisted sync run.')
        report['checks']['refresh']={'run_id':run['id'],'result':current['result']}
    dashboard=call('GET','dashboard?mode=sourced')
    quotes=dashboard['companies']
    report['checks']['prices']={'status':'passed' if all(q['close'] is not None and q['date'] and str(q['source_url']).startswith('https://') for q in quotes) else 'partial','count':len(quotes),'sessions':{q['ticker']:q['date'] for q in quotes},'source_urls':{q['ticker']:q['source_url'] for q in quotes}}
    report['checks']['digests']={}
    for window in ('24h','7d','30d'):
        feed=call('GET',f'announcements?mode=sourced&window={window}&limit=300')
        report['checks']['digests'][window]={'count':feed['total'],'loaded':len(feed['items']),'has_more':feed['has_more'],'coverage':feed['coverage']}
    if args.threshold_check:
        prefs=call('GET','preferences')
        original={k:prefs[k] for k in ('price_threshold','volume_multiplier','lookback','companies','categories')}
        try:
            low={**original,'price_threshold':0.1,'volume_multiplier':1.1}
            call('PUT','preferences',json=low)
            first=call('GET','notifications?mode=sourced')['total']
            alerts=call('GET','alerts?mode=sourced')
            call('PUT','preferences',json=low)
            second=call('GET','notifications?mode=sourced')['total']
            assert first==second,'Repeated calculation created duplicate events'
            assert all(a['date'] in {q['date'] for q in quotes} and a['mode']=='sourced' for a in alerts)
            report['checks']['thresholds']={'status':'passed','real_eod_alerts':len(alerts),'duplicate_events':second-first}
        finally:call('PUT','preferences',json=original)
    ai=[]
    if args.gemini and health.get('ai_configured'):
        for question in ['What FY25 growth guidance did management provide?','What does the FY25 report say about operating cash flow?']:
            result=call('POST','research',json={'ticker':'INFY','question':question,'use_ai':True})
            ai.append({'question':question,'method':result['method'],'cached':result['cached'],'grounding':result.get('grounding'),'citations':[{'id':e['id'],'page':e['page'],'url':e['url']} for e in result['evidence']]})
        report['checks']['gemini']={'status':'passed' if all(a['method']=='grounded_ai' and a['citations'] and not a['cached'] for a in ai) else 'not_verified','requests':ai}
    else:
        report['checks']['gemini']={'status':'blocked' if not health.get('ai_configured') else 'not_run','reason':'A rotated server-side key and --gemini are required. Configuration alone is not provider proof.'}
    unknown=client.post('research',json={'ticker':'FINNNOTAREALSTOCK','question':'What is the revenue outlook?','use_ai':False})
    report['checks']['unknown_ticker']={'status':'passed' if unknown.status_code==404 else 'failed','http_status':unknown.status_code}
    if args.frontend_url:
        with httpx.Client(timeout=30) as browser:
            home=browser.get(args.frontend_url)
            proxy=browser.get(args.frontend_url.rstrip('/')+'/api/companies')
            report['checks']['frontend']={'status':'passed' if home.status_code==200 and proxy.status_code in (200,401) else 'failed','home_http_status':home.status_code,'anonymous_api_status':proxy.status_code,'note':'An HTTP check does not replace a real-device end-to-end test.'}
report['limits']+=['A push-service acceptance is not proof of device display.','Physical-device, incognito hosted login and hosting restart tests require the actual target environment.']
out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':str(out.resolve()),'checks':{k:v.get('status','recorded') for k,v in report['checks'].items() if isinstance(v,dict)}},indent=2))
