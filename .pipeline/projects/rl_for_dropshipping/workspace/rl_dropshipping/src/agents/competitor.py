"""Competitor agent for the dropshipping environment."""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, Optional


class CompetitorAgent:
    """Simulates competitor behavior in the dropshipping market.

    Competitors adjust their prices based on market conditions,
    their own inventory levels, and the actions of other competitors.
    """

    def __init__(
        self,
        competitor_id: int,
        base_price: float,
        inventory: int,
        max_inventory: int,
        price_aggression: float = 0.5,
        inventory_threshold: float = 0.3,
        seed: Optional[int] = None,
    ):
        self.competitor_id = competitor_id
        self.base_price = base_price
        self.inventory = inventory
        self.max_inventory = max_inventory
        self.price_aggression = price_aggression
        self.inventory_threshold = inventory_threshold
        self.np_random = np.random.RandomState(seed)

    def get_price(self, market_conditions: Dict[str, float]) -> float:
        """Get the competitor's current price based on market conditions.

        Args:
            market_conditions: Dictionary with keys 'competition_intensity',
                'seasonality', 'demand_trend'.

        Returns:
            The competitor's current price.
        """
        competition_intensity = market_conditions.get("competition_intensity", 0.3)
        seasonality = market_conditions.get("seasonality", 1.0)
        demand_trend = market_conditions.get("demand_trend", 1.0)

        # Base price adjustment for competition
        price_adjustment = 1.0 - competition_intensity * self.price_aggression

        # Inventory-based adjustment (clearance if low inventory)
        inventory_ratio = self.inventory / max(self.max_inventory, 1)
        if inventory_ratio < self.inventory_threshold:
            price_adjustment *= 0.8  # Discount for clearance

        # Seasonality adjustment
        price_adjustment *= seasonality

        # Demand trend adjustment
        price_adjustment *= demand_trend

        price = self.base_price * price_adjustment
        return max(price, self.base_price * 0.5)  # Floor at 50% of base price

    def update_inventory(self, sales: int) -> None:
        """Update the competitor's inventory after sales.

        Args:
            sales: Number of units sold.
        """
        self.inventory = max(0, self.inventory - sales)

    def restock(self, quantity: int) -> None:
        """Restock the competitor's inventory.

        Args:
            quantity: Number of units to add.
        """
        self.inventory = min(self.max_inventory, self.inventory + quantity)

    def get_state(self) -> Dict[str, Any]:
        """Get the competitor's current state.

        Returns:
            Dictionary with competitor state information.
        """
        return {
            "competitor_id": self.competitor_id,
            "price": self.get_price({
                "competition_intensity": 0.3,
                "seasonality": 1.0,
                "demand_trend": 1.0,
            }),
            "inventory": self.inventory,
            "max_inventory": self.max_inventory,
        }
