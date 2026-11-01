"""Actual production-proxy outage and two-session checks in an isolated local desk."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
import httpx

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/verification-gaps'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    database=OUT/('resilience-'+secrets.token_hex(4)+'.db')
    base='http://127.0.0.1:3007';backend='http://127.0.0.1:8007'
    token=secrets.token_urlsafe(32);code=secrets.token_urlsafe(24)
    env={**os.environ,'DATABASE_URL':'sqlite:///'+database.as_posix(),'FINN_API_TOKEN':token,'FINN_ACCESS_TOKEN':code,'FINN_SESSION_SECRET':secrets.token_urlsafe(40),'FINN_PUBLIC_MODE':'true','FINN_PUBLIC_ORIGIN':base,'BACKEND_URL':backend,'PORT':'3007','HOSTNAME':'127.0.0.1','PUBLIC_DEPLOYMENT':'true','ENABLE_SCHEDULER':'false','GEMINI_API_KEY':'','VAPID_PRIVATE_KEY':'','VAPID_PUBLIC_KEY':'','VAPID_SUBJECT':''}
    for origin in (base,backend):
        try:httpx.get(origin+'/api/health',timeout=1)
        except httpx.TransportError:pass
        else:raise RuntimeError('A resilience-test port is already in use. No existing process was stopped.')
    log=(OUT/'resilience-process.log').open('w',encoding='utf-8');children=[];checks={}
    def launch(command,cwd):
        p=subprocess.Popen(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT);children.append(p);return p
    def wait(origin,path,process):
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('Isolated service startup failed; inspect the private process log.')
            try:
                if httpx.get(origin+path,timeout=2).status_code==200:return
            except httpx.TransportError:pass
            time.sleep(.25)
        raise RuntimeError('Isolated service startup timed out.')
    def stop(p):
        p.terminate()
        try:p.wait(timeout=15)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    def backend_process():
        p=launch([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8007'],ROOT/'backend');wait(backend,'/api/health',p);return p
    try:
        # Copy assets using the same production launcher used by the local app.
        front=launch(['node','scripts/start-production.mjs'],ROOT/'frontend');wait(base,'/',front)
        checks['not_ready_without_backend']=httpx.get(base+'/api/ready').status_code==503
        with httpx.Client(base_url=base,headers={'Origin':base},timeout=15) as first,httpx.Client(base_url=base,headers={'Origin':base},timeout=15) as second:
            first.post('/api/session',json={'access_code':code}).raise_for_status()
            failure=first.get('/api/companies')
            checks['backend_outage_recovers_cleanly']=failure.status_code==503 and all(value not in failure.text for value in ('127.0.0.1','localhost','8000','8007'))
            back=backend_process()
            checks['ready_after_backend_start']=first.get('/api/ready').status_code==200
            checks['existing_session_survives_outage']=first.get('/api/companies').status_code==200
            second.post('/api/session',json={'access_code':code}).raise_for_status()
            checks['two_active_sessions']=first.get('/api/companies').status_code==second.get('/api/companies').status_code==200
            first.delete('/api/session').raise_for_status()
            checks['logout_is_device_local']=first.get('/api/companies').status_code==401 and second.get('/api/companies').status_code==200
            stop(back)
            checks['readiness_detects_lost_backend']=second.get('/api/ready').status_code==503
            checks['proxy_reports_lost_backend']=second.get('/api/companies').status_code==503
            back=backend_process()
            checks['same_session_recovers_after_restart']=second.get('/api/companies').status_code==200
            second.delete('/api/session').raise_for_status()
        report={'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'actual local production Next.js proxy, two independent HTTP cookie jars and real FastAPI process stop/start; no public HTTPS or physical-device claim','checks':checks,'passed':all(checks.values()),'external_provider_calls':0}
        (OUT/'resilience.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
    finally:
        for process in reversed(children):
            if process.poll() is None:stop(process)
        log.close()


if __name__=='__main__':sys.exit(main())
