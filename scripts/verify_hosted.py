"""Hosted same-origin acceptance. --qa authorizes mutations on an isolated desk.

FINN_HOSTED_ACCESS_CODE is read only from the environment. Reports omit cookies,
credentials, subscription details, prompts and full response bodies.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

import httpx


def target_origin(value):
    try:
        url=urlsplit(value)
        port=url.port
    except ValueError:
        raise ValueError('Malformed frontend URL.') from None
    if url.username or url.password or url.query or url.fragment or url.path not in ('','/') or not url.hostname or (port is not None and not 1<=port<=65535):
        raise ValueError('Use a frontend origin without paths, credentials or query strings.')
    if url.scheme!='https' and not (url.scheme=='http' and url.hostname in ('127.0.0.1','localhost')):
        raise ValueError('Use HTTPS for remote acceptance; local loopback HTTP is allowed.')
    return value.rstrip('/')


def verify(base, code, *, qa=False, refresh=False, gemini=False, ticker=None, transport=None):
    base=target_origin(base)
    if any((refresh,gemini,ticker)) and not qa:
        raise ValueError('Use --qa only against an isolated evaluator desk before mutation/provider checks.')
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'frontend_origin':base,'isolated_qa_acknowledged':qa,'checks':[],'operations':[],'limits':['Physical-device display, provider semantic correctness and hosting-disk durability require separate acceptance.','Push subscribe needs an actual browser-generated subscription; this script never fabricates one.']}
    with httpx.Client(base_url=base,timeout=55,transport=transport,follow_redirects=False) as client:
        def call(method,path,expected=200,*,template=None,keys=None,body=None,label=None):
            row={'scenario':label or path,'method':method,'path':template or path.split('?')[0],'expected':expected}
            try:
                response=client.request(method,path,headers={'Origin':base},json=body) if body is not None else client.request(method,path,headers={'Origin':base})
                row['http_status']=response.status_code
                try:data=response.json()
                except ValueError:data=None
                row['schema_valid']=keys is None or isinstance(data,dict) and all(k in data for k in keys)
                row['status']='passed' if response.status_code==expected and row['schema_valid'] else 'failed'
                if path=='/api/session' and method=='POST' and expected==200:
                    cookie=response.headers.get('set-cookie','').lower()
                    row['http_only']='httponly' in cookie;row['same_site_strict']='samesite=strict' in cookie
                    row['secure']='secure' in cookie
                    if not row['http_only'] or not row['same_site_strict'] or (base.startswith('https:') and not row['secure']):row['status']='failed'
            except httpx.HTTPError as error:
                data=None;row.update(status='failed',error_type=type(error).__name__)
            report['checks'].append(row)
            if template:report['operations'].append(row.copy())
            return data if row['status']=='passed' else None
        call('GET','/',label='frontend loads')
        call('GET','/api/ready',keys=['status'],label='public readiness')
        call('GET','/api/companies',401,label='anonymous desk blocked')
        if not code:
            report['limits'].append('FINN_HOSTED_ACCESS_CODE missing; authenticated acceptance not run.')
        else:
            call('POST','/api/session',body={'access_code':code},label='HTTPS-aware sign-in')
            companies=call('GET','/api/companies',template='/api/companies')
            call('GET','/api/health',template='/api/health',keys=['status','ai_configured'])
            dashboard=call('GET','/api/dashboard?mode=sourced',template='/api/dashboard',keys=['companies','last_sync','as_of'])
            call('GET','/api/operations',template='/api/operations',keys=['sources','metrics','push'])
            feed=call('GET','/api/announcements?mode=demo&window=7d',template='/api/announcements',keys=['items','coverage'])
            call('GET','/api/alerts?mode=sourced',template='/api/alerts')
            notifications=call('GET','/api/notifications?mode=demo',template='/api/notifications',keys=['items','unread_count'])
            prefs=call('GET','/api/preferences',template='/api/preferences',keys=['price_threshold','volume_multiplier','lookback','companies','categories'])
            call('GET','/api/push/config',template='/api/push/config',keys=['available'])
            call('GET','/api/push/status?device_id='+'q'*32,template='/api/push/status',keys=['enabled'])
            for suffix in ('documents','financials','guidance'):
                call('GET','/api/companies/INFY/'+suffix,template='/api/companies/{ticker}/'+suffix)
            if feed and feed.get('items'):
                call('GET',f'/api/announcements/{feed["items"][0]["id"]}/context',template='/api/announcements/{filing_id}/context',keys=['status','message'])
            last=(dashboard or {}).get('last_sync')
            if last:call('GET',f'/api/sync/{last["id"]}',template='/api/sync/{run_id}',keys=['id','result'])
            if qa:
                if prefs:
                    original={k:prefs[k] for k in ('price_threshold','volume_multiplier','lookback','companies','categories')}
                    temporary={**original,'price_threshold':6.25 if original['price_threshold']!=6.25 else 6.5}
                    try:
                        call('PUT','/api/preferences',template='/api/preferences',body=temporary,keys=['price_threshold'])
                        saved=call('GET','/api/preferences',label='preference side effect persists')
                        report['checks'].append({'scenario':'preference persisted value','status':'passed' if saved and saved['price_threshold']==temporary['price_threshold'] else 'failed'})
                    finally:call('PUT','/api/preferences',body=original,label='restore QA preferences')
                if isinstance(companies,list) and companies:
                    company=next((c for c in companies if c['ticker']=='INFY'),companies[0]);path='/api/companies/'+company['ticker']
                    try:
                        result=call('PATCH',path,template='/api/companies/{ticker}',body={'watched':not company['watched']},keys=['watched'])
                        saved=call('GET','/api/companies',label='watchlist value persists')
                        persisted=next((c for c in saved if c['ticker']==company['ticker']),None) if isinstance(saved,list) else None
                        report['checks'].append({'scenario':'watchlist side effect','status':'passed' if result and persisted and persisted['watched'] is not company['watched'] else 'failed'})
                    finally:call('PATCH',path,body={'watched':company['watched']},label='restore QA watchlist')
                if notifications and notifications.get('items'):
                    call('POST',f'/api/notifications/{notifications["items"][0]["id"]}/read',template='/api/notifications/{event_id}/read')
                call('POST','/api/notifications/read-all?mode=demo',template='/api/notifications/read-all')
                after=call('GET','/api/notifications?mode=demo',label='read state persists')
                report['checks'].append({'scenario':'read-all persisted value','status':'passed' if after and after['unread_count']==0 else 'failed'})
                call('POST','/api/push/unsubscribe',template='/api/push/unsubscribe',body={'device_id':'q'*32})
                if refresh:
                    started=call('POST','/api/sync',202,template='/api/sync',keys=['id'])
                    if started and 'id' in started:
                        deadline=time.monotonic()+300
                        current=None
                        while time.monotonic()<deadline:
                            current=call('GET',f'/api/sync/{started["id"]}',template='/api/sync/{run_id}',keys=['id','result'])
                            if not current or current.get('completed_at'):break
                            time.sleep(2)
                        report['checks'].append({'scenario':'real refresh completion','status':'passed' if current and current.get('completed_at') and current.get('result',{}).get('status') in ('complete','partial') else 'failed','refresh_status':(current or {}).get('result',{}).get('status')})
                if ticker:
                    discovery=call('POST','/api/companies/'+ticker+'/discover',template='/api/companies/{ticker}/discover',keys=['company','documents'])
                    candidates=(discovery or {}).get('documents',[])
                    if candidates:
                        candidate=candidates[0]
                        call('POST','/api/documents',template='/api/documents',body={'ticker':ticker,'title':candidate['title'],'period':candidate['period'],'kind':candidate['kind'],'url':candidate['url']},keys=['id','page_count'])
                    else:report['limits'].append('No import candidate available for the requested ticker.')
                result=call('POST','/api/research',template='/api/research',body={'ticker':'INFY','question':'What FY25 operating margin guidance did management provide?','use_ai':gemini,'refresh':gemini},keys=['method','evidence','cached'])
                if gemini:
                    report['checks'].append({'scenario':'fresh source-cited Gemini answer','status':'passed' if result and result['method']=='grounded_ai' and not result['cached'] and result['evidence'] else 'failed','method':(result or {}).get('method'),'citations':[{'page':e['page'],'url':e['url']} for e in (result or {}).get('evidence',[])]})
                call('POST','/api/session',body={'access_code':code},label='session renewal')
            call('DELETE','/api/session',label='logout')
            call('GET','/api/companies',401,label='logout removes access')
    # Exact route inventory, including optional operations that must remain unverified.
    expected={('GET',p) for p in ['/api/health','/api/operations','/api/companies','/api/dashboard','/api/announcements','/api/alerts','/api/notifications','/api/preferences','/api/push/config','/api/push/status','/api/sync/{run_id}','/api/announcements/{filing_id}/context','/api/companies/{ticker}/documents','/api/companies/{ticker}/financials','/api/companies/{ticker}/guidance']}
    expected.update({('PATCH','/api/companies/{ticker}'),('PUT','/api/preferences')})
    expected.update(('POST',p) for p in ['/api/sync','/api/research','/api/documents','/api/companies/{ticker}/discover','/api/push/subscribe','/api/push/unsubscribe','/api/notifications/read-all','/api/notifications/{event_id}/read'])
    seen={(r['method'],r['path']) for r in report['operations']}
    report['operation_inventory']=[{'method':m,'path':p,'status':'passed' if any(r['status']=='passed' for r in report['operations'] if (r['method'],r['path'])==(m,p)) else 'failed' if (m,p) in seen else 'not_verified'} for m,p in sorted(expected)]
    report['summary']={'passed':sum(r['status']=='passed' for r in report['checks']),'failed':sum(r['status']=='failed' for r in report['checks']),'business_operations':len(expected),'operations_not_verified':sum(r['status']=='not_verified' for r in report['operation_inventory'])}
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True);parser.add_argument('--qa',action='store_true',help='Explicit acknowledgement: target is a disposable isolated evaluator desk.')
    parser.add_argument('--refresh',action='store_true');parser.add_argument('--gemini',action='store_true');parser.add_argument('--ticker')
    parser.add_argument('--out',default='artifacts/hosted-acceptance.json')
    args=parser.parse_args()
    try:report=verify(args.url,os.environ.get('FINN_HOSTED_ACCESS_CODE',''),qa=args.qa,refresh=args.refresh,gemini=args.gemini,ticker=args.ticker)
    except ValueError as error:parser.error(str(error))
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(out.resolve()),'summary':report['summary']}))
    return 1 if report['summary']['failed'] else 0


if __name__=='__main__':sys.exit(main())
