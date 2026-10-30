"""Idempotent, conspicuously synthetic scenarios. Not corporate disclosures."""
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import select
from .config import ROOT
from .models import Announcement, Company, Financial, Guidance, Preference, Price
from .services.materiality import classify, fingerprint

DEMO_CLOCK = datetime(2026,10,30,13,0)
COMPANIES = [
 ('RELIANCE','Reliance Industries','Energy','https://www.ril.com'),
 ('TCS','Tata Consultancy Services','Information technology','https://www.tcs.com'),
 ('INFY','Infosys','Information technology','https://www.infosys.com'),
 ('HDFCBANK','HDFC Bank','Banking','https://www.hdfcbank.com'),
 ('ICICIBANK','ICICI Bank','Banking','https://www.icicibank.com'),
 ('ITC','ITC','Consumer goods','https://www.itcportal.com'),
 ('BHARTIARTL','Bharti Airtel','Telecommunications','https://www.airtel.in'),
 ('SUNPHARMA','Sun Pharmaceutical','Pharmaceuticals','https://sunpharma.com'),
 ('MARUTI','Maruti Suzuki','Automobiles','https://www.marutisuzuki.com'),
 ('LT','Larsen & Toubro','Infrastructure','https://www.larsentoubro.com'),
 ('HINDUNILVR','Hindustan Unilever','Consumer goods','https://www.hul.co.in'),
 ('SBIN','State Bank of India','Banking','https://sbi.co.in'),
 ('WIPRO','Wipro','Information technology','https://www.wipro.com'),
 ('TATASTEEL','Tata Steel','Metals','https://www.tatasteel.com'),
 ('BAJFINANCE','Bajaj Finance','Financial services','https://www.bajajfinserv.in'),
 ('PERSISTENT','Persistent Systems','Information technology','https://www.persistent.com'),
 ('KPRMILL','K.P.R. Mill','Textiles','https://kprmilllimited.com'),
 ('CERA','Cera Sanitaryware','Building products','https://www.cera-india.com'),
]

def seed(db):
    for ticker,name,sector,website in COMPANIES:
        if not db.get(Company,ticker):
            db.add(Company(ticker=ticker,name=name,sector=sector,website=website,watched=True,verified=False))
    if not db.get(Preference,1):
        db.add(Preference(id=1,price_threshold=5,volume_multiplier=2,lookback=20,companies=[],categories=[]))
    db.flush()
    if not db.scalar(select(Price.id).where(Price.mode=='demo').limit(1)):
        for n,(ticker,*_) in enumerate(COMPANIES):
            base = [1450,3900,1800,1700,1250,450,1600,1700,12000,3500,2400,800,300,140,7000,5700,950,6800][n]
            days = []
            day = DEMO_CLOCK.date()
            while len(days)<65:
                if day.weekday()<5:
                    days.append(day)
                day -= timedelta(days=1)
            days.reverse()
            for i,day in enumerate(days):
                close = base*(1+0.025*math.sin(i/5+n)+0.0006*i)
                volume = int((1_000_000+n*120000)*(1+0.12*math.sin(i+n)))
                if i==64:
                    previous = base*(1+0.025*math.sin((i-1)/5+n)+0.0006*(i-1))
                    move = {0:2.36,1:-1.24,2:1.82,3:-0.68,4:1.12,7:5.73,13:-5.28,15:3.41}.get(n,round(1.6*math.sin(n),2))
                    close = previous*(1+move/100)
                    if n in (0,7,15):
                        volume = int((1_000_000+n*120000)*{0:2.7,7:3.2,15:2.3}[n])
                db.add(Price(ticker=ticker,date=day,close=round(close,2),volume=volume,mode='demo',source_url=''))
    scenarios = [
      ('TCS','CFO resignation; succession plan announced','A simulated leadership transition to demonstrate how FINN elevates executive departures. No such corporate event is asserted.','Review the effective date, succession plan and incoming executive experience. A leadership change alone does not establish a change in earnings.',2),
      ('INFY','Quarterly financial results released','A simulated results alert. The separate research workspace uses dated, sourced Infosys documents; these are not today’s results.','Open research to compare revenue and profits on a consistent reporting basis.',3),
      ('RELIANCE','Acquisition of a strategic business approved','A simulated acquisition alert for the product walkthrough. The transaction and consideration are fictional.','Deal funding and integration could affect returns. No valuation conclusion can be drawn from this scenario.',5),
      ('SUNPHARMA','Capacity expansion receives board approval','A simulated capital expenditure disclosure. No actual investment amount or approval is asserted.','Capacity investments can support future output while reducing near-term free cash flow.',7),
      ('HDFCBANK','Credit rating reaffirmed; outlook stable','A simulated credit-rating update for demonstrating prioritisation.','A reaffirmation preserves a rating; it should not be treated as an upgrade.',9),
      ('ITC','Dividend declaration and record date','A simulated dividend disclosure. No dividend amount or record date is represented as real.','Check eligibility and cash distribution against the company’s source filing.',12),
      ('LT','Investor meeting schedule disclosed','Simulated routine investor-meeting paperwork.','Scheduling information is available, but no change in company fundamentals is established.',15),
      ('WIPRO','Compliance certificate for share transfer facility','Simulated administrative filing, grouped as routine.','No business impact is established by this compliance scenario.',18),
      ('CERA','Postal ballot voting notice','Simulated shareholder voting notice.','Review resolutions in the source before inferring materiality.',20),
      ('TATASTEEL','Regulatory penalty order disclosed','A simulated legal disclosure from an earlier demo session. No real order or exposure is asserted.','Legal exposure requires the actual order and company response.',50),
      ('MARUTI','Quarterly financial results published','A simulated result announcement from last week.','Compare reported volumes and profitability with the source results.',110),
    ]
    for ticker,title,summary,why,hours in scenarios:
        published = DEMO_CLOCK-timedelta(hours=hours)
        key = fingerprint(ticker,title,published,'demo')
        if not db.scalar(select(Announcement.id).where(Announcement.fingerprint==key)):
            result = classify(title)
            result.update(summary=summary,why_matters=why)
            db.add(Announcement(ticker=ticker,title=title,published_at=published,source_url=None,text='',mode='demo',fingerprint=key,analysis_method='Synthetic scenario; deterministic classification',**result))
    # Verified historical metrics/guidance are installed only from the separate
    # reviewed manifest created after the actual source PDFs have been fetched.
    manifest = ROOT/'data'/'primary'/'verified.json'
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding='utf-8'))
        for row in data.get('financials',[]):
            if not db.scalar(select(Financial.id).where(Financial.ticker==row['ticker'],Financial.period==row['period'],Financial.mode=='sourced')):
                db.add(Financial(mode='sourced',**row))
        if not db.scalar(select(Guidance.id).limit(1)):
            db.add_all([Guidance(ticker=row['ticker'],data=row) for row in data.get('guidance',[])])
    db.commit()
