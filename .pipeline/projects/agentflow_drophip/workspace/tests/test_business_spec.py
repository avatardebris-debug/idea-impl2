"""Tests for business_spec models."""

import pytest
from pydantic import ValidationError

from agentflow_drophip.models.business_spec import (
    BrandingConfig,
    BusinessSpec,
    FulfillmentType,
    PricingConfig,
    PricingStrategy,
    StorefrontType,
    SupplierType,
    TargetMarket,
)


class TestTargetMarket:
    """Tests for TargetMarket model."""

    def test_valid_target_market(self):
        """Test creating a valid TargetMarket."""
        market = TargetMarket(
            countries=["US", "CA"],
            currency="USD",
            language="en"
        )
        assert market.countries == ["US", "CA"]
        assert market.currency == "USD"
        assert market.language == "en"

    def test_default_target_market(self):
        """Test default TargetMarket values."""
        market = TargetMarket()
        assert market.countries == []
        assert market.currency == "USD"
        assert market.language == "en"

    def test_empty_countries_raises_error(self):
        """Test that empty countries list raises ValidationError."""
        with pytest.raises(ValidationError):
            TargetMarket(countries=[])

    def test_to_dict(self):
        """Test serialization to dict."""
        market = TargetMarket(countries=["US"], currency="USD", language="en")
        d = market.model_dump()
        assert d["countries"] == ["US"]
        assert d["currency"] == "USD"
        assert d["language"] == "en"


class TestBrandingConfig:
    """Tests for BrandingConfig model."""

    def test_default_branding_config(self):
        """Test default BrandingConfig values."""
        config = BrandingConfig()
        assert config.brand_name is None
        assert config.custom_packaging is False
        assert config.custom_packaging_message is None
        assert config.logo_url is None
        assert config.color_scheme is None
        assert config.tone_of_voice is None

    def test_full_branding_config(self):
        """Test BrandingConfig with all fields."""
        config = BrandingConfig(
            brand_name="MyBrand",
            custom_packaging=True,
            custom_packaging_message="Thank you!",
            logo_url="https://example.com/logo.png",
            color_scheme="#FF0000",
            tone_of_voice="friendly"
        )
        assert config.brand_name == "MyBrand"
        assert config.custom_packaging is True
        assert config.custom_packaging_message == "Thank you!"
        assert config.logo_url == "https://example.com/logo.png"
        assert config.color_scheme == "#FF0000"
        assert config.tone_of_voice == "friendly"


class TestPricingConfig:
    """Tests for PricingConfig model."""

    def test_default_pricing_config(self):
        """Test default PricingConfig values."""
        config = PricingConfig()
        assert config.markup_multiplier == 1.0
        assert config.min_price is None
        assert config.max_price is None
        assert config.pricing_strategy == PricingStrategy.MARKUP
        assert config.discount_rules == []

    def test_custom_pricing_config(self):
        """Test PricingConfig with custom values."""
        config = PricingConfig(
            markup_multiplier=2.5,
            min_price=10.0,
            max_price=100.0,
            pricing_strategy=PricingStrategy.COMPETITIVE,
            discount_rules=[{"type": "bulk", "min_qty": 5}]
        )
        assert config.markup_multiplier == 2.5
        assert config.min_price == 10.0
        assert config.max_price == 100.0
        assert config.pricing_strategy == PricingStrategy.COMPETITIVE
        assert len(config.discount_rules) == 1

    def test_invalid_markup_multiplier_raises_error(self):
        """Test that markup_multiplier < 1.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            PricingConfig(markup_multiplier=0.5)

    def test_invalid_min_price_raises_error(self):
        """Test that min_price < 0 raises ValidationError."""
        with pytest.raises(ValidationError):
            PricingConfig(min_price=-1.0)

    def test_invalid_max_price_raises_error(self):
        """Test that max_price < 0 raises ValidationError."""
        with pytest.raises(ValidationError):
            PricingConfig(max_price=-1.0)


class TestBusinessSpec:
    """Tests for BusinessSpec model."""

    def test_valid_business_spec(self):
        """Test creating a valid BusinessSpec."""
        spec = BusinessSpec(
            niche="pet supplies",
            supplier=SupplierType.ALIEXPRESS,
            storefront=StorefrontType.SHOPIFY,
            target_market=TargetMarket(countries=["US"], currency="USD", language="en"),
            pricing=PricingConfig(markup_multiplier=2.0),
            fulfillment=FulfillmentType.AUTO,
            branding=BrandingConfig(brand_name="PetShop"),
            description="A pet supplies store",
        )
        assert spec.niche == "pet supplies"
        assert spec.supplier == SupplierType.ALIEXPRESS
        assert spec.storefront == StorefrontType.SHOPIFY
        assert spec.fulfillment == FulfillmentType.AUTO
        assert spec.branding.brand_name == "PetShop"

    def test_default_business_spec(self):
        """Test default BusinessSpec values."""
        spec = BusinessSpec(niche="general")
        assert spec.supplier == SupplierType.ALIEXPRESS
        assert spec.storefront == StorefrontType.SHOPIFY
        assert spec.fulfillment == FulfillmentType.AUTO
        assert spec.pricing.markup_multiplier == 1.0

    def test_empty_niche_raises_error(self):
        """Test that empty niche raises ValidationError."""
        with pytest.raises(ValidationError):
            BusinessSpec(niche="")

    def test_whitespace_only_niche_raises_error(self):
        """Test that whitespace-only niche raises ValidationError."""
        with pytest.raises(ValidationError):
            BusinessSpec(niche="   ")

    def test_niche_stripped(self):
        """Test that niche is stripped of whitespace."""
        spec = BusinessSpec(niche="  pet supplies  ")
        assert spec.niche == "pet supplies"

    def test_to_dict(self):
        """Test serialization to dict."""
        spec = BusinessSpec(
            niche="test",
            target_market=TargetMarket(countries=["US"]),
        )
        d = spec.to_dict()
        assert d["niche"] == "test"
        assert d["supplier"] == "aliexpress"
        assert d["storefront"] == "shopify"

    def test_str_representation(self):
        """Test string representation."""
        spec = BusinessSpec(
            niche="test",
            supplier=SupplierType.ALIEXPRESS,
            storefront=StorefrontType.SHOPIFY,
            target_market=TargetMarket(countries=["US"]),
            pricing=PricingConfig(markup_multiplier=2.0),
        )
        s = str(spec)
        assert "test" in s
        assert "aliexpress" in s
        assert "shopify" in s
        assert "2.0x" in s

    def test_invalid_pricing_strategy_raises_error(self):
        """Test that invalid pricing strategy raises ValidationError."""
        with pytest.raises(ValidationError):
            BusinessSpec(
                niche="test",
                pricing=PricingConfig(pricing_strategy="invalid_strategy"),
            )


class TestEnums:
    """Tests for enum types."""

    def test_supplier_type_values(self):
        """Test SupplierType enum values."""
        assert SupplierType.ALIEXPRESS.value == "aliexpress"
        assert SupplierType.SPOCKET.value == "spocket"
        assert SupplierType.CJ_DROPSHIPPING.value == "cj_dropsshipping"
        assert SupplierType.DROPSHIPMOBILE.value == "dropshipmobile"
        assert SupplierType.CUSTOM.value == "custom"

    def test_fulfillment_type_values(self):
        """Test FulfillmentType enum values."""
        assert FulfillmentType.AUTO.value == "auto"
        assert FulfillmentType.MANUAL.value == "manual"
        assert FulfillmentType.HYBRID.value == "hybrid"

    def test_storefront_type_values(self):
        """Test StorefrontType enum values."""
        assert StorefrontType.SHOPIFY.value == "shopify"
        assert StorefrontType.WOOCOMMERCE.value == "woocommerce"
        assert StorefrontType.ECOMMERCE_PLATFORM.value == "ecommerce_platform"
        assert StorefrontType.CUSTOM.value == "custom"

    def test_pricing_strategy_values(self):
        """Test PricingStrategy enum values."""
        assert PricingStrategy.MARKUP.value == "markup"
        assert PricingStrategy.COMPETITIVE.value == "competitive"
        assert PricingStrategy.PREMIUM.value == "premium"
