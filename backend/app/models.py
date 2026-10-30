from datetime import datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Company(Base):
    __tablename__ = 'companies'
    ticker: Mapped[str] = mapped_column(String(24), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    sector: Mapped[str] = mapped_column(String(100), default='Unverified sector')
    website: Mapped[str] = mapped_column(String(500), default='')
    watched: Mapped[bool] = mapped_column(Boolean, default=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

class Price(Base):
    __tablename__ = 'prices'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(ForeignKey('companies.ticker'), index=True)
    date: Mapped[datetime] = mapped_column(Date)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(12))
    source_url: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint('ticker', 'date', 'mode'),)

class Announcement(Base):
    __tablename__ = 'announcements'
    id: Mapped[int] = mapped_column(primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    ticker: Mapped[str] = mapped_column(ForeignKey('companies.ticker'), index=True)
    title: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    priority: Mapped[str] = mapped_column(String(12), index=True)
    score: Mapped[int] = mapped_column(Integer)
    factors: Mapped[list] = mapped_column(JSON)
    summary: Mapped[str] = mapped_column(Text)
    why_matters: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    text: Mapped[str] = mapped_column(Text, default='')
    mode: Mapped[str] = mapped_column(String(12), index=True)
    analysis_method: Mapped[str] = mapped_column(String(100), default='Deterministic rules; headline only')

class Preference(Base):
    __tablename__ = 'preferences'
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    price_threshold: Mapped[float] = mapped_column(Float, default=5)
    volume_multiplier: Mapped[float] = mapped_column(Float, default=2)
    lookback: Mapped[int] = mapped_column(Integer, default=20)
    companies: Mapped[list] = mapped_column(JSON, default=list)
    categories: Mapped[list] = mapped_column(JSON, default=list)

class Alert(Base):
    __tablename__ = 'alerts'
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(200), unique=True)
    ticker: Mapped[str] = mapped_column(ForeignKey('companies.ticker'), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    date: Mapped[datetime] = mapped_column(Date)
    mode: Mapped[str] = mapped_column(String(12), index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(ForeignKey('companies.ticker'), index=True)
    title: Mapped[str] = mapped_column(String(300))
    period: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(40))
    source_url: Mapped[str] = mapped_column(Text, unique=True)
    checksum: Mapped[str] = mapped_column(String(64))
    page_count: Mapped[int] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class Chunk(Base):
    __tablename__ = 'chunks'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), index=True)
    page: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

class Financial(Base):
    __tablename__ = 'financials'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(ForeignKey('companies.ticker'), index=True)
    period: Mapped[str] = mapped_column(String(40))
    basis: Mapped[str] = mapped_column(String(40), default='Consolidated IFRS')
    currency: Mapped[str] = mapped_column(String(12), default='INR crore')
    metrics: Mapped[dict] = mapped_column(JSON)
    source_url: Mapped[str] = mapped_column(Text)
    page: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(12))
    __table_args__ = (UniqueConstraint('ticker', 'period', 'basis', 'mode'),)

class Guidance(Base):
    __tablename__ = 'guidance'
    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(ForeignKey('companies.ticker'), index=True)
    data: Mapped[dict] = mapped_column(JSON)

class ResearchCache(Base):
    __tablename__ = 'research_cache'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class SyncRun(Base):
    __tablename__ = 'sync_runs'
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result: Mapped[dict] = mapped_column(JSON, default=dict)

Index('ix_announcements_mode_date_score', Announcement.mode, Announcement.published_at, Announcement.score)
