import math
import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator

Mode = Literal['demo', 'sourced']

def normalize_ticker(value: str) -> str:
    symbol = value.strip().upper().removesuffix('.NS')
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9&-]{0,23}', symbol):
        raise ValueError('Enter an NSE symbol, for example INFY or M&M. Do not enter a URL.')
    return symbol

class PreferencesIn(BaseModel):
    price_threshold: float = Field(default=5, ge=0.1, le=50, allow_inf_nan=False)
    volume_multiplier: float = Field(default=2, ge=1.1, le=20, allow_inf_nan=False)
    lookback: int = Field(default=20, ge=5, le=60)
    companies: list[str] = Field(default_factory=list, max_length=100)
    categories: list[str] = Field(default_factory=list, max_length=20)

    @field_validator('companies')
    @classmethod
    def clean_symbols(cls, values):
        return list(dict.fromkeys(normalize_ticker(x) for x in values))

class ResearchIn(BaseModel):
    ticker: str
    question: str = Field(min_length=4, max_length=1200)
    use_ai: bool = True
    refresh: bool = False

    @field_validator('ticker')
    @classmethod
    def clean_symbol(cls, v):
        return normalize_ticker(v)

class ImportDocumentIn(BaseModel):
    ticker: str
    url: str = Field(max_length=2000)
    title: str = Field(min_length=3, max_length=300)
    period: str = Field(min_length=2, max_length=80)
    kind: Literal['annual_report', 'transcript', 'results', 'investor_presentation']
    # For a new company, its issuer domain must match the authoritative listing
    # from NSE. Exchange archive domains are independently accepted.

    @field_validator('ticker')
    @classmethod
    def clean_symbol(cls, v):
        return normalize_ticker(v)

class WatchIn(BaseModel):
    watched: bool

class PushSubscriptionIn(BaseModel):
    device_id: str = Field(pattern=r'^[A-Za-z0-9_-]{32,64}$')
    subscription: dict

class PushDisableIn(BaseModel):
    device_id: str = Field(pattern=r'^[A-Za-z0-9_-]{32,64}$')

class AnalysisOut(BaseModel):
    answer: str = Field(min_length=10, max_length=6000)
    evidence_ids: list[int] = Field(min_length=1, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=8)

class GroundingReviewOut(BaseModel):
    supported: bool
    unsupported_claims: list[str] = Field(default_factory=list, max_length=20)
    reason: str = Field(max_length=1200)

class SynthesisClaim(BaseModel):
    text: str = Field(min_length=10,max_length=800)
    evidence_ids: list[int] = Field(min_length=1,max_length=6)

class SynthesisOut(BaseModel):
    claims: list[SynthesisClaim] = Field(min_length=1,max_length=8)
    limitations: list[str] = Field(default_factory=list,max_length=8)

class ClassificationOut(BaseModel):
    category: Literal['results','M&A','fund_raise','management_change','litigation','insider_trading','earnings_call','investor_meetings','credit_rating','dividend','bonus_split','capex','press_release','postal_ballot','agm_egm','pledging','unclassified']
    summary: str = Field(min_length=10, max_length=900)
    why_matters: str = Field(min_length=10, max_length=900)
    confidence: Literal['high','medium','low'] = 'low'
    evidence_quote: str = Field(default='', max_length=500)
