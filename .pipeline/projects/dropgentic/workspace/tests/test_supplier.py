"""Tests for the Supplier model."""

import pytest
from dropgentic.models.supplier import Supplier


class TestSupplierInit:
    """Tests for Supplier initialization and validation."""

    def test_valid_supplier(self):
        """Test creating a valid supplier."""
        supplier = Supplier(
            supplier_id="S001",
            name="Test Supplier",
        )
        assert supplier.supplier_id == "S001"
        assert supplier.name == "Test Supplier"
        assert supplier.base_url == ""
        assert supplier.rating == 0.0
        assert supplier.shipping_cost_per_unit == 0.0
        assert supplier.shipping_weight_factor == 0.0
        assert supplier.min_order_quantity == 0
        assert supplier.max_order_quantity == 0
        assert supplier.lead_time_days == 0
        assert supplier.supported_currencies == []
        assert supplier.active is True
        assert supplier.categories == []
        assert supplier.raw == {}

    def test_empty_supplier_id_raises(self):
        """Test that empty supplier_id raises ValueError."""
        with pytest.raises(ValueError, match="supplier_id must be non-empty"):
            Supplier(supplier_id="", name="Test")

    def test_whitespace_supplier_id_raises(self):
        """Test that whitespace-only supplier_id raises ValueError."""
        with pytest.raises(ValueError, match="supplier_id must be non-empty"):
            Supplier(supplier_id="   ", name="Test")

    def test_empty_name_raises(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name must be non-empty"):
            Supplier(supplier_id="S001", name="")

    def test_whitespace_name_raises(self):
        """Test that whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="name must be non-empty"):
            Supplier(supplier_id="S001", name="   ")

    def test_invalid_rating_raises(self):
        """Test that invalid rating raises ValueError."""
        with pytest.raises(ValueError, match="rating must be a number"):
            Supplier(supplier_id="S001", name="Test", rating="high")

    def test_rating_below_zero_raises(self):
        """Test that rating below zero raises ValueError."""
        with pytest.raises(ValueError, match="rating must be between 0 and 5"):
            Supplier(supplier_id="S001", name="Test", rating=-0.1)

    def test_rating_above_five_raises(self):
        """Test that rating above five raises ValueError."""
        with pytest.raises(ValueError, match="rating must be between 0 and 5"):
            Supplier(supplier_id="S001", name="Test", rating=5.1)

    def test_rating_zero_allowed(self):
        """Test that rating of 0 is allowed."""
        supplier = Supplier(supplier_id="S001", name="Test", rating=0.0)
        assert supplier.rating == 0.0

    def test_rating_five_allowed(self):
        """Test that rating of 5 is allowed."""
        supplier = Supplier(supplier_id="S001", name="Test", rating=5.0)
        assert supplier.rating == 5.0

    def test_negative_shipping_cost_raises(self):
        """Test that negative shipping_cost_per_unit raises ValueError."""
        with pytest.raises(ValueError, match="shipping_cost_per_unit must be non-negative"):
            Supplier(supplier_id="S001", name="Test", shipping_cost_per_unit=-1.0)

    def test_negative_weight_factor_raises(self):
        """Test that negative shipping_weight_factor raises ValueError."""
        with pytest.raises(ValueError, match="shipping_weight_factor must be non-negative"):
            Supplier(supplier_id="S001", name="Test", shipping_weight_factor=-1.0)

    def test_negative_lead_time_raises(self):
        """Test that negative lead_time_days raises ValueError."""
        with pytest.raises(ValueError, match="lead_time_days must be non-negative"):
            Supplier(supplier_id="S001", name="Test", lead_time_days=-1)

    def test_all_fields(self):
        """Test creating a supplier with all fields."""
        supplier = Supplier(
            supplier_id="S001",
            name="Full Supplier",
            base_url="https://example.com",
            rating=4.5,
            shipping_cost_per_unit=5.0,
            shipping_weight_factor=2.0,
            min_order_quantity=10,
            max_order_quantity=1000,
            lead_time_days=7,
            supported_currencies=["USD", "EUR"],
            active=False,
            categories=["Electronics", "Accessories"],
            raw={"extra": "data"},
        )
        assert supplier.base_url == "https://example.com"
        assert supplier.rating == 4.5
        assert supplier.shipping_cost_per_unit == 5.0
        assert supplier.shipping_weight_factor == 2.0
        assert supplier.min_order_quantity == 10
        assert supplier.max_order_quantity == 1000
        assert supplier.lead_time_days == 7
        assert supplier.supported_currencies == ["USD", "EUR"]
        assert supplier.active is False
        assert supplier.categories == ["Electronics", "Accessories"]
        assert supplier.raw == {"extra": "data"}


class TestSupplierToDict:
    """Tests for the to_dict method."""

    def test_to_dict_basic(self):
        """Test to_dict with basic supplier."""
        supplier = Supplier(supplier_id="S001", name="Test")
        result = supplier.to_dict()
        assert result["supplier_id"] == "S001"
        assert result["name"] == "Test"
        assert result["base_url"] == ""
        assert result["rating"] == 0.0
        assert result["active"] is True

    def test_to_dict_includes_all_fields(self):
        """Test to_dict includes all fields."""
        supplier = Supplier(
            supplier_id="S001",
            name="Full",
            base_url="https://example.com",
            rating=4.5,
            shipping_cost_per_unit=5.0,
            shipping_weight_factor=2.0,
            min_order_quantity=10,
            max_order_quantity=1000,
            lead_time_days=7,
            supported_currencies=["USD"],
            active=False,
            categories=["Cat"],
            raw={"r": 1},
        )
        result = supplier.to_dict()
        assert result["base_url"] == "https://example.com"
        assert result["rating"] == 4.5
        assert result["shipping_cost_per_unit"] == 5.0
        assert result["shipping_weight_factor"] == 2.0
        assert result["min_order_quantity"] == 10
        assert result["max_order_quantity"] == 1000
        assert result["lead_time_days"] == 7
        assert result["supported_currencies"] == ["USD"]
        assert result["active"] is False
        assert result["categories"] == ["Cat"]
        assert result["raw"] == {"r": 1}


class TestSupplierFromDict:
    """Tests for the from_dict class method."""

    def test_from_dict_basic(self):
        """Test from_dict with basic data."""
        data = {
            "supplier_id": "S001",
            "name": "Test",
        }
        supplier = Supplier.from_dict(data)
        assert supplier.supplier_id == "S001"
        assert supplier.name == "Test"

    def test_from_dict_with_all_fields(self):
        """Test from_dict with all fields."""
        data = {
            "supplier_id": "S001",
            "name": "Full",
            "base_url": "https://example.com",
            "rating": 4.5,
            "shipping_cost_per_unit": 5.0,
            "shipping_weight_factor": 2.0,
            "min_order_quantity": 10,
            "max_order_quantity": 1000,
            "lead_time_days": 7,
            "supported_currencies": ["USD"],
            "active": False,
            "categories": ["Cat"],
            "raw": {"r": 1},
        }
        supplier = Supplier.from_dict(data)
        assert supplier.base_url == "https://example.com"
        assert supplier.rating == 4.5
        assert supplier.shipping_cost_per_unit == 5.0
        assert supplier.shipping_weight_factor == 2.0
        assert supplier.min_order_quantity == 10
        assert supplier.max_order_quantity == 1000
        assert supplier.lead_time_days == 7
        assert supplier.supported_currencies == ["USD"]
        assert supplier.active is False
        assert supplier.categories == ["Cat"]
        assert supplier.raw == {"r": 1}


class TestSupplierRepr:
    """Tests for the __repr__ method."""

    def test_repr(self):
        """Test __repr__ output."""
        supplier = Supplier(supplier_id="S001", name="Test Supplier", rating=4.5)
        repr_str = repr(supplier)
        assert "S001" in repr_str
        assert "Test Supplier" in repr_str
        assert "4.5" in repr_str