"""API configuration — settings via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    """API configuration loaded from environment variables."""

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False

    # Database
    db_path: str = "sec_importer.db"

    # CORS
    cors_origins: list[str] = ["*"]

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Pagination
    max_limit: int = 500
    default_limit: int = 50

    # Caching
    cache_ttl_seconds: int = 300

    # Logging
    log_level: str = "INFO"

    # API Metadata
    api_title: str = "SEC Importer API"
    api_version: str = "0.1.0"
    api_description: str = "REST API for querying SEC EDGAR filing data."

    # EDGAR
    edgar_rate_limit_delay: float = 0.3

    # Tickers
    tickers_file: str = "sec_importer/tickers.csv"

    model_config = {"env_prefix": "API_", "env_file": ".env"}
