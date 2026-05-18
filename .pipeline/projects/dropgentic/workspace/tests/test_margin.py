"""Tests for the Margin model."""

import pytest
from dropgentic.models.margin import MarginResult, MarginCalculator


class TestMarginResultInit:
    """Tests for MarginResult initialization."""

    def test_margin_result_with_defaults(self):
        """Test creating a MarginResult with default values for optional fields."""
        result = MarginResult(
            cost_price=10.0,
            shipping_cost=5.0,
            total_cost=15.0,
            retail_price=30.0,
            gross_profit=15.0,
            gross_margin_pct=0.5,
            net_margin_pct=0.3,
            recommended_action="List",
        )
        assert result.cost_price == 10.0
        assert result.shipping_cost == 5.0
        assert result.total_cost == 15.0
        assert result.retail_price == 30.0
        assert result.gross_profit == 15.0
        assert result.gross_margin_pct == 0.5
        assert result.net_margin_pct == 0.3
        assert result.recommended_action == "List"
        assert result.platform_fee == 0.0
        assert result.payment_fee == 0.0
        assert result.total_fees == 0.0
        assert result.net_profit == 0.0
        assert result.currency == "USD"

    def test_margin_result_with_all_fields(self):
        """Test creating a MarginResult with all fields."""
        result = MarginResult(
            cost_price=10.0,
            shipping_cost=5.0,
            total_cost=15.0,
            retail_price=30.0,
            gross_profit=15.0,
            gross_margin_pct=0.5,
            net_margin_pct=0.3,
            recommended_action="List",
            platform_fee=4.5,
            payment_fee=1.17,
            total_fees=5.67,
            net_profit=9.33,
            currency="EUR",
        )
        assert result.platform_fee == 4.5
        assert result.payment_fee == 1.17
        assert result.total_fees == 5.67
        assert result.net_profit == 9.33
        assert result.currency == "EUR"


class TestMarginResultToDict:
    """Tests for the to_dict method."""

    def test_to_dict_basic(self):
        """Test to_dict with basic MarginResult."""
        result = MarginResult(
            cost_price=10.0,
            shipping_cost=5.0,
            total_cost=15.0,
            retail_price=30.0,
            gross_profit=15.0,
            gross_margin_pct=0.5,
            net_margin_pct=0.3,
            recommended_action="List",
        )
        data = result.to_dict()
        assert data["cost_price"] == 10.0
        assert data["shipping_cost"] == 5.0
        assert data["total_cost"] == 15.0
        assert data["retail_price"] == 30.0
        assert data["gross_profit"] == 15.0
        assert data["gross_margin_pct"] == 0.5
        assert data["net_margin_pct"] == 0.3
        assert data["recommended_action"] == "List"
        assert data["platform_fee"] == 0.0
        assert data["payment_fee"] == 0.0
        assert data["total_fees"] == 0.0
        assert data["net_profit"] == 0.0
        assert data["currency"] == "USD"

    def test_to_dict_with_all_fields(self):
        """Test to_dict includes all fields."""
        result = MarginResult(
            cost_price=10.0,
            shipping_cost=5.0,
            total_cost=15.0,
            retail_price=30.0,
            gross_profit=15.0,
            gross_margin_pct=0.5,
            net_margin_pct=0.3,
            recommended_action="List",
            platform_fee=4.5,
            payment_fee=1.17,
            total_fees=5.67,
            net_profit=9.33,
            currency="EUR",
        )
        data = result.to_dict()
        assert data["platform_fee"] == 4.5
        assert data["payment_fee"] == 1.17
        assert data["total_fees"] == 5.67
        assert data["net_profit"] == 9.33
        assert data["currency"] == "EUR"


class TestMarginResultFromDict:
    """Tests for the from_dict class method."""

    def test_from_dict_basic(self):
        """Test from_dict with basic data."""
        data = {
            "cost_price": 10.0,
            "shipping_cost": 5.0,
            "total_cost": 15.0,
            "retail_price": 30.0,
            "gross_profit": 15.0,
            "gross_margin_pct": 0.5,
            "net_margin_pct": 0.3,
            "recommended_action": "List",
        }
        result = MarginResult.from_dict(data)
        assert result.cost_price == 10.0
        assert result.shipping_cost == 5.0
        assert result.total_cost == 15.0
        assert result.retail_price == 30.0
        assert result.gross_profit == 15.0
        assert result.gross_margin_pct == 0.5
        assert result.net_margin_pct == 0.3
        assert result.recommended_action == "List"

    def test_from_dict_with_all_fields(self):
        """Test from_dict with all fields."""
        data = {
            "cost_price": 10.0,
            "shipping_cost": 5.0,
            "total_cost": 15.0,
            "retail_price": 30.0,
            "gross_profit": 15.0,
            "gross_margin_pct": 0.5,
            "net_margin_pct": 0.3,
            "recommended_action": "List",
            "platform_fee": 4.5,
            "payment_fee": 1.17,
            "total_fees": 5.67,
            "net_profit": 9.33,
            "currency": "EUR",
        }
        result = MarginResult.from_dict(data)
        assert result.platform_fee == 4.5
        assert result.payment_fee == 1.17
        assert result.total_fees == 5.67
        assert result.net_profit == 9.33
        assert result.currency == "EUR"


class TestMarginResultRepr:
    """Tests for the __repr__ method."""

    def test_repr(self):
        """Test __repr__ output."""
        result = MarginResult(
            cost_price=10.0,
            shipping_cost=5.0,
            total_cost=15.0,
            retail_price=30.0,
            gross_profit=15.0,
            gross_margin_pct=0.5,
            net_margin_pct=0.3,
            recommended_action="List",
        )
        repr_str = repr(result)
        assert "10.0" in repr_str
        assert "30.0" in repr_str
        assert "50.00%" in repr_str
        assert "30.00%" in repr_str


class TestMarginCalculatorInit:
    """Tests for MarginCalculator initialization."""

    def test_default_values(self):
        """Test default values for MarginCalculator."""
        calculator = MarginCalculator()
        assert calculator.platform_fee_pct == 0.15
        assert calculator.payment_processing_fee_pct == 0.029
        assert calculator.fixed_payment_fee == 0.30
        assert calculator.currency == "USD"

    def test_custom_values(self):
        """Test custom values for MarginCalculator."""
        calculator = MarginCalculator(
            platform_fee_pct=0.10,
            payment_processing_fee_pct=0.025,
            fixed_payment_fee=0.20,
            currency="EUR",
        )
        assert calculator.platform_fee_pct == 0.10
        assert calculator.payment_processing_fee_pct == 0.025
        assert calculator.fixed_payment_fee == 0.20
        assert calculator.currency == "EUR"


class TestMarginCalculatorCalculateShipping:
    """Tests for the calculate_shipping method."""

    def test_calculate_shipping_basic(self):
        """Test basic shipping cost calculation."""
        calculator = MarginCalculator()
        cost = calculator.calculate_shipping(weight_kg=1.0, supplier_shipping_cost_per_unit=5.0, supplier_shipping_weight_factor=2.0)
        assert cost == 7.0  # 5.0 + 1.0 * 2.0

    def test_calculate_shipping_zero_weight(self):
        """Test shipping cost with zero weight."""
        calculator = MarginCalculator()
        cost = calculator.calculate_shipping(weight_kg=0.0, supplier_shipping_cost_per_unit=5.0, supplier_shipping_weight_factor=2.0)
        assert cost == 5.0

    def test_calculate_shipping_zero_supplier_cost(self):
        """Test shipping cost with zero supplier cost."""
        calculator = MarginCalculator()
        cost = calculator.calculate_shipping(weight_kg=1.0, supplier_shipping_cost_per_unit=0.0, supplier_shipping_weight_factor=2.0)
        assert cost == 2.0

    def test_calculate_shipping_zero_weight_factor(self):
        """Test shipping cost with zero weight factor."""
        calculator = MarginCalculator()
        cost = calculator.calculate_shipping(weight_kg=1.0, supplier_shipping_cost_per_unit=5.0, supplier_shipping_weight_factor=0.0)
        assert cost == 5.0

    def test_calculate_shipping_negative_weight_raises(self):
        """Test that negative weight raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="weight_kg must be non-negative"):
            calculator.calculate_shipping(weight_kg=-1.0, supplier_shipping_cost_per_unit=5.0, supplier_shipping_weight_factor=2.0)

    def test_calculate_shipping_negative_supplier_cost_raises(self):
        """Test that negative supplier cost raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="supplier_shipping_cost_per_unit must be non-negative"):
            calculator.calculate_shipping(weight_kg=1.0, supplier_shipping_cost_per_unit=-1.0, supplier_shipping_weight_factor=2.0)

    def test_calculate_shipping_negative_weight_factor_raises(self):
        """Test that negative weight factor raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="supplier_shipping_weight_factor must be non-negative"):
            calculator.calculate_shipping(weight_kg=1.0, supplier_shipping_cost_per_unit=5.0, supplier_shipping_weight_factor=-1.0)


class TestMarginCalculatorCalculatePlatformFee:
    """Tests for the calculate_platform_fee method."""

    def test_calculate_platform_fee_basic(self):
        """Test basic platform fee calculation."""
        calculator = MarginCalculator()
        fee = calculator.calculate_platform_fee(retail_price=100.0)
        assert fee == 15.0  # 100.0 * 0.15

    def test_calculate_platform_fee_zero_retail(self):
        """Test platform fee with zero retail price."""
        calculator = MarginCalculator()
        fee = calculator.calculate_platform_fee(retail_price=0.0)
        assert fee == 0.0

    def test_calculate_platform_fee_custom_rate(self):
        """Test platform fee with custom rate."""
        calculator = MarginCalculator(platform_fee_pct=0.10)
        fee = calculator.calculate_platform_fee(retail_price=100.0)
        assert fee == 10.0

    def test_calculate_platform_fee_negative_raises(self):
        """Test that negative retail price raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="retail_price must be non-negative"):
            calculator.calculate_platform_fee(retail_price=-1.0)


class TestMarginCalculatorCalculatePaymentFee:
    """Tests for the calculate_payment_fee method."""

    def test_calculate_payment_fee_basic(self):
        """Test basic payment fee calculation."""
        calculator = MarginCalculator()
        fee = calculator.calculate_payment_fee(retail_price=100.0)
        assert fee == pytest.approx(3.2)  # 100.0 * 0.029 + 0.30

    def test_calculate_payment_fee_zero_retail(self):
        """Test payment fee with zero retail price."""
        calculator = MarginCalculator()
        fee = calculator.calculate_payment_fee(retail_price=0.0)
        assert fee == 0.30  # Only fixed fee

    def test_calculate_payment_fee_custom_rates(self):
        """Test payment fee with custom rates."""
        calculator = MarginCalculator(
            payment_processing_fee_pct=0.025,
            fixed_payment_fee=0.20,
        )
        fee = calculator.calculate_payment_fee(retail_price=100.0)
        assert fee == pytest.approx(2.7)  # 100.0 * 0.025 + 0.20

    def test_calculate_payment_fee_negative_raises(self):
        """Test that negative retail price raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="retail_price must be non-negative"):
            calculator.calculate_payment_fee(retail_price=-1.0)


class TestMarginCalculatorRecommendAction:
    """Tests for the _recommend_action method."""

    def test_reject_low_gross_margin(self):
        """Test rejection with low gross margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.05, net_margin_pct=0.02)
        assert action == "Reject"

    def test_review_medium_gross_margin(self):
        """Test review with medium gross margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.20, net_margin_pct=0.10)
        assert action == "Review"

    def test_list_high_gross_margin(self):
        """Test listing with high gross margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.50, net_margin_pct=0.30)
        assert action == "List"

    def test_reject_boundary_gross_margin(self):
        """Test rejection at boundary gross margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.15, net_margin_pct=0.10)
        assert action == "Review"

    def test_review_boundary_gross_margin(self):
        """Test review at boundary gross margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.20, net_margin_pct=0.10)
        assert action == "Review"

    def test_list_boundary_gross_margin(self):
        """Test listing at boundary gross margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.25, net_margin_pct=0.10)
        assert action == "Review"

    def test_reject_low_net_margin(self):
        """Test rejection with low net margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.30, net_margin_pct=0.05)
        assert action == "Reject"

    def test_review_medium_net_margin(self):
        """Test review with medium net margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.30, net_margin_pct=0.10)
        assert action == "Review"

    def test_list_high_net_margin(self):
        """Test listing with high net margin."""
        calculator = MarginCalculator()
        action = calculator._recommend_action(gross_margin_pct=0.30, net_margin_pct=0.15)
        assert action == "List"


class TestMarginCalculatorCalculate:
    """Tests for the calculate method."""

    def test_calculate_basic(self):
        """Test basic margin calculation."""
        calculator = MarginCalculator()
        result = calculator.calculate(
            cost_price=10.0,
            shipping_cost=5.0,
            retail_price=30.0,
        )
        assert isinstance(result, MarginResult)
        assert result.cost_price == 10.0
        assert result.shipping_cost == 5.0
        assert result.total_cost == 15.0
        assert result.retail_price == 30.0
        assert result.gross_profit == 15.0
        assert result.gross_margin_pct == pytest.approx(0.5)
        assert result.platform_fee == pytest.approx(4.5)
        assert result.payment_fee == pytest.approx(1.17)
        assert result.total_fees == pytest.approx(5.67)
        assert result.net_profit == pytest.approx(9.33)
        assert result.currency == "USD"

    def test_calculate_with_custom_fees(self):
        """Test margin calculation with custom fees."""
        calculator = MarginCalculator(
            platform_fee_pct=0.10,
            payment_processing_fee_pct=0.025,
            fixed_payment_fee=0.20,
            currency="EUR",
        )
        result = calculator.calculate(
            cost_price=10.0,
            shipping_cost=5.0,
            retail_price=100.0,
        )
        assert result.platform_fee == pytest.approx(10.0)
        assert result.payment_fee == pytest.approx(2.7)
        assert result.total_fees == pytest.approx(12.7)
        assert result.net_profit == pytest.approx(72.3)
        assert result.currency == "EUR"

    def test_calculate_zero_costs(self):
        """Test margin calculation with zero costs."""
        calculator = MarginCalculator()
        result = calculator.calculate(
            cost_price=0.0,
            shipping_cost=0.0,
            retail_price=100.0,
        )
        assert result.total_cost == 0.0
        assert result.gross_profit == 100.0
        assert result.gross_margin_pct == 1.0
        assert result.net_profit == pytest.approx(81.8)

    def test_calculate_negative_cost_price_raises(self):
        """Test that negative cost_price raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="cost_price must be non-negative"):
            calculator.calculate(
                cost_price=-1.0,
                shipping_cost=5.0,
                retail_price=30.0,
            )

    def test_calculate_negative_shipping_cost_raises(self):
        """Test that negative shipping_cost raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="shipping_cost must be non-negative"):
            calculator.calculate(
                cost_price=10.0,
                shipping_cost=-1.0,
                retail_price=30.0,
            )

    def test_calculate_negative_retail_price_raises(self):
        """Test that negative retail_price raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="retail_price must be non-negative"):
            calculator.calculate(
                cost_price=10.0,
                shipping_cost=5.0,
                retail_price=-1.0,
            )

    def test_calculate_retail_less_than_cost_raises(self):
        """Test that retail_price < cost_price raises ValueError."""
        calculator = MarginCalculator()
        with pytest.raises(ValueError, match="retail_price must be >= cost_price"):
            calculator.calculate(
                cost_price=20.0,
                shipping_cost=5.0,
                retail_price=10.0,
            )

    def test_calculate_retail_equal_to_cost(self):
        """Test that retail_price == cost_price is allowed."""
        calculator = MarginCalculator()
        result = calculator.calculate(
            cost_price=10.0,
            shipping_cost=0.0,
            retail_price=10.0,
        )
        assert result.gross_profit == 0.0
        assert result.gross_margin_pct == 0.0

    def test_calculate_shipping_integration(self):
        """Test calculate with shipping integration."""
        calculator = MarginCalculator()
        shipping_cost = calculator.calculate_shipping(
            weight_kg=1.0,
            supplier_shipping_cost_per_unit=5.0,
            supplier_shipping_weight_factor=2.0,
        )
        result = calculator.calculate(
            cost_price=10.0,
            shipping_cost=shipping_cost,
            retail_price=30.0,
        )
        assert result.shipping_cost == 7.0
        assert result.total_cost == 17.0

    def test_calculate_recommended_action(self):
        """Test that recommended_action is set correctly."""
        calculator = MarginCalculator()
        # High margin should be "List"
        result = calculator.calculate(
            cost_price=10.0,
            shipping_cost=0.0,
            retail_price=100.0,
        )
        assert result.recommended_action == "List"

        # Low margin should be "Reject"
        result = calculator.calculate(
            cost_price=90.0,
            shipping_cost=0.0,
            retail_price=100.0,
        )
        assert result.recommended_action == "Reject"

        # Medium margin should be "Review"
        result = calculator.calculate(
            cost_price=70.0,
            shipping_cost=0.0,
            retail_price=100.0,
        )
        assert result.recommended_action == "Review"