"""Dynamic Pricing Integrator — Phase 1 & 2 & 3 package.

Exports core models, configuration, mock sources, price tracker,
discount engine, margin optimizer, pricing integrator, exporters,
and YouTube Studio integration.
"""

from .config import PricingConfig
from .constants import (
    DEFAULT_CURRENCY,
    DEFAULT_DISCOUNT_PERCENT,
    DEFAULT_GAP_THRESHOLD,
    DEFAULT_INVENTORY_DAYS_THRESHOLD,
    DEFAULT_MARGIN_FLOOR,
    DEFAULT_MARGIN_FLOOR_THRESHOLD,
    DEFAULT_POLLING_INTERVAL,
    DEFAULT_CEILING_MULTIPLIER,
    PRICING_STRATEGY_COMPETITOR_MATCH,
    PRICING_STRATEGY_INVENTORY_AGE,
    PRICING_STRATEGY_MARGIN_FLOOR,
    PRICING_STRATEGY_PRICE_GAP,
)
from .discount_engine import (
    BaseRule,
    CompetitorMatchRule,
    DiscountEngine,
    InventoryAgeRule,
    MarginFloorRule,
    PriceGapRule,
)
from .integrator import PricingIntegrator
from .margin_optimizer import MarginOptimizer
from .models import (
    CompetitorPrice,
    DiscountResult,
    DiscountRule,
    DiscountRuleType,
    MarginStatus,
    MarginStatusEnum,
    PriceSnapshot,
    Product,
    ProductMetadata,
    RecommendedPrice,
)
from .price_tracker import PriceTracker
from .mock_sources import MockAPISource, MockCSVSource
from .exporters.json_exporter import JSONExporter
from .exporters.csv_exporter import CSVExporter
from youtube_studio.youtube_studio import YouTubeStudio
from youtube_studio.seo_optimizer import SEOOptimizer
from youtube_studio.config import YouTubeConfig
from youtube_studio.constants import (
    YOUTUBE_PRICING_ENABLED,
    YOUTUBE_DEFAULT_CURRENCY,
    YOUTUBE_MAX_TITLE_LENGTH,
    YOUTUBE_MAX_DESCRIPTION_LENGTH,
    YOUTUBE_MAX_TAGS_COUNT,
    YOUTUBE_DEFAULT_POLLING_INTERVAL,
    YOUTUBE_DEFAULT_MARGIN_FLOOR,
    YOUTUBE_DEFAULT_SEO_TITLE_SUFFIX,
    YOUTUBE_DEFAULT_SEO_TAGS,
)

__all__ = [
    # Config
    "PricingConfig",
    "YouTubeConfig",
    # Constants
    "DEFAULT_CURRENCY",
    "DEFAULT_DISCOUNT_PERCENT",
    "DEFAULT_GAP_THRESHOLD",
    "DEFAULT_INVENTORY_DAYS_THRESHOLD",
    "DEFAULT_MARGIN_FLOOR",
    "DEFAULT_MARGIN_FLOOR_THRESHOLD",
    "DEFAULT_POLLING_INTERVAL",
    "DEFAULT_CEILING_MULTIPLIER",
    "PRICING_STRATEGY_COMPETITOR_MATCH",
    "PRICING_STRATEGY_INVENTORY_AGE",
    "PRICING_STRATEGY_MARGIN_FLOOR",
    "PRICING_STRATEGY_PRICE_GAP",
    "YOUTUBE_PRICING_ENABLED",
    "YOUTUBE_DEFAULT_CURRENCY",
    "YOUTUBE_MAX_TITLE_LENGTH",
    "YOUTUBE_MAX_DESCRIPTION_LENGTH",
    "YOUTUBE_MAX_TAGS_COUNT",
    "YOUTUBE_DEFAULT_POLLING_INTERVAL",
    "YOUTUBE_DEFAULT_MARGIN_FLOOR",
    "YOUTUBE_DEFAULT_SEO_TITLE_SUFFIX",
    "YOUTUBE_DEFAULT_SEO_TAGS",
    # Discount Engine
    "BaseRule",
    "CompetitorMatchRule",
    "DiscountEngine",
    "InventoryAgeRule",
    "MarginFloorRule",
    "PriceGapRule",
    # Integrator
    "PricingIntegrator",
    # Margin Optimizer
    "MarginOptimizer",
    # Models
    "CompetitorPrice",
    "DiscountResult",
    "DiscountRule",
    "DiscountRuleType",
    "MarginStatus",
    "MarginStatusEnum",
    "PriceSnapshot",
    "Product",
    "ProductMetadata",
    "RecommendedPrice",
    # Price Tracker
    "PriceTracker",
    # Sources
    "MockAPISource",
    "MockCSVSource",
    # Exporters
    "JSONExporter",
    "CSVExporter",
    # YouTube Studio
    "YouTubeStudio",
    "SEOOptimizer",
]
