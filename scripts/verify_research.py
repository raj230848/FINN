"""Network smoke test of the generic, previously unseen ticker research path."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.database import SessionLocal
from app.models import Company
from app.ingestion.market import resolve_company
from app.services.documents import discover_documents, ingest_url
from app.services.research import research

def main():
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'known':{},'unseen':{}}
    with SessionLocal() as db:
        for ticker in ['INFY','TCS','PERSISTENT']:
            result=research(db,ticker,'What is the business model and its major services?',False)
            report['known'][ticker]={'method':result['method'],'citations':len(result['evidence']),'sources':[{'title':e['title'],'page':e['page'],'url':e['url']} for e in result['evidence'][:2]]}
        # POLYCAB is not in seed.COMPANIES or the demo source catalog.
        ticker='POLYCAB'
        try:
            resolved=resolve_company(ticker)
            company=db.get(Company,ticker)
            if not company:
                company=Company(**resolved,watched=False)
                db.add(company)
            db.commit()
            candidates=discover_documents(company)
            report['unseen']={'ticker':ticker,'resolved':True,'primary_candidates':len(candidates),'website':company.website}
            for candidate in sorted(candidates,key=lambda c:c['kind']!='transcript')[:3]:
                try:
                    doc=ingest_url(db,company,candidate['title'],candidate['period'],candidate['kind'],candidate['url'])
                    db.commit()
                    report['unseen']['imported']={'title':doc.title,'pages':doc.page_count,'source_url':doc.source_url}
                    break
                except Exception as exc:
                    db.rollback()
                    report['unseen'].setdefault('import_errors',[]).append(str(exc))
            result=research(db,ticker,'What does the business do and what are its risks?',False)
            report['unseen']['method']=result['method']
            report['unseen']['citations']=len(result['evidence'])
        except Exception as exc:
            db.rollback()
            report['unseen'].update(ticker=ticker,error=str(exc))
        db.commit()
    out=Path(__file__).resolve().parents[1]/'docs/research-verification.json'
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    main()
