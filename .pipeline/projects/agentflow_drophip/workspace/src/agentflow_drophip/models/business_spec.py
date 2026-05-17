"""BusinessSpec — the structured business specification that the Intent Parser outputs."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SupplierType(str, Enum):
    """Supported supplier platforms."""
    ALIEXPRESS = "aliexpress"
    SPOCKET = "spocket"
    CJ_DROPSHIPPING = "cj_dropsshipping"
    DROPSHIPMOBILE = "dropshipmobile"
    CUSTOM = "custom"


class FulfillmentType(str, Enum):
    """Fulfillment modes."""
    AUTO = "auto"
    MANUAL = "manual"
    HYBRID = "hybrid"


class StorefrontType(str, Enum):
    """Supported storefront platforms."""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    ECOMMERCE_PLATFORM = "ecommerce_platform"
    CUSTOM = "custom"


class TargetMarket(BaseModel):
    """Geographic target market configuration."""
    countries: List[str] = Field(default_factory=list, description="ISO 3166-1 alpha-2 country codes")
    currency: str = Field(default="USD", description="Primary currency")
    language: str = Field(default="en", description="Primary language code")

    @field_validator("countries")
    @classmethod
    def countries_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one target country must be specified")
        return v


class BrandingConfig(BaseModel):
    """Branding and packaging preferences."""
    brand_name: Optional[str] = None
    custom_packaging: bool = False
    custom_packaging_message: Optional[str] = None
    logo_url: Optional[str] = None
    color_scheme: Optional[str] = None
    tone_of_voice: Optional[str] = None


class PricingStrategy(str, Enum):
    """Pricing strategies."""
    MARKUP = "markup"
    COMPETITIVE = "competitive"
    PREMIUM = "premium"


class PricingConfig(BaseModel):
    """Pricing strategy configuration."""
    markup_multiplier: float = Field(default=1.0, ge=1.0, description="Markup multiplier (e.g., 2.5 for 2.5x)")
    min_price: Optional[float] = Field(default=None, ge=0, description="Minimum selling price")
    max_price: Optional[float] = Field(default=None, ge=0, description="Maximum selling price")
    pricing_strategy: PricingStrategy = Field(
        default=PricingStrategy.MARKUP,
        description="Pricing strategy: markup, competitive, or premium"
    )

    @field_validator("pricing_strategy")
    @classmethod
    def validate_pricing_strategy(cls, v: PricingStrategy) -> PricingStrategy:
        return v
    discount_rules: List[dict] = Field(default_factory=list, description="Discount/promotion rules")


class BusinessSpec(BaseModel):
    """Complete business specification for a dropshipping operation.

    This is the structured output of the Intent Parser, representing
    the user's natural-language intent as a validated data model.
    """
    # Core identity
    niche: str = Field(description="Product niche/category (e.g., 'pet supplies')")
    supplier: SupplierType = Field(default=SupplierType.ALIEXPRESS, description="Preferred supplier platform")
    storefront: StorefrontType = Field(default=StorefrontType.SHOPIFY, description="Preferred storefront platform")

    # Market
    target_market: TargetMarket = Field(default_factory=TargetMarket)

    # Pricing
    pricing: PricingConfig = Field(default_factory=PricingConfig)

    # Fulfillment
    fulfillment: FulfillmentType = Field(default=FulfillmentType.AUTO, description="Fulfillment mode")

    # Branding
    branding: BrandingConfig = Field(default_factory=BrandingConfig)

    # Additional metadata
    description: str = Field(default="", description="Free-text description of the business")
    max_product_cost: Optional[float] = Field(default=None, ge=0, description="Maximum product cost from supplier")
    min_profit_margin: Optional[float] = Field(default=None, ge=0, le=1, description="Minimum profit margin (0-1)")
    auto_reorder_threshold: Optional[int] = Field(default=None, ge=0, description="Inventory threshold for auto-reorder")

    @field_validator("niche")
    @classmethod
    def niche_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Niche must be a non-empty string")
        return v.strip()

    @field_validator("pricing")
    @classmethod
    def pricing_valid(cls, v: PricingConfig) -> PricingConfig:
        if v.pricing_strategy not in ("markup", "competitive", "premium"):
            raise ValueError("pricing_strategy must be 'markup', 'competitive', or 'premium'")
        return v

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return self.model_dump()

    def __str__(self) -> str:
        return (
            f"BusinessSpec(niche={self.niche!r}, supplier={self.supplier.value}, "
            f"storefront={self.storefront.value}, target_market={self.target_market.countries}, "
            f"markup={self.pricing.markup_multiplier}x)"
        )
