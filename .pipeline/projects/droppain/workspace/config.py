"""Configuration for droppain.

Manages application settings loaded from environment variables and defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from droppain.exceptions import ConfigurationError


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # Shopify settings
    shopify_api_key: str = field(default_factory=lambda: os.environ.get("SHOPIFY_API_KEY", ""))
    shopify_password: str = field(default_factory=lambda: os.environ.get("SHOPIFY_PASSWORD", ""))
    shopify_store_name: str = field(default_factory=lambda: os.environ.get("SHOPIFY_STORE_NAME", ""))
    shopify_api_version: str = field(default_factory=lambda: os.environ.get("SHOPIFY_API_VERSION", "2024-01"))

    # Campaign settings
    campaign_name_prefix: str = field(default_factory=lambda: os.environ.get("DROPPAIN_CAMPAIGN_PREFIX", "Dropship Campaign"))
    default_currency: str = field(default_factory=lambda: os.environ.get("DEFAULT_CURRENCY", "USD"))
    default_timezone: str = field(default_factory=lambda: os.environ.get("DROPPAIN_DEFAULT_TIMEZONE", "UTC"))
    supported_currencies: List[str] = field(default_factory=lambda: ["USD", "EUR", "GBP", "CAD"])

    # Content settings
    default_content_length: int = 280
    default_hashtags: List[str] = field(default_factory=lambda: [
        "#dropshipping", "#ecommerce", "#onlineshopping", "#shopnow", "#deals"
    ])

    # Execution settings
    max_products_per_campaign: int = 100
    api_timeout: int = 30
    api_max_retries: int = 3

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Validate Shopify credentials require store name
        if (self.shopify_api_key or self.shopify_password) and not self.shopify_store_name:
            raise ConfigurationError(
                "SHOPIFY_STORE_NAME is required when Shopify credentials are provided"
            )

    @property
    def is_shopify_configured(self) -> bool:
        """Check if Shopify integration is configured."""
        return bool(self.shopify_api_key or self.shopify_password)

    @property
    def shopify_base_url(self) -> str:
        """Get the Shopify API base URL."""
        if not self.shopify_store_name:
            raise ConfigurationError("SHOPIFY_STORE_NAME is required to generate base URL")
        return f"https://{self.shopify_api_key}:{self.shopify_password}@{self.shopify_store_name}.myshopify.com/admin/api/{self.shopify_api_version}"


def get_config() -> Config:
    """Get application configuration from environment variables.

    Returns:
        Config instance with values from environment variables.
    """
    return Config(
        shopify_api_key=os.environ.get("SHOPIFY_API_KEY", ""),
        shopify_password=os.environ.get("SHOPIFY_PASSWORD", ""),
        shopify_store_name=os.environ.get("SHOPIFY_STORE_NAME", ""),
        shopify_api_version=os.environ.get("SHOPIFY_API_VERSION", "2024-01"),
        campaign_name_prefix=os.environ.get("DROPPAIN_CAMPAIGN_PREFIX", "Dropship Campaign"),
        default_currency=os.environ.get("DEFAULT_CURRENCY", "USD"),
    )
