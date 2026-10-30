"""Explicit opt-in network smoke test. Writes an honest availability report."""
import csv
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.main import initialize
from app.database import SessionLocal
from app.models import Company, SyncRun
from app.seed import COMPANIES
from app.ingestion.http import fetch_public
from app.services.sync import run_sync
from sqlalchemy import select

def main():
    initialize()
    report = {'checked_at':datetime.now(timezone.utc).isoformat(),'sources':{},'symbols':{}}
    try:
        content,_ = fetch_public('https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv',{'nsearchives.nseindia.com'})
        listing = {row['SYMBOL']:row for row in csv.DictReader(io.StringIO(content.decode('utf-8-sig')))}
        with SessionLocal() as db:
            for ticker,*_ in COMPANIES:
                report['symbols'][ticker] = {'verified':ticker in listing,'exchange_name':listing.get(ticker,{}).get('NAME OF COMPANY')}
                if ticker in listing:
                    db.get(Company,ticker).verified = True
            db.commit()
        report['sources']['nse_listing'] = {'ok':True,'listed_symbols':len(listing)}
    except Exception as exc:
        report['sources']['nse_listing'] = {'ok':False,'error':str(exc)}
    print('Checking all portfolio price feeds and NSE announcements…',flush=True)
    run_sync()
    with SessionLocal() as db:
        run = db.scalar(select(SyncRun).order_by(SyncRun.id.desc()).limit(1))
        report['sources']['sync'] = run.result
    out = Path(__file__).resolve().parents[1]/'docs'/'source-verification.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    main()
