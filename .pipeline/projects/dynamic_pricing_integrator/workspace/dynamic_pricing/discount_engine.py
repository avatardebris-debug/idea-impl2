"""Discount rule engine for dynamic pricing.

Provides a rule-based discount calculation engine with support for
four rule types and two combination strategies.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional

from .models import (
    CompetitorPrice,
    DiscountResult,
    DiscountRule,
    DiscountRuleType,
    PriceSnapshot,
    Product,
)


class BaseRule(ABC):
    """Abstract base class for discount rules."""

    @abstractmethod
    def apply(self, product: Product, snapshots: List[PriceSnapshot]) -> Optional[DiscountResult]:
        """Apply this rule and return a DiscountResult if the rule triggers, else None."""
        ...


class PriceGapRule(BaseRule):
    """Triggers when a competitor's price is below the base price by a threshold.

    Attributes:
        gap_threshold: Minimum price gap ratio to trigger (e.g. 0.05 = 5%).
        discount_pct: Discount percentage to apply when triggered.
    """

    def __init__(self, gap_threshold: float = 0.05, discount_pct: float = 0.10):
        self.gap_threshold = gap_threshold
        self.discount_pct = discount_pct

    def apply(self, product: Product, snapshots: List[PriceSnapshot]) -> Optional[DiscountResult]:
        if not snapshots:
            return None

        lowest_competitor_price = min(s.price for s in snapshots)
        gap_ratio = (product.base_price - lowest_competitor_price) / product.base_price

        if gap_ratio >= self.gap_threshold:
            effective_price = product.base_price * (1 - self.discount_pct)
            return DiscountResult(
                discount_pct=self.discount_pct,
                effective_price=round(effective_price, 2),
                reason=f"Competitor price {lowest_competitor_price:.2f} is {gap_ratio:.1%} below base price {product.base_price:.2f}",
            )
        return None


class InventoryAgeRule(BaseRule):
    """Triggers when a product has been in inventory longer than a threshold.

    Attributes:
        inventory_days: Days-in-inventory threshold to trigger.
        discount_pct: Discount percentage to apply when triggered.
    """

    def __init__(self, inventory_days: int = 30, discount_pct: float = 0.10):
        self.inventory_days = inventory_days
        self.discount_pct = discount_pct

    def apply(self, product: Product, snapshots: List[PriceSnapshot]) -> Optional[DiscountResult]:
        # Use the most recent snapshot timestamp as a proxy for inventory age
        if not snapshots:
            return None

        oldest_timestamp = min(s.timestamp for s in snapshots)
        days_in_inventory = (datetime.now() - oldest_timestamp).days

        if days_in_inventory >= self.inventory_days:
            effective_price = product.base_price * (1 - self.discount_pct)
            return DiscountResult(
                discount_pct=self.discount_pct,
                effective_price=round(effective_price, 2),
                reason=f"Product has been in inventory for {days_in_inventory} days (threshold: {self.inventory_days})",
            )
        return None


class MarginFloorRule(BaseRule):
    """Triggers when current margin drops below a floor threshold.

    Attributes:
        margin_floor: Minimum margin ratio to trigger (e.g. 0.10 = 10%).
        discount_pct: Discount percentage to apply when triggered.
    """

    def __init__(self, margin_floor: float = 0.10, discount_pct: float = 0.10):
        self.margin_floor = margin_floor
        self.discount_pct = discount_pct

    def apply(self, product: Product, snapshots: List[PriceSnapshot]) -> Optional[DiscountResult]:
        if not snapshots:
            return None

        lowest_competitor_price = min(s.price for s in snapshots)
        # Assume cost is base_price * (1 - margin_floor) for simplicity
        # Current margin = (lowest_competitor_price - cost) / lowest_competitor_price
        cost = product.base_price * (1 - self.margin_floor)
        current_margin = (lowest_competitor_price - cost) / lowest_competitor_price if lowest_competitor_price > 0 else 0

        if current_margin < self.margin_floor:
            effective_price = product.base_price * (1 - self.discount_pct)
            return DiscountResult(
                discount_pct=self.discount_pct,
                effective_price=round(effective_price, 2),
                reason=f"Current margin {current_margin:.1%} is below floor {self.margin_floor:.1%}",
            )
        return None


class CompetitorMatchRule(BaseRule):
    """Triggers to match the lowest competitor price.

    Attributes:
        discount_pct: Discount percentage to apply to match competitor price.
    """

    def __init__(self, discount_pct: float = 0.0):
        self.discount_pct = discount_pct

    def apply(self, product: Product, snapshots: List[PriceSnapshot]) -> Optional[DiscountResult]:
        if not snapshots:
            return None

        lowest_competitor_price = min(s.price for s in snapshots)
        if lowest_competitor_price < product.base_price:
            # Calculate the discount needed to match the competitor
            needed_discount = (product.base_price - lowest_competitor_price) / product.base_price
            effective_price = lowest_competitor_price
            return DiscountResult(
                discount_pct=round(needed_discount, 4),
                effective_price=round(effective_price, 2),
                reason=f"Matching lowest competitor price {lowest_competitor_price:.2f}",
            )
        return None


class DiscountEngine:
    """Engine for evaluating discount rules on products.

    Attributes:
        rules: List of registered discount rules.
        strategy: Combination strategy ('last_rule_wins' or 'weighted_average').
    """

    def __init__(self, strategy: str = "last_rule_wins"):
        self._rules: List[BaseRule] = []
        self.strategy = strategy

    def add_rule(self, rule: BaseRule) -> None:
        """Register a discount rule."""
        self._rules.append(rule)

    def evaluate(self, product: Product, snapshots: List[PriceSnapshot]) -> Optional[DiscountResult]:
        """Evaluate all registered rules and return a DiscountResult.

        Args:
            product: The product to evaluate.
            snapshots: Competitor price snapshots for the product.

        Returns:
            A DiscountResult if any rule triggers, else None.
        """
        if not self._rules:
            return None

        results = []
        for rule in self._rules:
            result = rule.apply(product, snapshots)
            if result is not None:
                results.append(result)

        if not results:
            return None

        if self.strategy == "last_rule_wins":
            return results[-1]
        elif self.strategy == "weighted_average":
            return self._weighted_average(results)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _weighted_average(self, results: List[DiscountResult]) -> DiscountResult:
        """Compute a weighted average of multiple DiscountResults.

        Weights are proportional to the discount_pct of each result.
        The effective_price is computed as the weighted average of individual effective prices.
        """
        total_weight = sum(r.discount_pct for r in results)
        if total_weight == 0:
            return results[0]

        avg_discount = sum(r.discount_pct * r.discount_pct for r in results) / total_weight
        # Compute effective_price as the weighted average of individual effective prices
        avg_effective = sum(r.effective_price * r.discount_pct for r in results) / total_weight
        combined_reason = " + ".join(r.reason for r in results)
        return DiscountResult(
            discount_pct=round(avg_discount, 4),
            effective_price=round(avg_effective, 2),
            reason=combined_reason,
        )

    @property
    def rules(self) -> List[BaseRule]:
        """Return the list of registered rules."""
        return list(self._rules)
