import json
import re
import pymupdf
from app.config import ROOT
from app.models import Financial
from app.services.calculations import percent_change

def test_quarter_comparisons_and_missing_ebitda(client):
    result=client.get('/api/companies/INFY/financials').json()
    metrics={r['metric']:r for r in result['rows']}
    assert metrics['revenue']['current']==40925
    assert metrics['revenue']['previous']==41764
    assert metrics['revenue']['last_year']==37923
    assert metrics['revenue']['qoq']==-2.01
    assert metrics['revenue']['yoy']==7.92
    assert metrics['pat']['current']==7033
    assert metrics['pat']['yoy']==-11.75
    assert metrics['ebitda']['current'] is None
    assert metrics['ebitda']['qoq'] is None
    assert all(s['source_url'].startswith('https://www.infosys.com/') for s in result['sources'])
    assert client.get('/api/companies/CERA/financials').json()['rows']==[]

def test_financials_do_not_compare_different_accounting_basis(client,db):
    from sqlalchemy import select
    db.scalar(select(Financial).where(Financial.period=='2025-Q3')).basis='Standalone'
    db.commit()
    result=client.get('/api/companies/INFY/financials').json()
    assert result['rows'][0]['previous'] is None
    assert result['rows'][0]['qoq'] is None

def test_guidance_revisions_compare_same_period_and_currency(client):
    data=client.get('/api/companies/INFY/guidance').json()
    assert [r['status'] for r in data['items']]==['exceeded','exceeded','achieved','missed']
    assert data['items'][-1]['deviation_pp']==-0.3
    assert len({r['target_period'] for r in data['items']})==1
    assert all(r['guidance_page']>0 and r['actual_page']>0 for r in data['items'])

def test_reviewed_values_exist_in_actual_pdf_rows():
    # Real local primary documents, not an implementation-shaped mocked table.
    sources={row['url']:row for row in json.loads((ROOT/'data/primary/catalog.json').read_text(encoding='utf-8'))}
    manifest=json.loads((ROOT/'data/primary/verified.json').read_text(encoding='utf-8'))
    for row in manifest['financials']:
        if row['ticker']!='INFY': continue
        source=sources[row['source_url']]
        with pymupdf.open(ROOT/'data/primary'/source['file']) as doc:
            text=doc[row['page']-1].get_text(sort=True)
        assert '(in' in text.lower() and 'crore' in text.lower()
        for metric,term in [('revenue','Revenues'),('pbt','Profit before income taxes'),('pat','Net profit (after minority interest)')]:
            line=next(line for line in text.splitlines() if term in line)
            numbers=[int(n.replace(',','')) for n in re.findall(r'\b\d[\d,]*\b',line)]
            col=1 if row['period']=='2024-Q4' else 0
            assert numbers[col]==row['metrics'][metric]

def test_second_company_uses_reported_tcs_usd_tables(client):
    result=client.get('/api/companies/TCS/financials').json()
    assert result['currency']=='USD million'
    assert 'Consolidated IFRS' in result['basis']
    rows={r['metric']:r for r in result['rows']}
    assert rows['revenue']['current']==7465 and rows['revenue']['previous']==7539 and rows['revenue']['last_year']==7363
    assert rows['pbt']['current']==1900 and rows['pat']['current']==1418
    assert rows['revenue']['qoq']==-0.98 and rows['revenue']['yoy']==1.39
    assert rows['ebitda']['current'] is None
    manifest=json.loads((ROOT/'data/primary/verified.json').read_text())
    tables=json.loads((ROOT/'data/primary/reviewed-tcs-tables.json').read_text())['tables']
    for row in [r for r in manifest['financials'] if r['ticker']=='TCS']:
        source=next(t for t in tables if t['source_url']==row['source_url'])
        column=source['period_columns'].index(row['period'])
        for metric,label in [('revenue','Revenue'),('pbt','Income before income taxes'),('pat','Net income')]:
            assert row['metrics'][metric]==source['rows'][label][column]
    # Q4 and prior-year facts are also checked directly against the original issuer HTML.
    from bs4 import BeautifulSoup
    html=BeautifulSoup((ROOT/'data/primary/tcs-08.html').read_bytes(),'html.parser')
    table=next(t for t in html.find_all('table') if 'Three-month periods ended March' in t.get_text(' ',strip=True))
    assert all(str(v) in table.get_text(' ',strip=True).replace(',','') for v in [7465,7363,1900,1418])
