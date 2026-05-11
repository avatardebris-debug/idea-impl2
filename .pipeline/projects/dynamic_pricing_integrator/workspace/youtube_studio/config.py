"""YouTube Studio configuration — pricing integration defaults."""

from dataclasses import dataclass, field
from typing import List, Optional

from dynamic_pricing.config import PricingConfig


@dataclass
class YouTubeConfig:
    """Configuration for YouTube Studio integration.

    Attributes:
        pricing_enabled: Whether to enable pricing data in metadata.
        pricing_config: Underlying PricingConfig for pricing settings.
        channel_id: YouTube channel identifier.
        default_currency: Default currency for pricing.
        max_video_tags: Maximum number of tags per video.
    """
    pricing_enabled: bool = True
    pricing_config: Optional[PricingConfig] = None
    channel_id: str = ""
    default_currency: str = "USD"
    max_video_tags: int = 15
