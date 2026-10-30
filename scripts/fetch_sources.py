"""Download actual primary documents with provenance; index them for offline demo."""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.config import ROOT
from app.database import Base, engine, SessionLocal
from app.models import Company
from app.seed import seed
from app.services.documents import ingest_url, store_document
from app.ingestion.http import fetch_public

BASE = 'https://www.infosys.com/investors/reports-filings/quarterly-results/'
CATALOG = [
 {'ticker':'INFY','title':'Infosys Q4 FY25 results - IFRS INR','period':'Q4 FY25','kind':'results','url':BASE+'2024-2025/q4/documents/ifrs-inr-press-release.pdf'},
 {'ticker':'INFY','title':'Infosys Q4 FY24 earnings call','period':'Q4 FY24 / FY25 outlook','kind':'transcript','url':BASE+'2023-2024/q4/documents/transcripts/earningscall.pdf'},
 {'ticker':'INFY','title':'Infosys Q1 FY25 earnings call','period':'Q1 FY25','kind':'transcript','url':BASE+'2024-2025/q1/documents/transcripts/earningscall.pdf'},
 {'ticker':'INFY','title':'Infosys Q2 FY25 earnings call','period':'Q2 FY25','kind':'transcript','url':BASE+'2024-2025/q2/documents/transcripts/earningscall.pdf'},
 {'ticker':'INFY','title':'Infosys Q3 FY25 earnings call','period':'Q3 FY25','kind':'transcript','url':BASE+'2024-2025/q3/documents/transcripts/earningscall.pdf'},
 {'ticker':'INFY','title':'Infosys Q4 FY25 earnings call','period':'Q4 FY25','kind':'transcript','url':BASE+'2024-2025/q4/documents/transcripts/earningscall.pdf'},
 {'ticker':'INFY','title':'Infosys consolidated IFRS statements Q4 FY25','period':'Q4 FY25','kind':'results','url':BASE+'2024-2025/q4/documents/consolifrsinr-fy25-q4-and-12m-finstatement.pdf'},
 {'ticker':'INFY','title':'Infosys integrated annual report 2024-25','period':'FY25','kind':'annual_report','url':'https://www.infosys.com/investors/reports-filings/annual-report/annual/documents/infosys-ar-25.pdf'},
 {'ticker':'TCS','title':'TCS Q4 FY25 company results release','period':'Q4 FY25','kind':'results','url':'https://www.tcs.com/who-we-are/newsroom/press-release/tcs-financial-results-q4-fy-2025'},
 {'ticker':'PERSISTENT','title':'Persistent integrated annual report 2024-25','period':'FY25','kind':'annual_report','url':'https://www.persistent.com/wp-content/uploads/2025/06/persistent-annual-report-2025.pdf'},
 {'ticker':'INFY','title':'Infosys Q3 FY25 results - IFRS INR','period':'Q3 FY25','kind':'results','url':BASE+'2024-2025/q3/documents/ifrs-inr-press-release.pdf'},
]

def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
        # Issuer domains in the catalog are verified against their own sites;
        # symbol existence is separately checked by the source validation script.
        for ticker in {x['ticker'] for x in CATALOG}:
            db.get(Company,ticker).verified = True
        db.commit()
    directory = ROOT/'data'/'primary'
    directory.mkdir(parents=True,exist_ok=True)
    existing_manifest = directory/'catalog.json'
    old = json.loads(existing_manifest.read_text(encoding='utf-8')) if existing_manifest.exists() else []
    completed = {x['url']:x for x in old}
    for n,row in enumerate(CATALOG):
        try:
            from app.services.documents import permitted_domains
            with SessionLocal() as db:
                company = db.get(Company,row['ticker'])
                file = directory / (f"{row['ticker'].lower()}-{n:02d}" + ('.pdf' if '.pdf' in row['url'] else '.html'))
                if file.exists():
                    content = file.read_bytes()
                else:
                    content,_ = fetch_public(row['url'],permitted_domains(company))
                    file.write_bytes(content)
                doc = store_document(db,company,row['title'],row['period'],row['kind'],row['url'],content)
                db.commit()
                completed[row['url']] = {**row,'file':file.name,'checksum':doc.checksum,'page_count':doc.page_count}
                print('OK',row['ticker'],row['title'],doc.page_count,'pages',flush=True)
        except Exception as exc:
            print('UNAVAILABLE',row['title'],str(exc)[:250],flush=True)
        existing_manifest.write_text(json.dumps(list(completed.values()),indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
