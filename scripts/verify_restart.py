"""Real two-process SQLite durability check; uses its own disposable database.

No Gemini/source/push calls. Existing production databases are never targeted.
"""
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone

import httpx

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/verification-gaps'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    database=OUT/('restart-'+secrets.token_hex(4)+'.db')
    token=secrets.token_urlsafe(32)
    env={**os.environ,'DATABASE_URL':'sqlite:///'+database.as_posix(),'FINN_API_TOKEN':token,'PUBLIC_DEPLOYMENT':'true','ENABLE_SCHEDULER':'false','GEMINI_API_KEY':'','VAPID_PRIVATE_KEY':'','VAPID_PUBLIC_KEY':'','VAPID_SUBJECT':''}
    base='http://127.0.0.1:8005'
    with httpx.Client(timeout=2) as probe:
        try:probe.get(base+'/api/health')
        except httpx.TransportError:pass
        else:raise RuntimeError('Port 8005 is in use; no existing process was stopped.')
    log=(OUT/'restart-process.log').open('w',encoding='utf-8')
    def launch():
        process=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8005'],cwd=ROOT/'backend',env=env,stdout=log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if process.poll() is not None:raise RuntimeError('QA backend startup failed; inspect private restart log.')
            try:
                if httpx.get(base+'/api/health',timeout=2).status_code==200:return process
            except httpx.TransportError:pass
            time.sleep(.25)
        process.terminate();process.wait(timeout=15)
        raise RuntimeError('QA startup timed out.')
    def stop(process):
        process.terminate()
        try:process.wait(timeout=15)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    checks={};process=None
    try:
        process=launch()
        with httpx.Client(base_url=base,headers={'Authorization':'Bearer '+token},timeout=10) as client:
            pref=client.get('/api/preferences').json();pref.pop('available_categories',None);pref['price_threshold']=6.5
            client.put('/api/preferences',json=pref).raise_for_status()
            client.patch('/api/companies/INFY',json={'watched':False}).raise_for_status()
            client.post('/api/notifications/read-all?mode=demo').raise_for_status()
        with sqlite3.connect(database) as db:
            before={table:db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ('companies','documents','chunks','signal_events')}
            db.execute('INSERT INTO sync_runs (started_at,completed_at,result) VALUES (?,?,?)',('2026-11-01 10:00:00',None,json.dumps({'status':'running','prices':{'INFY':{'ok':True}}})))
            db.execute('INSERT INTO sync_runs (started_at,completed_at,result) VALUES (?,?,?)',('2026-11-01 09:00:00','2026-11-01 09:01:00',json.dumps({'status':'complete'})))
        stop(process);process=None
        process=launch()
        with httpx.Client(base_url=base,headers={'Authorization':'Bearer '+token},timeout=10) as client:
            checks['preference_retained']=client.get('/api/preferences').json()['price_threshold']==6.5
            checks['watchlist_retained']=not next(c for c in client.get('/api/companies').json() if c['ticker']=='INFY')['watched']
            checks['read_state_retained']=client.get('/api/notifications?mode=demo').json()['unread_count']==0
        with sqlite3.connect(database) as db:
            after={table:db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in before}
            checks['documents_and_chunks_retained']=before==after
            rows=[(json.loads(row[0]),row[1]) for row in db.execute('SELECT result,completed_at FROM sync_runs ORDER BY id')]
            checks['partial_refresh_marked_interrupted']=rows[0][0]['status']=='interrupted' and rows[0][0]['prices']['INFY']['ok'] and bool(rows[0][1])
            checks['completed_sync_retained']=rows[1][0]['status']=='complete' and bool(rows[1][1])
            checks['sqlite_wal_enabled']=db.execute('PRAGMA journal_mode').fetchone()[0]=='wal'
        report={'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'actual local process stop/start; isolated SQLite database; not a host-disk acceptance test','checks':checks,'row_counts_before':before,'row_counts_after':after,'passed':all(checks.values()),'external_provider_calls':0}
        (OUT/'restart.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,indent=2))
        return 0 if report['passed'] else 1
    finally:
        if process and process.poll() is None:stop(process)
        log.close()


if __name__=='__main__':sys.exit(main())
