import hashlib
import re
import json
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

CATEGORIES = ['results','M&A','fund_raise','management_change','litigation','insider_trading','earnings_call','investor_meetings','credit_rating','dividend','bonus_split','capex','press_release','postal_ballot','agm_egm','pledging','unclassified']
RULES = [
    ('earnings_call', r'transcript|earnings call|con\.?\s*call|conference call|audio recording|video recording'),
    ('management_change', r'(?:cfo|ceo|chief financial(?: officer)?|chief executive(?: officer)?|managing director|independent director|director|key managerial|\bkmp\b|company secretary).{0,90}(?:resign|appoint|retir|cessation|change)|(?:resign|appoint|retir|cessation|change).{0,90}(?:chief financial|chief executive|director|\bcfo\b|\bceo\b|key managerial|company secretary|\bkmp\b)'),
    ('insider_trading', r'insider trading|pit regulations|(?:promoter|insider|designated person).{0,90}(?:acquir|purchas|bought|sold|sale|sell|dispos|trading)|(?:acquir|purchas|sold|dispos).{0,90}(?:promoter|insider|designated person)'),
    ('pledging', r'pledg|encumbrance'),
    ('M&A', r'acquisi|merger|demerger|joint venture|sale of.*stake|scheme of (?:arrangement|amalgamation)'),
    ('litigation', r'litigation|penalty|regulatory order|insolvency|lawsuit|sebi.*order|fine imposed'),
    ('results', r'financial results|quarterly results|annual results|audited.*results|board meeting.*results'),
    ('fund_raise', r'fund rais|\bqip\b|rights issue|preferential|buyback|commercial paper|debenture'),
    ('credit_rating', r'credit rating|rating.*(?:upgrade|downgrade|reaffirm)|(?:upgrade|downgrade|reaffirm).*(?:rating|credit)'),
    ('bonus_split', r'bonus issue|stock split|sub.division'),
    ('dividend', r'dividend'),
    ('capex', r'capital expenditure|capex|capacity expansion|new plant'),
    ('postal_ballot', r'postal ballot'),
    ('agm_egm', r'annual general meeting|extraordinary general meeting|\bagm\b|\begm\b'),
    ('investor_meetings', r'investor meet|analyst meet|investor conference|schedule.*analyst'),
    ('press_release', r'press release|order win|new product|partnership|(?:receipt|award|awarded|bagged).{0,50}(?:order|contract)|(?:order|contract).{0,50}(?:awarded|secured)|letter of award'),
]
SIGNIFICANCE = {
    'management_change': 'Leadership changes can affect execution and capital allocation. Review the effective date and succession arrangements.',
    'M&A': 'Review deal consideration, financing, approvals and potential dilution before assessing the impact.',
    'litigation': 'Regulatory or legal outcomes may affect cash flows or operations. The headline alone does not establish the financial exposure.',
    'results': 'Compare reported growth and profitability with prior periods; distinguish consolidated from standalone accounts.',
    'credit_rating': 'Changes in credit quality can affect borrowing costs and funding access.',
    'dividend': 'Review the distribution and record date. A dividend alone does not establish business performance.',
    'capex': 'Capital spending affects future capacity and near-term free cash flow.',
    'fund_raise': 'Review the funding terms and potential dilution or leverage.',
}

def classify(title: str, text: str = '') -> dict:
    content = f'{title} {text[:6000]}'.lower()
    category = next((c for c, p in RULES if re.search(p, content)), 'unclassified')
    score = {'management_change': 85,'M&A': 83,'litigation': 80,'results': 78,'fund_raise': 64,'credit_rating': 62,'capex': 60,'pledging': 60,'dividend': 45,'bonus_split': 45,'earnings_call': 40,'press_release': 40,'insider_trading': 55}.get(category, 15)
    factors = [f'Disclosure category: {category.replace("_", " ")} ({score} base points).']
    if category=='press_release' and re.search(r'order win|letter of award|(?:order|contract).{0,50}(?:awarded|secured)|(?:receipt|award|awarded|bagged).{0,50}(?:order|contract)',content):
        score=60
        factors.append('Order or contract disclosure merits review. Size relative to the issuer and revenue recognition are not established.')
    if re.search(r'resign|downgrad|default|insolvency', content):
        score = min(100, score + 10)
        factors.append('Departure, downgrade or distress language adds 10 points; verify the document context.')
    if re.search(r'board meeting.*(consider|intimation)|(?:intimation|notice).*board meeting|notice.*results|newspaper.*results', content) and not re.search(r'resign|appointed|appointment|downgrad|default|penalty|acquisition approved', content):
        score = min(score, 30)
        factors.append('Meeting notice or publication notice: actual results have not been established.')
    if re.search(r'newspaper.*(publication|advertisement)|copy of newspaper', title.lower()):
        score = min(score, 20)
        factors.append('Administrative newspaper republication; not treated as a new business event.')
    needs_review = category == 'unclassified' and bool(re.search(r'board meeting outcome|outcome of.*board|material event|management|regulatory action|director|promoter|rating|restructur', content))
    proposed_change = category == 'management_change' and bool(re.search(r'(?:notice|intimation).*board meeting|board meeting.*(?:consider|propos)', content)) and not re.search(r'resign|has been appointed|appointed with effect|approved.*appointment', content)
    if proposed_change:
        score = 55
        needs_review = True
        factors.append('Proposed leadership change in a meeting notice: completion is not established; needs review.')
    if needs_review:
        score = max(score, 55)
        factors.append('Potentially material wording without a confident category: needs review; not hidden as routine.')
    priority = 'high' if score >= 75 else 'medium' if score >= 40 else 'low'
    description = re.sub(r'\s+', ' ', text).strip()
    summary = (f'Exchange description (extract): {description[:650]}' + ('…' if len(description)>650 else '')) if description else f'Disclosure headline: {title}. Read the original filing for the full terms and context.'
    return {'needs_review': needs_review, 'category': category, 'score': score, 'priority': priority, 'factors': factors,
            'summary': summary,
            'why_matters': SIGNIFICANCE.get(category, 'Review the source for details. No material financial impact is established from the headline alone.')}

def description_checksum(text: str) -> str:
    return hashlib.sha256(re.sub(r'\s+', ' ', text).strip().encode()).hexdigest()


def canonical_source_url(url: str | None) -> str:
    if not url:
        return ''
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in ('http','https') or not parts.hostname:
        return ''
    # Generic listing pages are not attachment identities.
    if 'corporate-filings-announcements' in parts.path:
        return ''
    query = sorted((k,v) for k,v in parse_qsl(parts.query, keep_blank_values=True)
                   if not k.lower().startswith('utm_') and k.lower() not in ('fbclid','gclid'))
    return urlunsplit((parts.scheme.lower(),parts.netloc.lower(),parts.path,urlencode(query),''))


def fingerprint(ticker: str, title: str, published_at, mode: str,
                source_url: str | None = None, source_filing_id: str | None = None,
                content_checksum: str | None = None) -> str:
    url = canonical_source_url(source_url)
    checksum = content_checksum or description_checksum('')
    day = published_at.date().isoformat()
    if source_filing_id:
        identity = ['exchange-id',str(source_filing_id),url,checksum]
    elif url:
        identity = ['attachment',url,checksum]
    else:
        # With no authoritative identity, preserve separate publication times.
        identity = ['timestamp',published_at.isoformat(),re.sub(r'\W+',' ',title.lower()).strip(),checksum]
    raw = json.dumps([mode,ticker.upper(),day,identity],separators=(',',':'))
    return hashlib.sha256(raw.encode()).hexdigest()
