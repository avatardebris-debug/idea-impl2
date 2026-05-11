"""Configuration for the dynamic pricing module."""

from dataclasses import dataclass, field
from typing import List, Optional

from .constants import (
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_MARGIN_FLOOR,
    DEFAULT_CURRENCY,
)


@dataclass
class PricingConfig:
    """Configuration for the dynamic pricing system.

    Attributes:
        polling_interval: How often (in seconds) to poll competitor prices.
        margin_floor: Minimum acceptable profit margin as a decimal (e.g. 0.15 = 15%).
        competitor_sources: List of competitor source identifiers to monitor.
        real_time_polling: Whether to enable real-time price polling.
        seo_integration: Whether to integrate pricing data with SEO metadata.
        approval_required: Whether discounts require manual approval before application.
        currency: Default currency code for pricing.
        ceiling_multiplier: Multiplier for ceiling price relative to base price.
        target_margin: Target profit margin as a decimal.
    """
    polling_interval: int = DEFAULT_POLLING_INTERVAL
    margin_floor: float = DEFAULT_MARGIN_FLOOR
    competitor_sources: List[str] = field(default_factory=list)
    real_time_polling: bool = False
    seo_integration: bool = False
    approval_required: bool = False
    currency: str = DEFAULT_CURRENCY
    ceiling_multiplier: float = 1.5
    target_margin: float = 0.20
