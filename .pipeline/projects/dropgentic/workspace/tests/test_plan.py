"""Tests for Product model."""

import pytest
from dropgentic.models.product import Product


class TestProductCreation:
    """Test Product instantiation and validation."""

    def test_create_valid_product(self):
        p = Product(product_id="P1", title="Widget", cost_price=10.0, retail_price=25.0)
        assert p.product_id == "P1"
        assert p.title == "Widget"
        assert p.cost_price == 10.0
        assert p.retail_price == 25.0

    def test_empty_product_id_raises(self):
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            Product(product_id="", title="X", cost_price=1.0, retail_price=2.0)

    def test_negative_cost_price_raises(self):
        with pytest.raises(ValueError, match="cost_price must be non-negative"):
            Product(product_id="P1", title="X", cost_price=-1.0, retail_price=2.0)

    def test_negative_retail_price_raises(self):
        with pytest.raises(ValueError, match="retail_price must be non-negative"):
            Product(product_id="P1", title="X", cost_price=1.0, retail_price=-2.0)

    def test_retail_below_cost_raises(self):
        with pytest.raises(ValueError, match="retail_price.*must be >= cost_price"):
            Product(product_id="P1", title="X", cost_price=25.0, retail_price=10.0)

    def test_default_values(self):
        p = Product(product_id="P1", title="X", cost_price=10.0, retail_price=20.0)
        assert p.category == ""
        assert p.sku == ""
        assert p.weight_kg == 0.0
        assert p.dimensions_cm == {}
        assert p.image_url == ""
        assert p.description == ""
        assert p.tags == []
        assert p.raw == {}


class TestProductProperties:
    """Test Product computed properties."""

    def test_gross_margin(self):
        p = Product(product_id="P1", title="X", cost_price=10.0, retail_price=25.0)
        assert p.gross_margin == pytest.approx(0.6)  # 60%

    def test_gross_margin_zero(self):
        p = Product(product_id="P1", title="X", cost_price=10.0, retail_price=10.0)
        assert p.gross_margin == 0.0

    def test_gross_margin_zero_retail(self):
        p = Product(product_id="P1", title="X", cost_price=0.0, retail_price=0.0)
        assert p.gross_margin == 0.0


class TestProductSerialization:
    """Test Product serialization."""

    def test_to_dict(self):
        p = Product(product_id="P1", title="X", cost_price=10.0, retail_price=25.0)
        d = p.to_dict()
        assert d["product_id"] == "P1"
        assert d["gross_margin"] == pytest.approx(0.6)

    def test_from_dict(self):
        d = {
            "product_id": "P1",
            "title": "X",
            "cost_price": 10.0,
            "retail_price": 25.0,
            "gross_margin": 0.6,  # should be ignored
        }
        p = Product.from_dict(d)
        assert p.product_id == "P1"
        assert p.gross_margin == pytest.approx(0.6)

    def test_repr(self):
        p = Product(product_id="P1", title="X", cost_price=10.0, retail_price=25.0)
        r = repr(p)
        assert "P1" in r
        assert "X" in r
