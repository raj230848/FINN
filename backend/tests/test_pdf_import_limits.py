import hashlib
import json
from pathlib import Path

import httpx
import pymupdf
import pytest
from sqlalchemy import select,func,event

from app import main
from app.config import settings
from app.models import Company,Document,Chunk,ResearchCache
from app.ingestion.http import SourceError
from app.ingestion import http as source
from app.services import documents as module
from app.services.documents import extract_pages,store_document,ingest_url
from app.services.research import research


def pdf_bytes(pages=1,issuer='Infosys Limited',text=None):
    with pymupdf.open() as doc:
        for i in range(pages):
            page=doc.new_page()
            body=text or (issuer+' annual report.\n'+('Revenue and cash flow from operations improved.\n'*8))
            page.insert_text((40,50),body,fontsize=10)
        return doc.tobytes()


@pytest.fixture(scope='module')
def long_pdf():
    with pymupdf.open() as doc:
        for i in range(701):
            page=doc.new_page()
            body='Infosys Limited annual report.\n'+('Revenue and cash flow from operations improved.\n'*5)
            if i==700:body+='Zirconium transition project operating lease commitments.\n'*5
            page.insert_text((40,50),body,fontsize=10)
        return doc.tobytes()


def test_report_over_600_pages_keeps_last_page_and_citations(db,long_pdf):
    doc=store_document(db,db.get(Company,'INFY'),'Complete annual report','FY25','annual_report','https://www.infosys.com/long.pdf',long_pdf)
    db.commit()
    assert doc.page_count==701
    assert db.scalar(select(func.max(Chunk.page)).where(Chunk.document_id==doc.id))==701
    assert db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id==doc.id))==701
    result=research(db,'INFY','What are zirconium transition lease commitments?',False)
    assert result['method']=='extractive'
    assert result['evidence'][0]['page']==701
    assert result['evidence'][0]['url'].endswith('#page=701')


@pytest.mark.parametrize('pages,accepted',[(2,True),(3,False)])
def test_configured_page_boundary(monkeypatch,pages,accepted):
    monkeypatch.setattr(settings,'document_max_pages',2)
    if accepted:assert len(extract_pages(pdf_bytes(pages)))==pages
    else:
        with pytest.raises(SourceError,match='3 pages; the configured limit is 2'):extract_pages(pdf_bytes(pages))


@pytest.mark.parametrize('name,value,message',[
    ('document_max_download_bytes',50,'byte import limit'),
    ('document_max_page_chars',100,'page exceeds'),
    ('document_max_text_chars',400,'character text limit'),
    ('document_max_chunks',1,'passage indexing limit'),
])
def test_limits_reject_without_partial_rows(db,monkeypatch,name,value,message):
    monkeypatch.setattr(settings,name,value)
    with pytest.raises(SourceError,match=message):store_document(db,db.get(Company,'INFY'),'Bounded report','FY25','annual_report','https://www.infosys.com/bounded.pdf',pdf_bytes(2))
    assert not db.scalar(select(Document).where(Document.source_url=='https://www.infosys.com/bounded.pdf'))


def test_extraction_deadline_rejects(monkeypatch):
    ticks=iter([0,91])
    monkeypatch.setattr(module.time,'monotonic',lambda:next(ticks))
    with pytest.raises(SourceError,match='time budget'):extract_pages(pdf_bytes())


@pytest.mark.parametrize('content',[b'',b'%PDF broken',b'PK\x03\x04not a report',b'\xff\x00\x01'*100])
def test_malformed_empty_and_unsupported_content(content):
    with pytest.raises(SourceError):extract_pages(content)


def test_bom_pdf_and_original_page_numbers_with_blank_pages(db):
    with pymupdf.open() as pdf:
        pdf.new_page();page=pdf.new_page();page.insert_text((40,50),'Infosys Limited\n'+('Revenue outlook and business operations improved.\n'*8))
        content=b'\xef\xbb\xbf \n'+pdf.tobytes()
    doc=store_document(db,db.get(Company,'INFY'),'Mixed pages','FY25','annual_report','https://www.infosys.com/mixed.pdf',content)
    payload=main.document_payload(db,doc)
    assert payload['page_count']==2 and payload['indexed_pages']==1 and payload['pages_without_passages']==1
    assert 'OCR was not run' in payload['indexing_note']
    assert db.scalar(select(Chunk.page).where(Chunk.document_id==doc.id))==2


def test_short_fragments_cannot_claim_success(db):
    with pymupdf.open() as pdf:
        for i in range(6):
            page=pdf.new_page();page.insert_text((40,50),'Infosys Limited report short readable fragments.')
        content=pdf.tobytes()
    with pytest.raises(SourceError,match='No indexable text passages'):store_document(db,db.get(Company,'INFY'),'Fragments','FY25','annual_report','https://www.infosys.com/fragments.pdf',content)


def test_duplicate_same_url_and_identical_content_alias_are_idempotent(db):
    content=pdf_bytes();company=db.get(Company,'INFY')
    first=store_document(db,company,'First report','FY25','annual_report','https://www.infosys.com/original.pdf',content);db.commit()
    count=db.scalar(select(func.count()).select_from(Chunk))
    for url in [first.source_url,'https://www.infosys.com/alias.pdf']:
        same=store_document(db,company,'Different supplied label','FY26','annual_report',url,content)
        assert same.id==first.id and same.period=='FY25'
    assert db.scalar(select(func.count()).select_from(Chunk))==count


def test_changed_url_content_updates_metadata_and_replaces_chunks(db):
    company=db.get(Company,'INFY');url='https://www.infosys.com/update.pdf'
    old=store_document(db,company,'Old report','FY24','annual_report',url,pdf_bytes());db.commit();fetched=old.fetched_at
    new=store_document(db,company,'New report','FY25','results',url,pdf_bytes(2))
    assert new.id==old.id and new.title=='New report' and new.period=='FY25' and new.kind=='results'
    assert new.page_count==2 and new.fetched_at>=fetched
    assert db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id==new.id))==2


@pytest.mark.parametrize('bad_content',[b'%PDF broken',pdf_bytes(issuer='Unrelated Issuer Limited')])
def test_bad_replacement_preserves_old_document_and_passages(db,bad_content):
    company=db.get(Company,'INFY');url='https://www.infosys.com/saved.pdf';content=pdf_bytes()
    doc=store_document(db,company,'Saved report','FY25','annual_report',url,content);db.commit()
    before=[c.text for c in db.scalars(select(Chunk).where(Chunk.document_id==doc.id))]
    with pytest.raises(SourceError):store_document(db,company,'Bad replacement','FY26','results',url,bad_content)
    db.expire_all();saved=db.get(Document,doc.id)
    assert saved.title=='Saved report' and saved.checksum==hashlib.sha256(content).hexdigest()
    assert [c.text for c in db.scalars(select(Chunk).where(Chunk.document_id==doc.id))]==before


def test_insert_failure_rolls_back_replacement_savepoint(db,long_pdf):
    company=db.get(Company,'INFY');url='https://www.infosys.com/rollback.pdf';original=pdf_bytes()
    doc=store_document(db,company,'Saved report','FY25','annual_report',url,original);db.commit();doc_id=doc.id
    db.add(ResearchCache(key='rollback-cache',result={'ticker':'INFY','answer':'saved'}));db.commit()
    calls=0
    def fail_second_batch(conn,cursor,statement,parameters,context,executemany):
        nonlocal calls
        if statement.lstrip().upper().startswith('INSERT INTO CHUNKS'):
            calls+=1
            if calls==2:raise RuntimeError('Controlled batch interruption')
    event.listen(db.bind,'before_cursor_execute',fail_second_batch)
    try:
        with pytest.raises(RuntimeError,match='Controlled batch'):store_document(db,company,'Replacement','FY26','annual_report',url,long_pdf)
    finally:event.remove(db.bind,'before_cursor_execute',fail_second_batch)
    db.expire_all();saved=db.get(Document,doc_id)
    assert saved.title=='Saved report' and saved.page_count==1
    assert db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id==doc_id))==1
    assert db.get(ResearchCache,'rollback-cache') is not None


def test_replaced_document_invalidates_stale_citations_for_that_issuer_only(db):
    company=db.get(Company,'INFY');url='https://www.infosys.com/cache-metadata.pdf';original=pdf_bytes()
    doc=store_document(db,company,'Old title','FY24','annual_report',url,original);db.commit()
    old=research(db,'INFY','What is revenue outlook?',False);db.commit()
    assert old['evidence'][0]['title']=='Old title'
    assert research(db,'INFY','What is revenue outlook?',False)['cached']
    db.add(ResearchCache(key='other-company',result={'ticker':'WIPRO','answer':'keep'}));db.commit()
    with pymupdf.open(stream=original,filetype='pdf') as pdf:
        pdf.set_metadata({'title':'Revised metadata, same page text'});replacement=pdf.tobytes()
    store_document(db,company,'New title','FY25','annual_report',url,replacement);db.commit()
    new=research(db,'INFY','What is revenue outlook?',False)
    assert not new['cached'] and new['evidence'][0]['title']=='New title'
    assert new['evidence'][0]['period']=='FY25'
    assert db.get(ResearchCache,'other-company') is not None


def test_live_import_requires_pdf_and_keeps_primary_wrapper_guards(db,monkeypatch):
    company=db.get(Company,'INFY')
    html=b'<html><main>Infosys Limited '+b'access login denied '*100+b'</main></html>'
    monkeypatch.setattr(module,'fetch_public',lambda *a,**k:(html,a[0]))
    with pytest.raises(SourceError,match='instead of a PDF'):ingest_url(db,company,'Not a PDF','FY25','annual_report','https://www.infosys.com/report.pdf')
    calls=[]
    def fetch(url,allowed,**kwargs):
        calls.append((url,allowed,kwargs))
        return (b'<iframe src="/report.pdf"></iframe>','https://www.bseindia.com/viewer') if len(calls)==1 else (pdf_bytes(),url)
    monkeypatch.setattr(module,'fetch_public',fetch)
    doc=ingest_url(db,company,'Wrapped PDF','FY25','annual_report','https://www.bseindia.com/viewer#page=2')
    assert doc.page_count==1 and doc.source_url=='https://www.bseindia.com/viewer'
    assert calls[1][0]=='https://www.bseindia.com/report.pdf' and calls[1][2]['max_bytes']==60_000_000


def test_import_route_busy_failure_release_and_real_page_counts(client,db,monkeypatch,long_pdf):
    body={'ticker':'INFY','title':'Long report','period':'FY25','kind':'annual_report','url':'https://www.infosys.com/long-route.pdf'}
    main.IMPORT_LOCK.acquire()
    try:
        response=client.post('/api/documents',json=body)
        assert response.status_code==409 and response.headers['retry-after']=='3'
    finally:main.IMPORT_LOCK.release()
    def fail(*a,**k):raise SourceError('Controlled PDF failure')
    monkeypatch.setattr(main,'ingest_url',fail)
    assert client.post('/api/documents',json=body).status_code==422
    assert not main.IMPORT_LOCK.locked()
    monkeypatch.setattr(module,'fetch_public',lambda *a,**k:(long_pdf,a[0]))
    monkeypatch.setattr(main,'ingest_url',ingest_url)
    response=client.post('/api/documents',json=body)
    assert response.status_code==200
    assert response.json()['page_count']==701 and response.json()['indexed_pages']==701
    again=client.post('/api/documents',json=body)
    assert again.json()['id']==response.json()['id']
    assert client.get('/api/companies/INFY/documents').json()[0]['indexed_passages']==701
    assert not main.IMPORT_LOCK.locked()


@pytest.mark.parametrize('status',[403,404,429,500])
def test_provider_errors_are_actionable_and_never_indexed(monkeypatch,status):
    monkeypatch.setattr(source,'validate_url',lambda *a:None)
    real=httpx.Client
    monkeypatch.setattr(source.httpx,'Client',lambda **kw:real(transport=httpx.MockTransport(lambda _:httpx.Response(status)),**kw))
    with pytest.raises(SourceError,match=f'HTTP {status}'):source.fetch_public('https://www.infosys.com/report.pdf',{'infosys.com'})


def test_declared_and_streamed_byte_limits_and_timeouts(monkeypatch):
    monkeypatch.setattr(source,'validate_url',lambda *a:None)
    real=httpx.Client
    for headers in ({'content-length':'1000'},{}):
        monkeypatch.setattr(source.httpx,'Client',lambda **kw:real(transport=httpx.MockTransport(lambda _:httpx.Response(200,headers=headers,content=b'12345')),**kw))
        with pytest.raises(SourceError,match='4-byte'):source.fetch_public('https://www.infosys.com/report.pdf',{'infosys.com'},max_bytes=4)
    def timeout(request):raise httpx.ReadTimeout('Controlled timeout')
    monkeypatch.setattr(source.httpx,'Client',lambda **kw:real(transport=httpx.MockTransport(timeout),**kw))
    with pytest.raises(SourceError,match='ReadTimeout'):source.fetch_public('https://www.infosys.com/report.pdf',{'infosys.com'})
