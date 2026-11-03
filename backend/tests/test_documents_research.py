import socket
import pymupdf
import pytest
from app.config import settings
from app.ingestion.http import SourceError, validate_url
from app.models import Company, Document, ResearchCache
from sqlalchemy import func, select
from app.schemas import AnalysisOut, SynthesisOut, SynthesisClaim
from app.services.documents import extract_pages, store_document
from app.services.research import research

def sample_pdf():
    doc=pymupdf.open()
    page=doc.new_page()
    page.insert_text((50,70),'Infosys Limited annual financial review.\n'+('Revenue outlook and cash flow from operations improved.\n' * 12),fontsize=10)
    return doc.tobytes()

def test_malformed_empty_and_scanned_documents():
    with pytest.raises(SourceError): extract_pages(b'%PDF broken truncated file')
    with pytest.raises(SourceError): extract_pages(b'<html>No data</html>')
    doc=pymupdf.open();doc.new_page()
    with pytest.raises(SourceError): extract_pages(doc.tobytes())

def test_primary_sources_page_citations_cache_and_no_outside_knowledge(db):
    company=db.get(Company,'INFY')
    doc=store_document(db,company,'Test primary financial report','FY25','annual_report','https://www.infosys.com/test.pdf',sample_pdf())
    db.commit()
    same=store_document(db,company,'Test primary financial report','FY25','annual_report',doc.source_url,sample_pdf())
    assert same.id==doc.id
    result=research(db,'INFY','What is revenue outlook?',False)
    assert result['method']=='extractive'
    assert result['evidence'][0]['page']==1
    assert result['evidence'][0]['url']=='https://www.infosys.com/test.pdf#page=1'
    assert result['evidence'][0]['document_id']==doc.id
    assert research(db,'INFY','What is revenue outlook?',False)['cached'] is True
    assert research(db,'WIPRO','What is revenue outlook?',False)['method']=='insufficient_evidence'

def test_model_fabricated_citation_rejected(db,monkeypatch):
    from app.services import research as module
    store_document(db,db.get(Company,'INFY'),'Test financial report','FY25','results','https://www.infosys.com/test.pdf',sample_pdf())
    monkeypatch.setattr(settings,'gemini_api_key','test-key')
    monkeypatch.setattr(module,'structured_call',lambda *args: SynthesisOut(claims=[SynthesisClaim(text='Invented financial claim.',evidence_ids=[999999])]))
    result=module.research(db,'INFY','What is revenue outlook?',True)
    assert result['method']=='extractive'
    assert any('validation failed' in l for l in result['limitations'])

def test_hosted_guest_cannot_use_gemini_or_write_research_cache(client, db, monkeypatch):
    from app.services import research as module
    store_document(db, db.get(Company, 'INFY'), 'Issuer report', 'FY25', 'annual_report',
                   'https://www.infosys.com/test.pdf', sample_pdf())
    db.commit()
    monkeypatch.setattr(settings, 'public_deployment', True)
    monkeypatch.setattr(settings, 'gemini_api_key', 'synthetic-test-key')
    monkeypatch.setattr(module, 'structured_call', lambda *args, **kwargs: pytest.fail('Guest called Gemini'))
    response = client.post('/api/research', headers={'X-Finn-Guest': '1'},
                           json={'ticker': 'INFY', 'question': 'What is revenue outlook?', 'use_ai': True, 'refresh': True})
    assert response.status_code == 200
    assert response.json()['method'] == 'extractive'
    assert response.json()['evidence']
    assert db.scalar(select(func.count()).select_from(ResearchCache)) == 0

def test_business_overview_answers_from_the_report_without_a_model(db):
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((50, 70), """K.P.R. Mill Limited
Details of business activities (accounting for 90% of the Turnover):
Description of Main Activity Description of Business Activity % of Turnover of the entity
1 Manufacturing Yarn 42.33
2 Manufacturing Fabric 8.89
3 Manufacturing Garment 42.62
Products/Services sold by the entity
The Group has classified its operations primarily into three reportable segments viz.,
Textile, Sugar and Others based on the management approach.""", fontsize=10)
    document = store_document(db, db.get(Company, 'KPRMILL'), 'Issuer report', 'FY26', 'annual_report',
                              'https://kprmilllimited.com/report.pdf', pdf.tobytes())
    result = research(db, 'KPRMILL', 'What does the company do?', use_ai=True)
    citation = f'[{result["evidence"][0]["id"]}]'
    assert result['method'] == 'extractive'
    assert f'manufacturing yarn, fabric and garment products {citation}' in result['answer']
    assert f'Textile, Sugar and Others as its operating segments {citation}' in result['answer']
    assert result['evidence'][0]['document_id'] == document.id

def test_primary_url_guards(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[(2,1,6,'',('127.0.0.1',443))])
    with pytest.raises(SourceError):validate_url('https://www.infosys.com/report.pdf',{'infosys.com'})
    for url in ['http://www.infosys.com/a.pdf','https://localhost/a.pdf','https://www.infosys.com.evil.com/a.pdf','https://user:pass@www.infosys.com/a.pdf','https://www.infosys.com:8443/a.pdf']:
        with pytest.raises(SourceError):validate_url(url,{'infosys.com'})

def test_discovery_actual_directory_classes_and_transcript_dates(db,monkeypatch):
    from app.services import documents
    html=b'''<section id="documents"><div class="documents annual-reports"><h3>Annual reports</h3><a href="https://www.bseindia.com/a.pdf">Annual Report 2025</a></div><div class="documents concalls"><ul><li><div>Oct 2026</div><a href="https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=test.pdf">Transcript</a><a href="https://www.bseindia.com/presentation.pdf">PPT</a><a href="https://news.example.com/research.pdf">Transcript</a></li></ul></div><div class="credit-ratings"><a href="https://www.bseindia.com/rating.pdf">Rating</a></div></section>'''
    monkeypatch.setattr(documents,'fetch_public',lambda *args,**kw:(html,'https://www.screener.in/company/INFY/consolidated/'))
    result=documents.discover_documents(db.get(Company,'INFY'))
    assert len(result)==2
    assert result[1]['period']=='Oct 2026'
    assert result[1]['kind']=='transcript'
    assert all('presentation' not in r['url'] and 'news.example' not in r['url'] for r in result)
