from datetime import datetime, timedelta
from sqlalchemy import select, func
import pytest
from app.models import Announcement
from app.services.materiality import classify, fingerprint
from app.services.sync import save_announcements

@pytest.mark.parametrize('title,category,priority',[
    ('CFO resignation effective immediately','management_change','high'),
    ('Acquisition of subsidiary','M&A','high'),
    ('Quarterly financial results','results','high'),
    ('Credit rating reaffirmed','credit_rating','medium'),
    ('Dividend declared','dividend','medium'),
    ('Compliance certificate for transfer facility','unclassified','low'),
    ('Board meeting to consider financial results','results','low'),
    ('Earnings call transcript','earnings_call','medium'),
    ('New plant capacity expansion','capex','medium'),
    ('Copy of newspaper publication of dividend record date','dividend','low'),
])
def test_classification_and_explanation(title,category,priority):
    result = classify(title)
    assert result['category']==category
    assert result['priority']==priority
    assert result['factors'] and result['why_matters']

def test_dedup_different_time_attachment_and_punctuation(db):
    day = datetime(2026,10,30,4)
    a = {'ticker':'INFY','title':'Financial Results!','published_at':day,'source_url':'https://nsearchives.nseindia.com/a.pdf','text':''}
    b = {**a,'title':'Financial results','published_at':day+timedelta(hours=1),'source_url':'https://nsearchives.nseindia.com/b.pdf'}
    assert save_announcements(db,[a,b])==1
    assert save_announcements(db,[a])==0
    assert fingerprint('INFY',a['title'],day,'demo')!=fingerprint('INFY',a['title'],day,'sourced')

def test_default_window_priority_routine_and_mode_isolation(client):
    result = client.get('/api/announcements').json()
    assert result['items'] and all(i['priority']!='low' and i['mode']=='demo' for i in result['items'])
    scores=[r['score'] for r in result['items']]
    assert scores==sorted(scores,reverse=True)
    assert result['routine_count']>0
    full=client.get('/api/announcements?include_routine=true').json()
    assert len(full['items'])==len(result['items'])+result['routine_count']
    assert client.get('/api/announcements?mode=sourced').json()['items']==[]
    assert len(client.get('/api/announcements?window=7d').json()['items'])>len(result['items'])

def test_custom_dates_and_invalid_range(client):
    data=client.get('/api/announcements',params={'window':'custom','start':'2026-10-30T00:00:00+05:30','end':'2026-10-30T23:59:59+05:30','include_routine':'true'}).json()
    assert all(i['published_at']>='2026-10-29T18:30:00' and i['published_at']<='2026-10-30T18:29:59Z' for i in data['items'])
    assert client.get('/api/announcements?window=custom').status_code==422
    assert client.get('/api/announcements?window=custom&start=2026-10-31&end=2026-10-01').status_code==422
    assert client.get('/api/announcements?window=banana').status_code==422

def test_exchange_description_is_extracted_without_invented_summary():
    result=classify('Outcome of Board Meeting','Issuer approved consolidated quarterly financial results; see original filing.')
    assert 'Issuer approved consolidated quarterly financial results' in result['summary']
    assert result['summary'].startswith('Exchange description (extract):')
