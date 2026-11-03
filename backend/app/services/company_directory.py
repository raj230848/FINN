"""Bounded name/ticker search over NSE's equity directory, not the watchlist."""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import re
from threading import RLock
import unicodedata

from ..config import ROOT
from ..ingestion.http import fetch_public, SourceError
from ..schemas import normalize_ticker

SOURCE_URL='https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv'


def normalized(value):
    value=unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower().replace('&',' and ')
    return ' '.join(re.findall(r'[a-z0-9]+',value))


def short_name(value):
    return re.sub(r'\b(?:limited|ltd)\b','',normalized(value)).strip()


def parse_listing(content, minimum=100):
    entries={}
    for raw in csv.DictReader(io.StringIO(content.decode('utf-8-sig'))):
        row={k.strip():str(v or '').strip() for k,v in raw.items() if k}
        if not {'SYMBOL','NAME OF COMPANY','SERIES'}<=row.keys():raise SourceError('NSE directory schema changed; previous list retained.')
        ticker=normalize_ticker(row['SYMBOL']);name=row['NAME OF COMPANY']
        if not 2<=len(name)<=220:raise SourceError('NSE directory contains an invalid issuer name.')
        if ticker not in entries or row['SERIES']=='EQ':
            entries[ticker]={'ticker':ticker,'name':name,'series':row['SERIES'],'isin':row.get('ISIN NUMBER','')}
    if len(entries)<minimum:raise SourceError('NSE directory was incomplete; previous list retained.')
    return {'source_url':SOURCE_URL,'retrieved_at':datetime.now(timezone.utc).isoformat(),'source_sha256':hashlib.sha256(content).hexdigest(),'entries':list(entries.values())}


class CompanyDirectory:
    def __init__(self,bundled=None,cache=None):
        self.bundled=bundled or ROOT/'data/nse-directory.json'
        self.cache=cache or ROOT/'data/cache/nse-directory.json'
        self.lock=RLock();self.document=None;self.last_attempt=None;self.failed=False

    def load(self):
        with self.lock:
            if self.document is not None:return self.document
            for path in (self.cache,self.bundled):
                try:
                    if path.stat().st_size>2_000_000:continue
                    data=json.loads(path.read_text(encoding='utf-8'))
                    if data['source_url']!=SOURCE_URL or not isinstance(data['entries'],list) or not data['entries']:continue
                    datetime.fromisoformat(data['retrieved_at'])
                    if not all(normalize_ticker(r['ticker'])==r['ticker'] and isinstance(r['name'],str) and 2<=len(r['name'])<=220 for r in data['entries']):continue
                    self.document=data;return data
                except (OSError,ValueError,TypeError,KeyError):continue
            return None

    def stale(self,now=None):
        data=self.load();now=now or datetime.now(timezone.utc)
        if not data:return True
        stamp=datetime.fromisoformat(data['retrieved_at'])
        return now-stamp.replace(tzinfo=stamp.tzinfo or timezone.utc)>timedelta(days=7)

    def lookup(self, ticker):
        data = self.load()
        if not data:
            raise SourceError('The NSE company directory is unavailable. Try again later.')
        return next((entry for entry in data['entries'] if entry['ticker'] == ticker), None)

    def refresh(self):
        with self.lock:
            now=datetime.now(timezone.utc)
            if self.last_attempt and now-self.last_attempt<timedelta(hours=1):return False
            self.last_attempt=now
        try:
            content,_=fetch_public(SOURCE_URL,{'nsearchives.nseindia.com'},max_bytes=2_000_000)
            data=parse_listing(content)
            with self.lock:
                self.cache.parent.mkdir(parents=True,exist_ok=True)
                temporary=self.cache.with_suffix('.json.tmp');temporary.write_text(json.dumps(data)+'\n',encoding='utf-8');temporary.replace(self.cache)
                self.document=data;self.failed=False;return True
        except (OSError,ValueError):
            with self.lock:
                self.failed=True;return False

    def search(self,query,limit=8,sectors=None):
        query=re.sub(r'\.NS$','',query.strip(),flags=re.I)
        data=self.load();needle=normalized(query);compact=needle.replace(' ','');short=short_name(query)
        ranked=[]
        if data and len(needle)>=2:
            for row in data['entries']:
                ticker=normalized(row['ticker']).replace(' ','');name=normalized(row['name']);common=short_name(row['name'])
                if compact==ticker:score=0
                elif needle==name or short==common:score=1
                elif ticker.startswith(compact):score=2
                elif short and common.startswith(short):score=3
                elif all(any(word.startswith(part) for word in common.split()) for part in needle.split()):score=4
                elif needle in name:score=5
                else:continue
                ranked.append((score,row['name'],row))
        items=[{**row,'exchange':'NSE','verified':True,'sector':(sectors or {}).get(row['ticker']),'source_date':data['retrieved_at']} for _,_,row in sorted(ranked,key=lambda r:(r[0],r[1]))[:limit]]
        stale=self.stale()
        message='Type at least two characters to search NSE company names or tickers.' if len(needle)<2 else 'No matching NSE equity in the directory. Try its official company name or NSE ticker; foreign listings are not supported.' if not items else 'Choose a company to open its primary-source library.'
        if not data:message='The NSE company directory is unavailable. Try again later; no issuer identity was inferred.'
        return {'items':items,'available':bool(data),'stale':stale,'source_url':SOURCE_URL,'source_date':data['retrieved_at'] if data else None,'message':message,'warning':'Directory update unavailable; last known NSE list is shown.' if self.failed else 'Directory is over seven days old; an update will be attempted.' if stale and data else None}


directory=CompanyDirectory()
