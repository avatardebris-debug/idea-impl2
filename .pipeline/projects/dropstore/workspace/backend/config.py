"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://dropstore:dropstore@localhost:5432/dropstore"
    redis_url: str = "redis://localhost:6379/0"

    # Shopify
    shopify_api_key: str = ""
    shopify_api_secret: str = ""
    shopify_scopes: str = "read_products,write_products,read_orders"

    # App
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    secret_key: str = "dropstore-dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 30  # 30 days

    # Supplier APIs
    aliexpress_api_key: str = ""
    aliexpress_api_secret: str = ""
    cjdropshipping_api_key: str = ""
    cjdropshipping_api_secret: str = ""

    # Sync settings
    sync_interval_hours: int = 6
    sync_max_retries: int = 3

    # Alert thresholds
    low_stock_threshold: int = 10
    price_change_threshold_pct: float = 10.0

    # Mock data mode (for development without real APIs)
    mock_data: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
