"""
Application settings loaded from environment variables via pydantic-settings.
A single Settings instance is created and reused throughout the app.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configurable values come from .env or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App metadata
    app_name: str = "Mini AI Personal Assistant"
    app_version: str = "1.0.0"
    debug: bool = True

    # Backend
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Database
    database_url: str = "sqlite:///./data/assistant.db"

    # Frontend
    frontend_host: str = "127.0.0.1"
    frontend_port: int = 8501
    backend_url: str = "http://127.0.0.1:8000"

    # Search
    fuzzy_match_threshold: int = 70
    max_search_results: int = 20


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns the cached Settings singleton."""
    return Settings()
