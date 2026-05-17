"""Tests for droppain.models module."""

import pytest

from droppain.models import Product, Variant


class TestProduct:
    """Tests for the Product model."""

    def test_product_creation(self):
        """Test basic product creation."""
        product = Product(id="1", title="Test Product", price=29.99)
        assert product.id == "1"
        assert product.title == "Test Product"
        assert product.price == 29.99
        assert product.tags == []
        assert product.variants == []
        assert product.status == "active"

    def test_display_price(self):
        """Test formatted price."""
        product = Product(id="1", title="Test", price=29.99)
        assert product.display_price == "$29.99"

    def test_display_price_rounding(self):
        """Test price rounding."""
        product = Product(id="1", title="Test", price=29.999)
        assert product.display_price == "$30.00"

    def test_is_available_active_with_variants(self):
        """Test is_available returns True for active product with variants."""
        product = Product(
            id="1", title="Test", price=10.0,
            status="active",
            variants=[Variant(id="v1", title="Default", price=10.0)],
        )
        assert product.is_available is True

    def test_is_available_inactive(self):
        """Test is_available returns False for inactive product."""
        product = Product(id="1", title="Test", price=10.0, status="draft")
        assert product.is_available is False

    def test_is_available_no_variants(self):
        """Test is_available returns False for active product with no variants."""
        product = Product(id="1", title="Test", price=10.0, status="active", variants=[])
        assert product.is_available is False

    def test_to_dict(self):
        """Test to_dict serialization."""
        product = Product(id="1", title="Test", price=29.99, tags=["a", "b"])
        d = product.to_dict()
        assert d["id"] == "1"
        assert d["title"] == "Test"
        assert d["price"] == 29.99
        assert d["tags"] == ["a", "b"]
        assert "variants" in d

    def test_from_dict(self):
        """Test from_dict deserialization."""
        d = {
            "id": "1",
            "title": "Test",
            "price": 29.99,
            "tags": ["a", "b"],
            "variants": [{"id": "v1", "title": "Small", "price": 25.0}],
        }
        product = Product.from_dict(d)
        assert product.id == "1"
        assert product.title == "Test"
        assert product.price == 29.99
        assert product.tags == ["a", "b"]
        assert len(product.variants) == 1
        assert product.variants[0].title == "Small"


class TestVariant:
    """Tests for the Variant model."""

    def test_variant_creation(self):
        """Test basic variant creation."""
        variant = Variant(id="v1", title="Small", price=25.0)
        assert variant.id == "v1"
        assert variant.title == "Small"
        assert variant.price == 25.0
        assert variant.sku == ""
        assert variant.inventory_quantity == 0
        assert variant.available is True

    def test_variant_display_price(self):
        """Test formatted price."""
        variant = Variant(id="v1", title="Small", price=25.0)
        assert variant.display_price == "$25.00"

    def test_variant_to_dict(self):
        """Test to_dict serialization."""
        variant = Variant(id="v1", title="Small", price=25.0, sku="SKU123")
        d = variant.to_dict()
        assert d["id"] == "v1"
        assert d["title"] == "Small"
        assert d["price"] == 25.0
        assert d["sku"] == "SKU123"

    def test_variant_from_dict(self):
        """Test from_dict deserialization."""
        d = {"id": "v1", "title": "Small", "price": 25.0, "sku": "SKU123"}
        variant = Variant.from_dict(d)
        assert variant.id == "v1"
        assert variant.title == "Small"
        assert variant.price == 25.0
        assert variant.sku == "SKU123"
