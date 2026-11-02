import hashlib
import re
import time
from threading import Lock
from urllib.parse import urljoin, urlparse
import pymupdf as fitz
from bs4 import BeautifulSoup
from sqlalchemy import select, delete, insert
from sqlalchemy.orm import Session
from ..config import ROOT,settings
from ..models import Chunk, Company, Document,utcnow
from ..ingestion.http import ARCHIVES, SourceError, domain, fetch_public

IMPORT_LOCK=Lock()


def is_pdf(content: bytes) -> bool:
    # Some genuine issuer PDFs contain whitespace/BOM bytes before the header.
    return b'%PDF' in content[:1024]

def permitted_domains(company: Company) -> set[str]:
    return ARCHIVES | ({domain(company.website)} if company.website and company.verified else set())

def extract_pages(content: bytes) -> list[str]:
    if not content or len(content)>settings.document_max_download_bytes:
        raise SourceError(f'Document is empty or exceeds the {settings.document_max_download_bytes:,}-byte import limit.')
    started=time.monotonic()
    total=0
    def checked(text):
        nonlocal total
        if time.monotonic()-started>settings.document_extract_timeout_seconds:
            raise SourceError('Document extraction exceeded its time budget. Import a smaller issuer report or split the original PDF at the source.')
        if len(text)>settings.document_max_page_chars:
            raise SourceError(f'A page exceeds the {settings.document_max_page_chars:,}-character extraction limit. The document was not partially indexed.')
        total+=len(text)
        if total>settings.document_max_text_chars:
            raise SourceError(f'Document exceeds the {settings.document_max_text_chars:,}-character text limit. The document was not partially indexed.')
        return text
    if is_pdf(content):
        try:
            with fitz.open(stream=content, filetype='pdf') as doc:
                if doc.is_encrypted:
                    raise SourceError('The PDF is encrypted. Provide an accessible primary document.')
                if doc.page_count > settings.document_max_pages:
                    raise SourceError(f'PDF has {doc.page_count:,} pages; the configured limit is {settings.document_max_pages:,}. Import a smaller issuer report or ask the desk administrator to review the limit.')
                pages = [checked(page.get_text(sort=True)) for page in doc]
        except SourceError:
            raise
        except Exception as exc:
            raise SourceError('Malformed or incomplete PDF.') from exc
    else:
        if not re.search(rb'<(?:!doctype\s+html|html|main|body|article|section|div|p)\b',content[:2048],re.I):
            raise SourceError('Unsupported document format. Provide an accessible PDF from the issuer or exchange.')
        soup = BeautifulSoup(content, 'html.parser')
        for tag in soup(['script','style','nav','header','footer']):
            tag.decompose()
        main = soup.find('main') or soup
        pages = [checked(main.get_text(' ', strip=True))]
    if sum(len(x.strip()) for x in pages) < 200:
        raise SourceError('No readable text found. Scanned PDFs need OCR, which this prototype does not infer.')
    return pages

def chunk_page(text: str, size: int = 1300, overlap: int = 180) -> list[str]:
    text = re.sub(r'[ \t]+', ' ', text).strip()
    return [text[i:i+size] for i in range(0, len(text), size-overlap) if len(text[i:i+size].strip()) >= 80]

def store_document(db: Session, company: Company, title: str, period: str, kind: str, url: str, content: bytes) -> Document:
    checksum = hashlib.sha256(content).hexdigest()
    existing = db.scalar(select(Document).where(Document.source_url == url))
    if existing and existing.ticker != company.ticker:
        raise SourceError('That URL is already associated with a different issuer.')
    if existing and existing.checksum == checksum and db.scalar(select(Chunk.id).where(Chunk.document_id==existing.id).limit(1)):
        return existing
    same_content=db.scalar(select(Document).where(Document.ticker==company.ticker,Document.checksum==checksum))
    if not existing and same_content and db.scalar(select(Chunk.id).where(Chunk.document_id==same_content.id).limit(1)):
        return same_content
    pages = extract_pages(content)
    # An archive domain alone is insufficient: check that the issuer is named.
    identity_text = ' '.join(pages[:5]).lower()
    normalize=lambda value:re.sub(r'[^a-z0-9]','',value.lower())
    issuer_name=normalize(re.sub(r'\b(?:limited|ltd|corporation)\b','',company.name.lower()))
    ticker=normalize(company.ticker)
    ticker_token=re.search(r'(?<![a-z0-9])'+re.escape(company.ticker.lower())+r'(?![a-z0-9])',identity_text)
    if not (ticker_token or (len(issuer_name)>=4 and issuer_name in normalize(identity_text)) or (len(ticker)>=5 and ticker in normalize(identity_text))):
        raise SourceError('The document does not identify the selected issuer in its first five pages. It was not indexed.')
    chunks=[]
    for page_num, text in enumerate(pages, 1):
        for part in chunk_page(text):
            chunks.append({'page':page_num,'text':part})
            if len(chunks)>settings.document_max_chunks:
                raise SourceError(f'Document exceeds the {settings.document_max_chunks:,}-passage indexing limit. The previous library was retained.')
    if not chunks:
        raise SourceError('No indexable text passages were found. Short fragments or scanned pages cannot support sourced research; use a text-readable PDF.')
    # Validation precedes mutation; a failed batch restores the previous library.
    with db.begin_nested():
        if existing:
            db.execute(delete(Chunk).where(Chunk.document_id == existing.id))
            doc=existing
            doc.title,doc.period,doc.kind=title,period,kind
            doc.checksum,doc.page_count,doc.fetched_at=checksum,len(pages),utcnow()
        else:
            doc=Document(ticker=company.ticker,title=title,period=period,kind=kind,source_url=url,checksum=checksum,page_count=len(pages))
            db.add(doc);db.flush()
        for offset in range(0,len(chunks),500):
            db.execute(insert(Chunk),[{'document_id':doc.id,**row} for row in chunks[offset:offset+500]])
        db.flush()
    return doc

def ingest_url(db: Session, company: Company, title: str, period: str, kind: str, url: str) -> Document:
    # A viewer fragment does not identify a different source document.
    try:url=urlparse(url.strip())._replace(fragment='').geturl()
    except ValueError:raise SourceError('Malformed primary-document URL.') from None
    allowed = permitted_domains(company)
    started=time.monotonic()
    content, final_url = fetch_public(url, allowed,max_bytes=settings.document_max_download_bytes,timeout_seconds=60)
    # BSE's published AnnPdfOpen links sometimes return a viewer rather than
    # an HTTP redirect. Follow only its embedded public primary document.
    if not is_pdf(content) and domain(final_url)=='bseindia.com':
        soup = BeautifulSoup(content,'html.parser')
        embedded = soup.select_one('iframe[src], embed[src], object[data]')
        if embedded:
            target = embedded.get('src') or embedded.get('data')
            remaining=60-(time.monotonic()-started)
            if remaining<=0:raise SourceError('Source download exceeded its time budget. Please retry the primary document.')
            content, _ = fetch_public(urljoin(final_url,target),allowed,max_bytes=settings.document_max_download_bytes,timeout_seconds=remaining)
    if not is_pdf(content):
        raise SourceError('The source returned a web page or unsupported file instead of a PDF. Open the primary link and use the direct PDF URL; access/login pages are not indexed.')
    return store_document(db, company, title, period, kind, url, content)

def discover_documents(company: Company) -> list[dict]:
    # Screener is used only to find links. Its ratios, commentary and financial
    # tables never enter the primary-source research index.
    url = f'https://www.screener.in/company/{company.ticker}/consolidated/'
    content, _ = fetch_public(url, {'screener.in'}, max_bytes=3_000_000)
    soup = BeautifulSoup(content, 'html.parser')
    candidates = []
    for section_id, kind in [('annual-reports','annual_report'), ('concalls','transcript')]:
        section = soup.find(id=section_id) or soup.select_one(f'#documents .{section_id}')
        if not section:
            continue
        group = []
        for a in section.select('a[href]'):
            href = urljoin(url, a['href'])
            host = urlparse(href).hostname or ''
            text = a.get_text(' ',strip=True)
            if kind=='transcript' and 'transcript' not in text.lower():
                continue
            pdf_link = urlparse(href).path.lower().endswith('.pdf') or (host=='www.bseindia.com' and 'annpdfopen.aspx' in href.lower() and '.pdf' in urlparse(href).query.lower())
            if pdf_link and any(host == d or host.endswith('.'+d) for d in permitted_domains(company)):
                parent = a.find_parent('li')
                date_node = parent.find('div') if parent and kind=='transcript' else None
                period = date_node.get_text(' ',strip=True)[:80] if date_node else text[:80]
                group.append({'url':href,'title':f'{company.name} — {text} ({period})' if kind=='transcript' else f'{company.name} — {text}','period':period or 'Period requires review','kind':kind})
        candidates.extend(list({x['url']:x for x in group}.values())[:3])
    return list({x['url']:x for x in candidates}.values())[:6]
