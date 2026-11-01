import hashlib
import re
from urllib.parse import urljoin, urlparse
import pymupdf as fitz
from bs4 import BeautifulSoup
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from ..config import ROOT
from ..models import Chunk, Company, Document
from ..ingestion.http import ARCHIVES, SourceError, domain, fetch_public

def permitted_domains(company: Company) -> set[str]:
    return ARCHIVES | ({domain(company.website)} if company.website and company.verified else set())

def extract_pages(content: bytes) -> list[str]:
    if content.startswith(b'%PDF'):
        try:
            with fitz.open(stream=content, filetype='pdf') as doc:
                if doc.is_encrypted:
                    raise SourceError('The PDF is encrypted. Provide an accessible primary document.')
                if doc.page_count > 600:
                    raise SourceError('PDF exceeds the 600 page prototype limit.')
                pages = [page.get_text(sort=True) for page in doc]
        except SourceError:
            raise
        except Exception as exc:
            raise SourceError('Malformed or incomplete PDF.') from exc
    else:
        soup = BeautifulSoup(content, 'html.parser')
        for tag in soup(['script','style','nav','header','footer']):
            tag.decompose()
        main = soup.find('main') or soup
        pages = [main.get_text(' ', strip=True)]
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
    if existing and existing.checksum == checksum:
        return existing
    pages = extract_pages(content)
    # An archive domain alone is insufficient: check that the issuer is named.
    identity_text = ' '.join(pages[:5]).lower()
    normalize=lambda value:re.sub(r'[^a-z0-9]','',value.lower())
    issuer_name=normalize(re.sub(r'\b(?:limited|ltd|corporation)\b','',company.name.lower()))
    ticker=normalize(company.ticker)
    ticker_token=re.search(r'(?<![a-z0-9])'+re.escape(company.ticker.lower())+r'(?![a-z0-9])',identity_text)
    if not (ticker_token or (len(issuer_name)>=4 and issuer_name in normalize(identity_text)) or (len(ticker)>=5 and ticker in normalize(identity_text))):
        raise SourceError('The document does not identify the selected issuer in its first five pages. It was not indexed.')
    if existing:
        db.execute(delete(Chunk).where(Chunk.document_id == existing.id))
        doc = existing
        doc.checksum, doc.page_count = checksum, len(pages)
    else:
        doc = Document(ticker=company.ticker, title=title, period=period, kind=kind, source_url=url, checksum=checksum, page_count=len(pages))
        db.add(doc)
        db.flush()
    for page_num, text in enumerate(pages, 1):
        db.add_all([Chunk(document_id=doc.id, page=page_num, text=part) for part in chunk_page(text)])
    db.flush()
    return doc

def ingest_url(db: Session, company: Company, title: str, period: str, kind: str, url: str) -> Document:
    # A viewer fragment does not identify a different source document.
    try:url=urlparse(url.strip())._replace(fragment='').geturl()
    except ValueError:raise SourceError('Malformed primary-document URL.') from None
    allowed = permitted_domains(company)
    content, final_url = fetch_public(url, allowed)
    # BSE's published AnnPdfOpen links sometimes return a viewer rather than
    # an HTTP redirect. Follow only its embedded public primary document.
    if not content.startswith(b'%PDF') and domain(final_url)=='bseindia.com':
        soup = BeautifulSoup(content,'html.parser')
        embedded = soup.select_one('iframe[src], embed[src], object[data]')
        if embedded:
            target = embedded.get('src') or embedded.get('data')
            content, _ = fetch_public(urljoin(final_url,target),allowed)
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
