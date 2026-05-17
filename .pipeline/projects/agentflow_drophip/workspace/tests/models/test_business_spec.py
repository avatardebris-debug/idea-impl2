"""Tests for BusinessSpec data model validation."""

import pytest
from pydantic import ValidationError

from agentflow_drophip.models.business_spec import (
    BusinessSpec,
    BrandingConfig,
    FulfillmentType,
    PricingConfig,
    SupplierType,
    StorefrontType,
    TargetMarket,
)


class TestTargetMarket:
    def test_default_target_market(self):
        tm = TargetMarket()
        assert tm.currency == "USD"
        assert tm.language == "en"
        assert tm.countries == []

    def test_target_market_with_countries(self):
        tm = TargetMarket(countries=["US", "CA"], currency="CAD", language="en")
        assert tm.countries == ["US", "CA"]
        assert tm.currency == "CAD"

    def test_empty_countries_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            TargetMarket(countries=[])
        assert "countries" in str(exc_info.value)


class TestPricingConfig:
    def test_default_pricing(self):
        p = PricingConfig()
        assert p.markup_multiplier == 1.0
        assert p.pricing_strategy == "markup"

    def test_custom_pricing(self):
        p = PricingConfig(markup_multiplier=2.5, pricing_strategy="competitive")
        assert p.markup_multiplier == 2.5
        assert p.pricing_strategy == "competitive"

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValidationError):
            PricingConfig(pricing_strategy="invalid_strategy")

    def test_negative_multiplier_raises(self):
        with pytest.raises(ValidationError):
            PricingConfig(markup_multiplier=-1.0)


class TestBrandingConfig:
    def test_default_branding(self):
        b = BrandingConfig()
        assert b.brand_name is None
        assert b.custom_packaging is False

    def test_custom_branding(self):
        b = BrandingConfig(brand_name="MyBrand", custom_packaging=True, color_scheme="blue")
        assert b.brand_name == "MyBrand"
        assert b.custom_packaging is True


class TestBusinessSpec:
    def test_minimal_valid_spec(self):
        spec = BusinessSpec(niche="pet supplies")
        assert spec.niche == "pet supplies"
        assert spec.supplier == SupplierType.ALIEXPRESS
        assert spec.storefront == StorefrontType.SHOPIFY
        assert spec.fulfillment == FulfillmentType.AUTO

    def test_full_spec(self):
        spec = BusinessSpec(
            niche="pet supplies",
            supplier=SupplierType.SPOCKET,
            storefront=StorefrontType.SHOPIFY,
            target_market=TargetMarket(countries=["US", "CA"], currency="USD"),
            pricing=PricingConfig(markup_multiplier=2.5, pricing_strategy="markup"),
            fulfillment=FulfillmentType.AUTO,
            branding=BrandingConfig(brand_name="PetPal", custom_packaging=True),
            description="Premium pet supplies store",
            max_product_cost=50.0,
            min_profit_margin=0.3,
        )
        assert spec.niche == "pet supplies"
        assert spec.supplier == SupplierType.SPOCKET
        assert spec.pricing.markup_multiplier == 2.5
        assert spec.branding.brand_name == "PetPal"

    def test_empty_niche_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            BusinessSpec(niche="")
        assert "niche" in str(exc_info.value)

    def test_whitespace_niche_raises(self):
        with pytest.raises(ValidationError):
            BusinessSpec(niche="   ")

    def test_niche_stripped(self):
        spec = BusinessSpec(niche="  pet supplies  ")
        assert spec.niche == "pet supplies"

    def test_to_dict(self):
        spec = BusinessSpec(niche="test niche")
        d = spec.to_dict()
        assert d["niche"] == "test niche"
        assert "supplier" in d
        assert "pricing" in d

    def test_str_representation(self):
        spec = BusinessSpec(niche="electronics", pricing=PricingConfig(markup_multiplier=3.0))
        s = str(spec)
        assert "electronics" in s
        assert "3.0x" in s

    def test_negative_max_product_cost_raises(self):
        with pytest.raises(ValidationError):
            BusinessSpec(niche="test", max_product_cost=-1.0)

    def test_margin_over_1_raises(self):
        with pytest.raises(ValidationError):
            BusinessSpec(niche="test", min_profit_margin=1.5)
