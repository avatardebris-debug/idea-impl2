"""Tests for the Product model."""

import pytest
from dropgentic.models.product import Product


class TestProductInit:
    """Tests for Product initialization and validation."""

    def test_valid_product(self):
        """Test creating a valid product."""
        product = Product(
            product_id="P001",
            title="Test Product",
            cost_price=10.0,
            retail_price=20.0,
        )
        assert product.product_id == "P001"
        assert product.title == "Test Product"
        assert product.cost_price == 10.0
        assert product.retail_price == 20.0
        assert product.category == ""
        assert product.sku == ""
        assert product.weight_kg == 0.0
        assert product.dimensions_cm == {}
        assert product.image_url == ""
        assert product.description == ""
        assert product.tags == []
        assert product.raw == {}

    def test_empty_product_id_raises(self):
        """Test that empty product_id raises ValueError."""
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            Product(product_id="", title="Test", cost_price=10.0, retail_price=20.0)

    def test_whitespace_product_id_raises(self):
        """Test that whitespace-only product_id raises ValueError."""
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            Product(product_id="   ", title="Test", cost_price=10.0, retail_price=20.0)

    def test_negative_cost_price_raises(self):
        """Test that negative cost_price raises ValueError."""
        with pytest.raises(ValueError, match="cost_price must be non-negative"):
            Product(product_id="P001", title="Test", cost_price=-1.0, retail_price=20.0)

    def test_negative_retail_price_raises(self):
        """Test that negative retail_price raises ValueError."""
        with pytest.raises(ValueError, match="retail_price must be non-negative"):
            Product(product_id="P001", title="Test", cost_price=10.0, retail_price=-1.0)

    def test_retail_less_than_cost_raises(self):
        """Test that retail_price < cost_price raises ValueError."""
        with pytest.raises(ValueError, match="retail_price must be >= cost_price"):
            Product(product_id="P001", title="Test", cost_price=20.0, retail_price=10.0)

    def test_retail_equal_to_cost_allowed(self):
        """Test that retail_price == cost_price is allowed."""
        product = Product(product_id="P001", title="Test", cost_price=10.0, retail_price=10.0)
        assert product.retail_price == 10.0

    def test_cost_price_zero_allowed(self):
        """Test that cost_price of 0 is allowed."""
        product = Product(product_id="P001", title="Test", cost_price=0.0, retail_price=10.0)
        assert product.cost_price == 0.0

    def test_retail_price_zero_allowed(self):
        """Test that retail_price of 0 is allowed."""
        product = Product(product_id="P001", title="Test", cost_price=0.0, retail_price=0.0)
        assert product.retail_price == 0.0

    def test_string_cost_price_raises(self):
        """Test that string cost_price raises ValueError."""
        with pytest.raises(ValueError, match="cost_price must be a number"):
            Product(product_id="P001", title="Test", cost_price="10", retail_price=20.0)

    def test_string_retail_price_raises(self):
        """Test that string retail_price raises ValueError."""
        with pytest.raises(ValueError, match="retail_price must be a number"):
            Product(product_id="P001", title="Test", cost_price=10.0, retail_price="20")

    def test_integer_cost_price_allowed(self):
        """Test that integer cost_price is allowed."""
        product = Product(product_id="P001", title="Test", cost_price=10, retail_price=20)
        assert product.cost_price == 10

    def test_integer_retail_price_allowed(self):
        """Test that integer retail_price is allowed."""
        product = Product(product_id="P001", title="Test", cost_price=10, retail_price=20)
        assert product.retail_price == 20

    def test_all_fields(self):
        """Test creating a product with all fields."""
        product = Product(
            product_id="P001",
            title="Full Product",
            cost_price=10.0,
            retail_price=20.0,
            category="Electronics",
            sku="SKU-001",
            weight_kg=1.5,
            dimensions_cm={"length": 10, "width": 20, "height": 30},
            image_url="http://example.com/img.jpg",
            description="A test product",
            tags=["test", "demo"],
            raw={"extra": "data"},
        )
        assert product.category == "Electronics"
        assert product.sku == "SKU-001"
        assert product.weight_kg == 1.5
        assert product.dimensions_cm == {"length": 10, "width": 20, "height": 30}
        assert product.image_url == "http://example.com/img.jpg"
        assert product.description == "A test product"
        assert product.tags == ["test", "demo"]
        assert product.raw == {"extra": "data"}


class TestProductGrossMargin:
    """Tests for the gross_margin property."""

    def test_gross_margin_positive(self):
        """Test gross_margin with positive margin."""
        product = Product(product_id="P001", title="Test", cost_price=10.0, retail_price=20.0)
        assert product.gross_margin == 0.5

    def test_gross_margin_zero(self):
        """Test gross_margin when retail equals cost."""
        product = Product(product_id="P001", title="Test", cost_price=10.0, retail_price=10.0)
        assert product.gross_margin == 0.0

    def test_gross_margin_zero_retail(self):
        """Test gross_margin when retail_price is zero."""
        product = Product(product_id="P001", title="Test", cost_price=0.0, retail_price=0.0)
        assert product.gross_margin == 0.0

    def test_gross_margin_high(self):
        """Test gross_margin with high margin."""
        product = Product(product_id="P001", title="Test", cost_price=1.0, retail_price=100.0)
        assert product.gross_margin == 0.99

    def test_gross_margin_small(self):
        """Test gross_margin with small margin."""
        product = Product(product_id="P001", title="Test", cost_price=9.9, retail_price=10.0)
        assert product.gross_margin == pytest.approx(0.01)


class TestProductToDict:
    """Tests for the to_dict method."""

    def test_to_dict_basic(self):
        """Test to_dict with basic product."""
        product = Product(product_id="P001", title="Test", cost_price=10.0, retail_price=20.0)
        result = product.to_dict()
        assert result["product_id"] == "P001"
        assert result["title"] == "Test"
        assert result["cost_price"] == 10.0
        assert result["retail_price"] == 20.0
        assert result["gross_margin"] == 0.5

    def test_to_dict_includes_all_fields(self):
        """Test to_dict includes all fields."""
        product = Product(
            product_id="P001",
            title="Full",
            cost_price=10.0,
            retail_price=20.0,
            category="Cat",
            sku="SKU",
            weight_kg=1.0,
            dimensions_cm={"l": 1},
            image_url="http://x.com",
            description="Desc",
            tags=["t"],
            raw={"r": 1},
        )
        result = product.to_dict()
        assert result["category"] == "Cat"
        assert result["sku"] == "SKU"
        assert result["weight_kg"] == 1.0
        assert result["dimensions_cm"] == {"l": 1}
        assert result["image_url"] == "http://x.com"
        assert result["description"] == "Desc"
        assert result["tags"] == ["t"]
        assert result["raw"] == {"r": 1}


class TestProductFromDict:
    """Tests for the from_dict class method."""

    def test_from_dict_basic(self):
        """Test from_dict with basic data."""
        data = {
            "product_id": "P001",
            "title": "Test",
            "cost_price": 10.0,
            "retail_price": 20.0,
        }
        product = Product.from_dict(data)
        assert product.product_id == "P001"
        assert product.title == "Test"
        assert product.cost_price == 10.0
        assert product.retail_price == 20.0

    def test_from_dict_with_gross_margin_excluded(self):
        """Test that gross_margin in data is excluded."""
        data = {
            "product_id": "P001",
            "title": "Test",
            "cost_price": 10.0,
            "retail_price": 20.0,
            "gross_margin": 0.5,
        }
        product = Product.from_dict(data)
        assert product.product_id == "P001"
        assert product.gross_margin == 0.5

    def test_from_dict_with_all_fields(self):
        """Test from_dict with all fields."""
        data = {
            "product_id": "P001",
            "title": "Full",
            "cost_price": 10.0,
            "retail_price": 20.0,
            "category": "Cat",
            "sku": "SKU",
            "weight_kg": 1.0,
            "dimensions_cm": {"l": 1},
            "image_url": "http://x.com",
            "description": "Desc",
            "tags": ["t"],
            "raw": {"r": 1},
        }
        product = Product.from_dict(data)
        assert product.category == "Cat"
        assert product.sku == "SKU"
        assert product.weight_kg == 1.0
        assert product.dimensions_cm == {"l": 1}
        assert product.image_url == "http://x.com"
        assert product.description == "Desc"
        assert product.tags == ["t"]
        assert product.raw == {"r": 1}


class TestProductRepr:
    """Tests for the __repr__ method."""

    def test_repr(self):
        """Test __repr__ output."""
        product = Product(product_id="P001", title="Test Product", cost_price=10.0, retail_price=20.0)
        repr_str = repr(product)
        assert "P001" in repr_str
        assert "Test Product" in repr_str
        assert "10.0" in repr_str
        assert "20.0" in repr_str