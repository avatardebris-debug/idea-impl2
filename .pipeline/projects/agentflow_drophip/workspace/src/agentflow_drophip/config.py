"""Configuration loader for AgentFlow Drophip.

Loads configuration from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # LLM settings
    llm_api_key: str = field(default="")
    llm_model: str = field(default="gpt-4o-mini")
    llm_base_url: Optional[str] = field(default=None)

    # Supplier settings
    aliexpress_api_key: str = field(default="")
    aliexpress_api_secret: str = field(default="")

    # Storefront settings
    shopify_api_key: str = field(default="")
    shopify_api_secret: str = field(default="")
    shopify_store_url: str = field(default="")

    # Workflow settings
    max_retries: int = field(default=3)
    retry_delay_seconds: float = field(default=2.0)
    default_markup: float = field(default=2.5)

    # Logging
    log_level: str = field(default="INFO")

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            llm_api_key=os.getenv("DROPHIP_LLM_API_KEY", ""),
            llm_model=os.getenv("DROPHIP_LLM_MODEL", "gpt-4o-mini"),
            llm_base_url=os.getenv("DROPHIP_LLM_BASE_URL"),
            aliexpress_api_key=os.getenv("DROPHIP_ALIEXPRESS_API_KEY", ""),
            aliexpress_api_secret=os.getenv("DROPHIP_ALIEXPRESS_API_SECRET", ""),
            shopify_api_key=os.getenv("DROPHIP_SHOPIFY_API_KEY", ""),
            shopify_api_secret=os.getenv("DROPHIP_SHOPIFY_API_SECRET", ""),
            shopify_store_url=os.getenv("DROPHIP_SHOPIFY_STORE_URL", ""),
            max_retries=int(os.getenv("DROPHIP_MAX_RETRIES", "3")),
            retry_delay_seconds=float(os.getenv("DROPHIP_RETRY_DELAY", "2.0")),
            default_markup=float(os.getenv("DROPHIP_DEFAULT_MARKUP", "2.5")),
            log_level=os.getenv("DROPHIP_LOG_LEVEL", "INFO"),
        )

    @property
    def llm_available(self) -> bool:
        """Check if LLM is configured."""
        return bool(self.llm_api_key)

    @property
    def supplier_configured(self) -> bool:
        """Check if supplier API is configured."""
        return bool(self.aliexpress_api_key)

    @property
    def storefront_configured(self) -> bool:
        """Check if storefront API is configured."""
        return bool(self.shopify_api_key and self.shopify_store_url)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
