"""Environment-based configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/user_service_db"
    firebase_credentials_path: Optional[str] = None
    google_application_credentials: Optional[str] = None
    internal_api_secret: str = "your-internal-service-secret-change-in-production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
