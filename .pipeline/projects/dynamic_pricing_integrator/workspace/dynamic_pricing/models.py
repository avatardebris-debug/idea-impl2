"""Core data models for the dynamic pricing module."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .constants import DEFAULT_CURRENCY


@dataclass
class Product:
    """Represents a product being tracked for pricing.

    Attributes:
        id: Unique product identifier.
        name: Human-readable product name.
        base_price: The base/retail price of the product.
        currency: Currency code (e.g. 'USD', 'EUR').
        category: Product category string.
    """
    id: str
    name: str
    base_price: float
    currency: str = DEFAULT_CURRENCY
    category: str = ""


@dataclass
class CompetitorPrice:
    """Represents a price reported by a competitor for a product.

    Attributes:
        product_id: The product this price applies to.
        competitor_name: Name of the competitor.
        price: The competitor's price.
        last_updated: When this price was last updated.
    """
    product_id: str
    competitor_name: str
    price: float
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PriceSnapshot:
    """A captured snapshot of competitor pricing data.

    Attributes:
        product_id: The product this snapshot applies to.
        competitor: Name of the competitor.
        price: The captured price.
        timestamp: When the snapshot was taken.
        source: The data source that provided this price.
    """
    product_id: str
    competitor: str
    price: float
    timestamp: datetime
    source: str


# ---- New dataclasses for Phase 2 ----

from enum import Enum


class DiscountRuleType(Enum):
    """Supported discount rule types."""
    PRICE_GAP = "PriceGap"
    INVENTORY_AGE = "InventoryAge"
    MARGIN_FLOOR = "MarginFloor"
    COMPETITOR_MATCH = "CompetitorMatch"


class MarginStatusEnum(Enum):
    """Margin status relative to target."""
    BELOW = "below"
    WITHIN = "within"
    ABOVE = "above"


@dataclass
class DiscountRule:
    """A rule that can trigger a discount on a product.

    Attributes:
        rule_type: The type of discount rule (e.g. PriceGap, InventoryAge).
        gap_threshold: Price gap threshold for PriceGap rules (decimal).
        discount_pct: Discount percentage to apply (decimal, e.g. 0.10 = 10%).
        inventory_days: Days-in-inventory threshold for InventoryAge rules.
        margin_floor: Margin floor threshold for MarginFloor rules.
        strategy: Combination strategy when multiple rules apply.
    """
    rule_type: DiscountRuleType
    gap_threshold: float = 0.05
    discount_pct: float = 0.10
    inventory_days: int = 30
    margin_floor: float = 0.10
    strategy: str = "last_rule_wins"


@dataclass
class DiscountResult:
    """Result of applying a discount rule.

    Attributes:
        discount_pct: The discount percentage applied (decimal).
        effective_price: The price after discount.
        reason: Human-readable explanation of why the discount was applied.
    """
    discount_pct: float
    effective_price: float
    reason: str


@dataclass
class RecommendedPrice:
    """A recommended price for a product.

    Attributes:
        product_id: The product identifier.
        recommended_price: The suggested price.
        target_margin: The target margin percentage (decimal).
        floor: The minimum acceptable price.
        ceiling: The maximum acceptable price.
    """
    product_id: str
    recommended_price: float
    target_margin: float
    floor: float
    ceiling: float


@dataclass
class MarginStatus:
    """Current margin status for a product.

    Attributes:
        current_margin: The current profit margin as a decimal.
        target_margin: The target margin as a decimal.
        status: Enum indicating if margin is below/within/above target.
    """
    current_margin: float
    target_margin: float
    status: MarginStatusEnum

# ---- Phase 3 models ----

@dataclass
class ProductMetadata:
    """Unified product metadata combining SEO and pricing data.

    Attributes:
        product_id: The product identifier.
        name: Product name.
        base_price: Base/retail price.
        effective_price: Price after discounts applied.
        discount_pct: Applied discount percentage (decimal).
        margin_status: Current margin status enum.
        recommended_price: Optimized recommended price.
        floor_price: Minimum acceptable price.
        ceiling_price: Maximum acceptable price.
        competitive_position: Human-readable competitive position string.
        seo_title: SEO-optimized title.
        seo_description: SEO-optimized description.
        seo_tags: List of SEO tags.
        currency: Currency code.
        category: Product category.
        approval_status: Approval status ('pending', 'approved', 'rejected').
    """
    product_id: str
    name: str
    base_price: float
    effective_price: float
    discount_pct: float
    margin_status: MarginStatusEnum
    recommended_price: float
    floor_price: float
    ceiling_price: float
    competitive_position: str
    seo_title: str
    seo_description: str
    seo_tags: List[str]
    currency: str
    category: str
    approval_status: str = "pending"
