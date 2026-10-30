import socket
import pymupdf
import pytest
from app.config import settings
from app.ingestion.http import SourceError, validate_url
from app.models import Company, Document
from app.schemas import AnalysisOut
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
    monkeypatch.setattr(settings,'openai_api_key','test-key')
    monkeypatch.setattr(module,'structured_call',lambda *args: AnalysisOut(answer='Invented claim [999999]',evidence_ids=[999999],limitations=[]))
    result=module.research(db,'INFY','What is revenue outlook?',True)
    assert result['method']=='extractive'
    assert any('validation failed' in l for l in result['limitations'])

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
