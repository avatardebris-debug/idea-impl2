"""Tests for Order model."""

import pytest
from dropgentic.models.order import Order


class TestOrderCreation:
    """Test Order instantiation and validation."""

    def test_create_valid_order(self):
        o = Order(
            order_id="O1",
            product_id="P1",
            supplier_id="S1",
            quantity=2,
            unit_cost=10.0,
            total_cost=20.0,
            retail_price=50.0,
        )
        assert o.order_id == "O1"
        assert o.quantity == 2
        assert o.status == "pending"
        assert o.shipping_cost == 0.0
        assert o.platform_fee == 0.0
        assert o.payment_fee == 0.0

    def test_empty_order_id_raises(self):
        with pytest.raises(ValueError, match="order_id must be non-empty"):
            Order(order_id="", product_id="P1", supplier_id="S1", quantity=1, unit_cost=10.0, total_cost=10.0)

    def test_empty_product_id_raises(self):
        with pytest.raises(ValueError, match="product_id must be non-empty"):
            Order(order_id="O1", product_id="", supplier_id="S1", quantity=1, unit_cost=10.0, total_cost=10.0)

    def test_empty_supplier_id_raises(self):
        with pytest.raises(ValueError, match="supplier_id must be non-empty"):
            Order(order_id="O1", product_id="P1", supplier_id="", quantity=1, unit_cost=10.0, total_cost=10.0)

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="quantity must be positive"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=0, unit_cost=10.0, total_cost=10.0)

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="quantity must be positive"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=-1, unit_cost=10.0, total_cost=10.0)

    def test_negative_unit_cost_raises(self):
        with pytest.raises(ValueError, match="unit_cost must be non-negative"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=1, unit_cost=-1.0, total_cost=10.0)

    def test_negative_total_cost_raises(self):
        with pytest.raises(ValueError, match="total_cost must be non-negative"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=1, unit_cost=10.0, total_cost=-1.0)

    def test_negative_shipping_cost_raises(self):
        with pytest.raises(ValueError, match="shipping_cost must be non-negative"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=1, unit_cost=10.0, total_cost=10.0, shipping_cost=-1.0)

    def test_negative_platform_fee_raises(self):
        with pytest.raises(ValueError, match="platform_fee must be non-negative"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=1, unit_cost=10.0, total_cost=10.0, platform_fee=-1.0)

    def test_negative_payment_fee_raises(self):
        with pytest.raises(ValueError, match="payment_fee must be non-negative"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=1, unit_cost=10.0, total_cost=10.0, payment_fee=-1.0)

    def test_negative_retail_price_raises(self):
        with pytest.raises(ValueError, match="retail_price must be non-negative"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=1, unit_cost=10.0, total_cost=10.0, retail_price=-1.0)

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="status must be one of"):
            Order(order_id="O1", product_id="P1", supplier_id="S1", quantity=1, unit_cost=10.0, total_cost=10.0, status="invalid")


class TestOrderProperties:
    """Test Order computed properties."""

    def test_total_fees(self):
        o = Order(
            order_id="O1", product_id="P1", supplier_id="S1",
            quantity=1, unit_cost=10.0, total_cost=10.0,
            platform_fee=5.0, payment_fee=3.0,
        )
        assert o.total_fees == 8.0

    def test_net_profit(self):
        # revenue = 1 * 50 = 50
        # cost = (10 * 1) + 5 + 3 = 18
        # profit = 50 - 18 = 32
        o = Order(
            order_id="O1", product_id="P1", supplier_id="S1",
            quantity=1, unit_cost=10.0, total_cost=10.0,
            shipping_cost=5.0, platform_fee=3.0, payment_fee=0.0,
            retail_price=50.0,
        )
        assert o.net_profit == 32.0

    def test_net_profit_with_quantity(self):
        # revenue = 2 * 50 = 100
        # cost = (10 * 2) + 5 + 3 = 28
        # profit = 100 - 28 = 72
        o = Order(
            order_id="O1", product_id="P1", supplier_id="S1",
            quantity=2, unit_cost=10.0, total_cost=10.0,
            shipping_cost=5.0, platform_fee=3.0, payment_fee=0.0,
            retail_price=50.0,
        )
        assert o.net_profit == 72.0

    def test_net_margin_pct(self):
        # revenue = 1 * 50 = 50
        # profit = 32
        # margin = 32/50 = 0.64
        o = Order(
            order_id="O1", product_id="P1", supplier_id="S1",
            quantity=1, unit_cost=10.0, total_cost=10.0,
            shipping_cost=5.0, platform_fee=3.0, payment_fee=0.0,
            retail_price=50.0,
        )
        assert o.net_margin_pct == pytest.approx(0.64)

    def test_net_margin_pct_zero_revenue(self):
        o = Order(
            order_id="O1", product_id="P1", supplier_id="S1",
            quantity=1, unit_cost=10.0, total_cost=10.0,
            retail_price=0.0,
        )
        assert o.net_margin_pct == 0.0

    def test_net_margin_pct_zero_quantity(self):
        # Can't create with quantity=0, so test with retail_price=0
        o = Order(
            order_id="O1", product_id="P1", supplier_id="S1",
            quantity=1, unit_cost=10.0, total_cost=10.0,
            retail_price=0.0,
        )
        assert o.net_margin_pct == 0.0


class TestOrderSerialization:
    """Test Order serialization methods."""

    def test_to_dict(self):
        o = Order(
            order_id="O1", product_id="P1", supplier_id="S1",
            quantity=2, unit_cost=10.0, total_cost=20.0,
            shipping_cost=5.0, platform_fee=3.0, payment_fee=1.0,
            retail_price=50.0, status="shipped",
        )
        d = o.to_dict()
        assert d["order_id"] == "O1"
        assert d["quantity"] == 2
        assert d["status"] == "shipped"
        assert d["shipping_cost"] == 5.0

    def test_from_dict(self):
        data = {
            "order_id": "O1", "product_id": "P1", "supplier_id": "S1",
            "quantity": 3, "unit_cost": 15.0, "total_cost": 45.0,
            "retail_price": 60.0,
        }
        o = Order.from_dict(data)
        assert o.order_id == "O1"
        assert o.quantity == 3
        assert o.unit_cost == 15.0

    def test_from_dict_with_extra_fields(self):
        data = {
            "order_id": "O1", "product_id": "P1", "supplier_id": "S1",
            "quantity": 1, "unit_cost": 10.0, "total_cost": 10.0,
            "retail_price": 50.0, "extra_field": "ignored",
        }
        o = Order.from_dict(data)
        assert o.order_id == "O1"
        assert o.extra_field == "ignored"

    def test_repr(self):
        o = Order(
            order_id="O1", product_id="P1", supplier_id="S1",
            quantity=2, unit_cost=10.0, total_cost=20.0,
            retail_price=50.0,
        )
        r = repr(o)
        assert "O1" in r
        assert "P1" in r
        assert "qty=2" in r
        assert "pending" in r
