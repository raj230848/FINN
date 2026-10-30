import hashlib
import re

CATEGORIES = ['results','M&A','fund_raise','management_change','litigation','insider_trading','earnings_call','investor_meetings','credit_rating','dividend','bonus_split','capex','press_release','postal_ballot','agm_egm','pledging','unclassified']
RULES = [
    ('earnings_call', r'transcript|earnings call|concall|conference call'),
    ('management_change', r'\b(cfo|ceo|chief financial|chief executive|managing director)\b.*(resign|appoint|retir)|resign.*\b(director|cfo|ceo)\b|change.*management|director.*appoint'),
    ('M&A', r'acquisi|merger|demerger|joint venture|sale of.*stake'),
    ('litigation', r'litigation|penalty|regulatory order|insolvency|lawsuit|sebi.*order|fine imposed'),
    ('results', r'financial results|quarterly results|annual results|audited.*results|board meeting.*results'),
    ('fund_raise', r'fund rais|qip|rights issue|preferential|buyback|commercial paper|debenture'),
    ('credit_rating', r'credit rating|rating.*(upgrade|downgrade|reaffirm)'),
    ('bonus_split', r'bonus issue|stock split|sub.division'),
    ('dividend', r'dividend'),
    ('capex', r'capital expenditure|capex|capacity expansion|new plant'),
    ('pledging', r'pledg|encumbrance'),
    ('insider_trading', r'insider trading|pit regulations|trading.*promoter'),
    ('postal_ballot', r'postal ballot'),
    ('agm_egm', r'annual general meeting|extraordinary general meeting|\bagm\b|\begm\b'),
    ('investor_meetings', r'investor meet|analyst meet|investor conference|schedule.*analyst'),
    ('press_release', r'press release|order win|new product|partnership'),
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
    score = {'management_change': 85,'M&A': 83,'litigation': 80,'results': 78,'fund_raise': 64,'credit_rating': 62,'capex': 60,'pledging': 60,'dividend': 45,'bonus_split': 45,'earnings_call': 40,'press_release': 40,'insider_trading': 40}.get(category, 15)
    factors = [f'Disclosure category: {category.replace("_", " ")} ({score} base points).']
    if re.search(r'resign|downgrad|default|insolvency', content):
        score = min(100, score + 10)
        factors.append('Departure, downgrade or distress language adds 10 points; verify the document context.')
    if re.search(r'board meeting.*(consider|intimation)|notice.*results|newspaper.*results', content):
        score = min(score, 30)
        factors.append('Meeting notice or publication notice: actual results have not been established.')
    priority = 'high' if score >= 75 else 'medium' if score >= 40 else 'low'
    return {'category': category, 'score': score, 'priority': priority, 'factors': factors,
            'summary': f'Disclosure headline: {title}. Read the original filing for the full terms and context.',
            'why_matters': SIGNIFICANCE.get(category, 'Review the source for details. No material financial impact is established from the headline alone.')}

def fingerprint(ticker: str, title: str, published_at, mode: str) -> str:
    # Same issuer, normalised title, same calendar date is one event, even when
    # an exchange republishes it with a different attachment URL or time.
    normalised = re.sub(r'\W+', ' ', title.lower()).strip()
    raw = f'{mode}|{ticker}|{published_at.date().isoformat()}|{normalised}'
    return hashlib.sha256(raw.encode()).hexdigest()
