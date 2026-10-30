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
        source=sources[row['source_url']]
        with pymupdf.open(ROOT/'data/primary'/source['file']) as doc:
            text=doc[row['page']-1].get_text(sort=True)
        assert '(in' in text.lower() and 'crore' in text.lower()
        for metric,term in [('revenue','Revenues'),('pbt','Profit before income taxes'),('pat','Net profit (after minority interest)')]:
            line=next(line for line in text.splitlines() if term in line)
            numbers=[int(n.replace(',','')) for n in re.findall(r'\b\d[\d,]*\b',line)]
            col=1 if row['period']=='2024-Q4' else 0
            assert numbers[col]==row['metrics'][metric]
