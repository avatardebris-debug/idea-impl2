"""Unit tests for the MarginOptimizer."""

import pytest
from datetime import datetime, timedelta

from dynamic_pricing.config import PricingConfig
from dynamic_pricing.models import (
    MarginStatus,
    MarginStatusEnum,
    PriceSnapshot,
    Product,
    RecommendedPrice,
)
from dynamic_pricing.margin_optimizer import MarginOptimizer


# ---- Helpers ----

def make_product(base_price: float = 100.0) -> Product:
    return Product(id="p1", name="Test Product", base_price=base_price)


def make_snapshots(prices: list) -> list:
    ts = datetime.now() - timedelta(days=1)
    return [
        PriceSnapshot(
            product_id="p1",
            competitor=f"comp_{i}",
            price=p,
            timestamp=ts,
            source="mock",
        )
        for i, p in enumerate(prices)
    ]


# ---- MarginOptimizer Tests ----

class TestMarginOptimizer:
    def test_calculate_optimal_price_with_no_snapshots(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.20)
        product = make_product(base_price=100.0)
        result = optimizer.calculate_optimal_price(product, [])
        assert result is not None
        assert result.product_id == "p1"
        assert result.target_margin == 0.20
        # cost = 100 * (1 - 0.15) = 85
        # optimal = 85 / (1 - 0.20) = 106.25
        assert result.recommended_price == pytest.approx(106.25, abs=0.01)
        assert result.floor == pytest.approx(85.0, abs=0.01)
        assert result.ceiling == pytest.approx(150.0, abs=0.01)

    def test_calculate_optimal_price_with_snapshots(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.20)
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([90.0, 95.0])  # lowest = 90
        result = optimizer.calculate_optimal_price(product, snapshots)
        assert result is not None
        # cost = 85, optimal = 85 / 0.80 = 106.25
        assert result.recommended_price == pytest.approx(106.25, abs=0.01)

    def test_floor_enforcement(self):
        config = PricingConfig(margin_floor=0.15)
        # Very low target margin => optimal price would be below floor
        optimizer = MarginOptimizer(config=config, target_margin=0.01)
        product = make_product(base_price=100.0)
        result = optimizer.calculate_optimal_price(product, [])
        # cost = 85, optimal = 85 / 0.99 = 85.86 => clamped to floor? No, 85.86 > 85
        # Let's test with target_margin = 0.0 => optimal = 85 / 1.0 = 85 = floor
        optimizer2 = MarginOptimizer(config=config, target_margin=0.0)
        result2 = optimizer2.calculate_optimal_price(product, [])
        assert result2.recommended_price == pytest.approx(85.0, abs=0.01)

    def test_ceiling_enforcement(self):
        config = PricingConfig(margin_floor=0.15)
        # Very high target margin => optimal price would exceed ceiling
        optimizer = MarginOptimizer(config=config, target_margin=0.99)
        product = make_product(base_price=100.0)
        result = optimizer.calculate_optimal_price(product, [])
        # cost = 85, optimal = 85 / 0.01 = 8500 => clamped to ceiling = 150
        assert result.recommended_price == pytest.approx(150.0, abs=0.01)
        assert result.ceiling == pytest.approx(150.0, abs=0.01)

    def test_check_margin_below(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.20)
        product = make_product(base_price=100.0)
        # cost = 85, competitor = 88 => margin = (88 - 85) / 88 = 0.034 < 0.18 (0.9 * 0.20)
        snapshots = make_snapshots([88.0])
        result = optimizer.check_margin(product, snapshots)
        assert result.status == MarginStatusEnum.BELOW
        assert result.current_margin == pytest.approx(0.0341, abs=0.001)

    def test_check_margin_within(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.20)
        product = make_product(base_price=100.0)
        # cost = 85, competitor = 100 => margin = (100 - 85) / 100 = 0.15
        # 0.18 <= 0.15 <= 0.22 => WITHIN
        # Actually: 0.15 < 0.18, so it's BELOW. Let's use a higher competitor price.
        # competitor = 110 => margin = (110 - 85) / 110 = 0.2273
        # 0.18 <= 0.2273 <= 0.22 => ABOVE. Let's use competitor = 105
        # margin = (105 - 85) / 105 = 0.1905
        # 0.18 <= 0.1905 <= 0.22 => WITHIN
        snapshots = make_snapshots([105.0])
        result = optimizer.check_margin(product, snapshots)
        assert result.status == MarginStatusEnum.WITHIN
        assert result.current_margin == pytest.approx(0.1905, abs=0.001)

    def test_check_margin_above(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.20)
        product = make_product(base_price=100.0)
        # cost = 85, competitor = 120 => margin = (120 - 85) / 120 = 0.2917 > 0.22
        snapshots = make_snapshots([120.0])
        result = optimizer.check_margin(product, snapshots)
        assert result.status == MarginStatusEnum.ABOVE

    def test_check_margin_no_snapshots(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.20)
        product = make_product(base_price=100.0)
        # current_margin = config.margin_floor = 0.15
        # 0.18 <= 0.15 <= 0.22 => WITHIN
        # Actually: 0.15 < 0.18, so it's BELOW
        result = optimizer.check_margin(product, [])
        assert result.status == MarginStatusEnum.BELOW
        assert result.current_margin == pytest.approx(0.15, abs=0.001)

    def test_recommended_price_has_correct_fields(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.20)
        product = make_product(base_price=100.0)
        result = optimizer.calculate_optimal_price(product, [])
        assert isinstance(result, RecommendedPrice)
        assert result.product_id == "p1"
        assert result.recommended_price > 0
        assert result.floor > 0
        assert result.ceiling > result.floor
        assert result.target_margin == 0.20

    def test_margin_status_has_correct_fields(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.20)
        product = make_product(base_price=100.0)
        result = optimizer.check_margin(product, [])
        assert isinstance(result, MarginStatus)
        assert result.current_margin == pytest.approx(0.15, abs=0.001)
        assert result.target_margin == 0.20
        assert result.status in (MarginStatusEnum.BELOW, MarginStatusEnum.WITHIN, MarginStatusEnum.ABOVE)

    def test_default_config_used_when_none_provided(self):
        optimizer = MarginOptimizer(target_margin=0.20)
        product = make_product(base_price=100.0)
        result = optimizer.calculate_optimal_price(product, [])
        # Default margin_floor = 0.15
        # cost = 85, optimal = 85 / 0.80 = 106.25
        assert result.recommended_price == pytest.approx(106.25, abs=0.01)

    def test_target_margin_zero(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=0.0)
        product = make_product(base_price=100.0)
        result = optimizer.calculate_optimal_price(product, [])
        # optimal = 85 / 1.0 = 85
        assert result.recommended_price == pytest.approx(85.0, abs=0.01)

    def test_target_margin_one(self):
        config = PricingConfig(margin_floor=0.15)
        optimizer = MarginOptimizer(config=config, target_margin=1.0)
        product = make_product(base_price=100.0)
        # When target_margin = 1.0, optimal = product.base_price = 100
        result = optimizer.calculate_optimal_price(product, [])
        assert result.recommended_price == pytest.approx(100.0, abs=0.01)
