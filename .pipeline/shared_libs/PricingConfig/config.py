"""Configuration for the dynamic pricing module."""

from dataclasses import dataclass, field
from typing import List

from .constants import DEFAULT_POLLING_INTERVAL, DEFAULT_MARGIN_FLOOR


@dataclass
class PricingConfig:
    """Configuration for the dynamic pricing system.

    Attributes:
        polling_interval: How often (in seconds) to poll competitor prices.
        margin_floor: Minimum acceptable profit margin as a decimal (e.g. 0.15 = 15%).
        competitor_sources: List of competitor source identifiers to monitor.
    """
    polling_interval: int = DEFAULT_POLLING_INTERVAL
    margin_floor: float = DEFAULT_MARGIN_FLOOR
    competitor_sources: List[str] = field(default_factory=list)
