from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT.parent / '.env', extra='ignore')
    database_url: str = f"sqlite:///{(ROOT / 'data' / 'finn.db').as_posix()}"
    cors_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'
    openai_api_key: str = ''
    openai_model: str = 'gpt-4.1-mini'
    finn_api_token: str = ''
    enable_scheduler: bool = False
    sync_interval_minutes: int = 60

settings = Settings()
