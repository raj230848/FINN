from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT.parent / '.env', extra='ignore')
    database_url: str = f"sqlite:///{(ROOT / 'data' / 'finn.db').as_posix()}"
    cors_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-3.5-flash-lite'
    finn_api_token: str = ''
    enable_scheduler: bool = False
    sync_interval_minutes: int = 60
    filing_lookback_days: int = 7
    document_max_pages: int = Field(default=3000,ge=1,le=10000)
    document_max_download_bytes: int = Field(default=60_000_000,ge=1,le=100_000_000)
    document_max_text_chars: int = Field(default=12_000_000,ge=200,le=30_000_000)
    document_max_page_chars: int = Field(default=200_000,ge=200,le=2_000_000)
    document_max_chunks: int = Field(default=20000,ge=1,le=50000)
    document_extract_timeout_seconds: int = Field(default=90,ge=1,le=120)
    public_deployment: bool = False
    vapid_private_key: str = ''
    vapid_public_key: str = ''
    vapid_subject: str = ''

settings = Settings()
