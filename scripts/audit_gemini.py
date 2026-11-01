"""Real Gemini checks at every integration call site, in a disposable DB."""
import argparse
import json
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from sqlalchemy import select

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.config import settings
from app.database import SessionLocal
from app.models import Company,Announcement,utcnow
from app.ai.client import structured_call
from app.services import sync,research
from app.schemas import GroundingReviewOut,ClassificationOut

parser=argparse.ArgumentParser();parser.add_argument('--out',default=str(ROOT/'artifacts/comprehensive-audit/gemini.json'));args=parser.parse_args()
if 'comprehensive-audit' not in settings.database_url:raise SystemExit('Use the disposable comprehensive-audit database, never the normal runtime DB.')
report={'checked_at':datetime.now(timezone.utc).isoformat(),'model':settings.gemini_model,'key_configured':bool(settings.gemini_api_key),'calls':[],'scenarios':[]}
def traced(system,payload,schema,**kwargs):
    start=time.monotonic();record={'schema':schema.__name__,'model':settings.gemini_model}
    try:
        result=structured_call(system,payload,schema,**kwargs);record['status']='validated_live_response'
        if isinstance(result,GroundingReviewOut):record.update(supported=result.supported,unsupported_claims=len(result.unsupported_claims))
        if isinstance(result,ClassificationOut):record.update(category=result.category,confidence=result.confidence)
        return result
    except Exception as error:record['status']='failed';record['error_type']=type(error).__name__;raise
    finally:record['elapsed_ms']=round((time.monotonic()-start)*1000);report['calls'].append(record)
sync.structured_call=traced;research.structured_call=traced
with SessionLocal() as db:
    question='What FY25 operating margin guidance did management provide?'
    answer=research.research(db,'INFY',question,True,refresh=True);db.commit()
    report['scenarios'].append({'name':'fresh primary-source synthesis and support review','question':question,'method':answer['method'],'cached':answer['cached'],'answer':answer['answer'],'sources':[{'id':e['id'],'page':e['page'],'url':e['url']} for e in answer['evidence']]})
    count=len(report['calls']);cached=research.research(db,'INFY',question,True)
    report['scenarios'].append({'name':'research cache','cached':cached['cached'],'provider_calls':len(report['calls'])-count})
    count=len(report['calls']);missing=research.research(db,'CERA','What is revenue?',True)
    report['scenarios'].append({'name':'no evidence','method':missing['method'],'provider_calls':len(report['calls'])-count})
    db.rollback()
    for name,description in [('evidence-rich ambiguous filing','The board approved a material restructuring: the entire ownership of the network-services subsidiary will be transferred to an external buyer under signed terms.'),('insufficient filing details','A material matter was discussed. No further details have been disclosed.')]:
        fixture_db=SessionLocal()
        try:
            if not fixture_db.get(Company,'AUDITLLM'):fixture_db.add(Company(ticker='AUDITLLM',name='Synthetic integration fixture',watched=False));fixture_db.flush()
            row={'ticker':'AUDITLLM','title':'Outcome of Board Meeting — controlled synthetic test','text':description,'published_at':utcnow(),'source_url':None}
            before=len(report['calls']);inserted=sync.save_announcements(fixture_db,[row]);fixture_db.flush()
            filing=fixture_db.scalar(select(Announcement).where(Announcement.ticker=='AUDITLLM'))
            outcome={'name':name,'fixture':'synthetic; not an actual issuer event','inserted':inserted,'category':filing.category,'priority':filing.priority,'needs_review':filing.needs_review,'analysis_method':filing.analysis_method,'summary':filing.summary,'provider_calls':len(report['calls'])-before}
            before=len(report['calls']);duplicate=sync.save_announcements(fixture_db,[row])
            outcome['repeat_insertions']=duplicate;outcome['repeat_provider_calls']=len(report['calls'])-before;report['scenarios'].append(outcome)
        finally:fixture_db.rollback();fixture_db.close()
    db.rollback()
schemas={r['schema'] for r in report['calls'] if r['status']=='validated_live_response'}
report['summary']={'all_three_call_sites_exercised':{'SynthesisOut','GroundingReviewOut','ClassificationOut'}<=schemas,'live_provider_calls':len(report['calls']),'accepted_research':report['scenarios'][0]['method']=='grounded_ai','limitations':'Synthetic classifier fixtures verify integration behavior, not real-world classification accuracy or semantic certainty.'}
encoded=json.dumps(report,indent=2)+'\n';assert not settings.gemini_api_key or settings.gemini_api_key not in encoded
out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(encoded,encoding='utf-8');print(json.dumps(report['summary'],indent=2))
