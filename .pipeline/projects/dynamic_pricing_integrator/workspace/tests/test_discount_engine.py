"""Unit tests for the DiscountEngine and its rule types."""

import pytest
from datetime import datetime

from dynamic_pricing.models import (
    CompetitorPrice,
    DiscountResult,
    DiscountRuleType,
    PriceSnapshot,
    Product,
)
from dynamic_pricing.discount_engine import (
    BaseRule,
    CompetitorMatchRule,
    DiscountEngine,
    InventoryAgeRule,
    MarginFloorRule,
    PriceGapRule,
)


# ---- Helpers ----

def make_product(base_price: float = 100.0) -> Product:
    return Product(id="p1", name="Test Product", base_price=base_price)


def make_snapshots(prices: list, days_ago: int = 0) -> list:
    """Create PriceSnapshots with given prices, all from `days_ago` days ago."""
    ts = datetime.now()
    from datetime import timedelta
    ts = ts - timedelta(days=days_ago)
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


# ---- PriceGapRule Tests ----

class TestPriceGapRule:
    def test_triggers_when_gap_exceeds_threshold(self):
        rule = PriceGapRule(gap_threshold=0.05, discount_pct=0.10)
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([90.0])  # 10% gap
        result = rule.apply(product, snapshots)
        assert result is not None
        assert result.discount_pct == 0.10
        assert result.effective_price == 90.0
        assert "10.0%" in result.reason

    def test_no_trigger_when_gap_below_threshold(self):
        rule = PriceGapRule(gap_threshold=0.05, discount_pct=0.10)
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([96.0])  # 4% gap
        result = rule.apply(product, snapshots)
        assert result is None

    def test_no_trigger_with_no_snapshots(self):
        rule = PriceGapRule(gap_threshold=0.05, discount_pct=0.10)
        product = make_product(base_price=100.0)
        result = rule.apply(product, [])
        assert result is None

    def test_uses_lowest_competitor_price(self):
        rule = PriceGapRule(gap_threshold=0.05, discount_pct=0.10)
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([95.0, 90.0, 92.0])  # lowest is 90
        result = rule.apply(product, snapshots)
        assert result is not None
        assert result.effective_price == 90.0  # 100 * (1 - 0.10)


# ---- InventoryAgeRule Tests ----

class TestInventoryAgeRule:
    def test_triggers_when_inventory_exceeds_days(self):
        rule = InventoryAgeRule(inventory_days=30, discount_pct=0.10)
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([100.0], days_ago=35)
        result = rule.apply(product, snapshots)
        assert result is not None
        assert result.discount_pct == 0.10
        assert "35 days" in result.reason

    def test_no_trigger_when_inventory_below_days(self):
        rule = InventoryAgeRule(inventory_days=30, discount_pct=0.10)
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([100.0], days_ago=25)
        result = rule.apply(product, snapshots)
        assert result is None

    def test_no_trigger_with_no_snapshots(self):
        rule = InventoryAgeRule(inventory_days=30, discount_pct=0.10)
        product = make_product(base_price=100.0)
        result = rule.apply(product, [])
        assert result is None


# ---- MarginFloorRule Tests ----

class TestMarginFloorRule:
    def test_triggers_when_margin_below_floor(self):
        rule = MarginFloorRule(margin_floor=0.10, discount_pct=0.10)
        product = make_product(base_price=100.0)
        # cost = 100 * (1 - 0.10) = 90
        # competitor price = 92 => margin = (92 - 90) / 92 = 0.0217 < 0.10
        snapshots = make_snapshots([92.0])
        result = rule.apply(product, snapshots)
        assert result is not None
        assert result.discount_pct == 0.10

    def test_no_trigger_when_margin_above_floor(self):
        rule = MarginFloorRule(margin_floor=0.10, discount_pct=0.10)
        product = make_product(base_price=100.0)
        # cost = 90, competitor = 95 => margin = (95 - 90) / 95 = 0.0526
        # This is still below 0.10, so it should trigger
        snapshots = make_snapshots([95.0])
        result = rule.apply(product, snapshots)
        # margin = 0.0526 < 0.10, so it triggers
        assert result is not None

    def test_no_trigger_with_no_snapshots(self):
        rule = MarginFloorRule(margin_floor=0.10, discount_pct=0.10)
        product = make_product(base_price=100.0)
        result = rule.apply(product, [])
        assert result is None


# ---- CompetitorMatchRule Tests ----

class TestCompetitorMatchRule:
    def test_triggers_when_competitor_lower(self):
        rule = CompetitorMatchRule(discount_pct=0.0)
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([90.0])
        result = rule.apply(product, snapshots)
        assert result is not None
        assert result.effective_price == 90.0
        assert "Matching" in result.reason

    def test_no_trigger_when_competitor_higher(self):
        rule = CompetitorMatchRule(discount_pct=0.0)
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([110.0])
        result = rule.apply(product, snapshots)
        assert result is None

    def test_no_trigger_with_no_snapshots(self):
        rule = CompetitorMatchRule(discount_pct=0.0)
        product = make_product(base_price=100.0)
        result = rule.apply(product, [])
        assert result is None


# ---- DiscountEngine Tests ----

class TestDiscountEngine:
    def test_no_rules_returns_none(self):
        engine = DiscountEngine()
        product = make_product()
        result = engine.evaluate(product, [])
        assert result is None

    def test_last_rule_wins_strategy(self):
        engine = DiscountEngine(strategy="last_rule_wins")
        engine.add_rule(PriceGapRule(gap_threshold=0.05, discount_pct=0.10))
        engine.add_rule(InventoryAgeRule(inventory_days=30, discount_pct=0.20))
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([90.0], days_ago=35)
        result = engine.evaluate(product, snapshots)
        assert result is not None
        assert result.discount_pct == 0.20  # last rule wins

    def test_weighted_average_strategy(self):
        engine = DiscountEngine(strategy="weighted_average")
        engine.add_rule(PriceGapRule(gap_threshold=0.05, discount_pct=0.10))
        engine.add_rule(InventoryAgeRule(inventory_days=30, discount_pct=0.20))
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([90.0], days_ago=35)
        result = engine.evaluate(product, snapshots)
        assert result is not None
        # Weighted average: (0.10^2 + 0.20^2) / (0.10 + 0.20) = (0.01 + 0.04) / 0.30 = 0.1667
        assert abs(result.discount_pct - 0.1667) < 0.001

    def test_single_rule_applied(self):
        engine = DiscountEngine()
        engine.add_rule(PriceGapRule(gap_threshold=0.05, discount_pct=0.10))
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([90.0])
        result = engine.evaluate(product, snapshots)
        assert result is not None
        assert result.discount_pct == 0.10

    def test_no_rule_triggers_returns_none(self):
        engine = DiscountEngine()
        engine.add_rule(PriceGapRule(gap_threshold=0.05, discount_pct=0.10))
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([98.0])  # only 2% gap
        result = engine.evaluate(product, snapshots)
        assert result is None

    def test_rules_property_returns_copy(self):
        engine = DiscountEngine()
        engine.add_rule(PriceGapRule())
        rules = engine.rules
        assert len(rules) == 1
        # Modifying the returned list should not affect the engine
        rules.clear()
        assert len(engine.rules) == 1

    def test_invalid_strategy_raises(self):
        engine = DiscountEngine(strategy="invalid")
        engine.add_rule(PriceGapRule(gap_threshold=0.05, discount_pct=0.10))
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([90.0])
        with pytest.raises(ValueError, match="Unknown strategy"):
            engine.evaluate(product, snapshots)

    def test_multiple_rules_some_trigger(self):
        engine = DiscountEngine(strategy="last_rule_wins")
        engine.add_rule(PriceGapRule(gap_threshold=0.05, discount_pct=0.10))
        engine.add_rule(InventoryAgeRule(inventory_days=30, discount_pct=0.15))
        product = make_product(base_price=100.0)
        # Only inventory rule triggers (gap is 0)
        snapshots = make_snapshots([100.0], days_ago=35)
        result = engine.evaluate(product, snapshots)
        assert result is not None
        assert result.discount_pct == 0.15

    def test_competitor_match_rule_integration(self):
        engine = DiscountEngine()
        engine.add_rule(CompetitorMatchRule())
        product = make_product(base_price=100.0)
        snapshots = make_snapshots([85.0])
        result = engine.evaluate(product, snapshots)
        assert result is not None
        assert result.effective_price == 85.0
        assert result.discount_pct == pytest.approx(0.15, abs=0.001)

    def test_margin_floor_rule_integration(self):
        engine = DiscountEngine()
        engine.add_rule(MarginFloorRule(margin_floor=0.10, discount_pct=0.10))
        product = make_product(base_price=100.0)
        # cost = 90, competitor = 91 => margin = 1/91 = 0.011 < 0.10
        snapshots = make_snapshots([91.0])
        result = engine.evaluate(product, snapshots)
        assert result is not None
        assert result.discount_pct == 0.10
