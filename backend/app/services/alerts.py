from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from ..models import Alert, Announcement, Company, Preference, Price
from .calculations import percent_change, volume_ratio
from .events import record_event

def quotes(db: Session, mode: str, lookback: int = 20) -> list[dict]:
    result = []
    for company in db.scalars(select(Company).where(Company.watched.is_(True)).order_by(Company.ticker)):
        prices = list(db.scalars(select(Price).where(Price.ticker == company.ticker, Price.mode == mode).order_by(Price.date.desc()).limit(65)))[::-1]
        latest = prices[-1] if prices else None
        result.append({'ticker':company.ticker,'name':company.name,'sector':company.sector,'verified':company.verified,
            'close':latest.close if latest else None,'date':latest.date.isoformat() if latest else None,
            'change_pct':percent_change(latest.close,prices[-2].close) if len(prices)>1 else None,
            'volume_ratio':volume_ratio(latest.volume,[p.volume for p in prices[:-1]],lookback) if latest else None,
            'volume':latest.volume if latest else None,'source_url':latest.source_url if latest else None,
            'fetched_at':latest.fetched_at.isoformat()+'Z' if latest else None,
            'history':[{'date':p.date.isoformat(),'close':p.close,'volume':p.volume} for p in prices]})
    return result

def evaluate_alerts(db: Session, mode: str) -> int:
    pref = db.get(Preference, 1)
    db.execute(delete(Alert).where(Alert.mode == mode))
    count = 0
    watched = set(db.scalars(select(Company.ticker).where(Company.watched.is_(True))))
    selected = set(pref.companies) if pref.companies else watched
    for quote in quotes(db, mode, pref.lookback):
        if quote['ticker'] not in selected or not quote['date']:
            continue
        for kind, value, threshold, crossed in [
            ('price',quote['change_pct'],pref.price_threshold,quote['change_pct'] is not None and abs(quote['change_pct']) >= pref.price_threshold),
            ('volume',quote['volume_ratio'],pref.volume_multiplier,quote['volume_ratio'] is not None and quote['volume_ratio'] >= pref.volume_multiplier),
        ]:
            if not crossed:
                continue
            from datetime import date
            title = f"{quote['ticker']}: {value:+.2f}% daily move" if kind == 'price' else f"{quote['ticker']}: {value:.2f}x usual volume"
            explanation = (f"Completed-session adjusted close changed {value:+.2f}% versus the preceding trading session; your threshold is +/-{threshold:g}%." if kind=='price' else f"Completed-session volume is {value:.2f} times the mean of the PRECEDING {pref.lookback} trading sessions (current day excluded); your threshold is {threshold:g}x.")
            db.add(Alert(key=f"{mode}:{quote['ticker']}:{quote['date']}:{kind}",ticker=quote['ticker'],kind=kind,title=title,explanation=explanation,value=value,threshold=threshold,date=date.fromisoformat(quote['date']),mode=mode,source_url=quote['source_url']))
            from datetime import datetime
            record_event(db,event_key=f"market:{mode}:{quote['ticker']}:{quote['date']}:{kind}",
                         ticker=quote['ticker'],mode=mode,kind=kind,severity='high',title=title,
                         explanation=explanation,occurred_at=datetime.fromisoformat(quote['date']),
                         source_url=quote['source_url'])
            count += 1
    db.flush()
    return count
