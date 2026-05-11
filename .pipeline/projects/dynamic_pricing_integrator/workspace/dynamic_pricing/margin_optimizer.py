"""Margin optimizer for dynamic pricing.

Computes optimal prices to hit target margins and checks current margin status.
"""

from typing import List, Optional

from .config import PricingConfig
from .models import (
    MarginStatus,
    MarginStatusEnum,
    PriceSnapshot,
    Product,
    RecommendedPrice,
)


class MarginOptimizer:
    """Optimizes pricing to achieve target margins.

    Attributes:
        config: Pricing configuration (provides default margin_floor).
        target_margin: Target profit margin as a decimal.
        ceiling_multiplier: Multiplier for ceiling price relative to base price.
    """

    def __init__(
        self,
        config: Optional[PricingConfig] = None,
        target_margin: float = 0.20,
        ceiling_multiplier: float = 1.5,
    ):
        self.config = config or PricingConfig()
        self.target_margin = target_margin
        self.ceiling_multiplier = ceiling_multiplier

    def calculate_optimal_price(self, product: Product, snapshots: List[PriceSnapshot]) -> RecommendedPrice:
        """Compute the optimal price to hit the target margin.

        Uses the lowest competitor price as a reference and computes
        the price that achieves the target margin.

        Args:
            product: The product to optimize pricing for.
            snapshots: Competitor price snapshots.

        Returns:
            A RecommendedPrice with floor/ceiling bounds enforced.
        """
        floor = product.base_price * (1 - self.config.margin_floor)
        ceiling = product.base_price * self.ceiling_multiplier

        if snapshots:
            lowest_competitor = min(s.price for s in snapshots)
            # Use competitor price as a reference point
            reference_price = lowest_competitor
        else:
            reference_price = product.base_price

        # Compute price needed to achieve target margin
        # margin = (price - cost) / price => price = cost / (1 - margin)
        # Assume cost is derived from base_price and margin_floor
        cost = product.base_price * (1 - self.config.margin_floor)
        optimal_price = cost / (1 - self.target_margin) if self.target_margin < 1.0 else product.base_price

        # Clamp to floor/ceiling
        optimal_price = max(floor, min(ceiling, optimal_price))

        return RecommendedPrice(
            product_id=product.id,
            recommended_price=round(optimal_price, 2),
            target_margin=self.target_margin,
            floor=round(floor, 2),
            ceiling=round(ceiling, 2),
        )

    def check_margin(self, product: Product, snapshots: List[PriceSnapshot]) -> MarginStatus:
        """Check the current margin status for a product.

        Args:
            product: The product to check.
            snapshots: Competitor price snapshots.

        Returns:
            A MarginStatus with current margin, target margin, and status.
        """
        if snapshots:
            lowest_competitor = min(s.price for s in snapshots)
            # Current margin based on lowest competitor price
            cost = product.base_price * (1 - self.config.margin_floor)
            current_margin = (lowest_competitor - cost) / lowest_competitor if lowest_competitor > 0 else 0
        else:
            # No competitor data; assume current margin is the config margin_floor
            current_margin = self.config.margin_floor

        if current_margin < self.target_margin * 0.9:
            status = MarginStatusEnum.BELOW
        elif current_margin > self.target_margin * 1.1:
            status = MarginStatusEnum.ABOVE
        else:
            status = MarginStatusEnum.WITHIN

        return MarginStatus(
            current_margin=round(current_margin, 4),
            target_margin=self.target_margin,
            status=status,
        )
