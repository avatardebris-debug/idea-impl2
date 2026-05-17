"""Operator agent for the dropshipping environment."""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, Optional


class OperatorAgent:
    """Manages the operator's (player's) actions in the dropshipping market.

    The operator decides which products to sell, through which channels,
    and at what budget levels.
    """

    def __init__(
        self,
        initial_budget: float,
        max_inventory: int,
        seed: Optional[int] = None,
    ):
        self.initial_budget = initial_budget
        self.budget = initial_budget
        self.max_inventory = max_inventory
        self.inventory = 0
        self.current_product: Optional[int] = None
        self.current_channel: Optional[int] = None
        self.current_budget_pct: float = 0.0
        self.cumulative_revenue: float = 0.0
        self.cumulative_cost: float = 0.0
        self.cumulative_ad_spend: float = 0.0
        self.np_random = np.random.RandomState(seed)

    def set_action(
        self,
        product_index: int,
        channel_index: int,
        budget_pct: float,
    ) -> None:
        """Set the operator's action for the current step.

        Args:
            product_index: Index of the product to sell.
            channel_index: Index of the ad channel to use.
            budget_pct: Percentage of budget to allocate to ads.
        """
        self.current_product = product_index
        self.current_channel = channel_index
        self.current_budget_pct = max(0.0, min(1.0, budget_pct))

    def execute_purchase(self, product_cost: float) -> bool:
        """Execute a purchase (inventory acquisition).

        Args:
            product_cost: Cost to acquire one unit of inventory.

        Returns:
            True if purchase was successful, False otherwise.
        """
        if self.budget >= product_cost and self.inventory < self.max_inventory:
            self.budget -= product_cost
            self.cumulative_cost += product_cost
            self.inventory += 1
            return True
        return False

    def execute_ad_spend(self) -> float:
        """Calculate and execute ad spend for the current step.

        Returns:
            The amount spent on advertising.
        """
        ad_budget = self.initial_budget * self.current_budget_pct * 0.1
        ad_spend = min(ad_budget, self.budget * 0.5)
        self.budget -= ad_spend
        self.cumulative_ad_spend += ad_spend
        return ad_spend

    def add_revenue(self, revenue: float) -> None:
        """Add revenue from sales.

        Args:
            revenue: Amount of revenue to add.
        """
        self.budget += revenue
        self.cumulative_revenue += revenue

    def reduce_inventory(self, quantity: int) -> None:
        """Reduce inventory by a given quantity.

        Args:
            quantity: Number of units to remove.
        """
        self.inventory = max(0, self.inventory - quantity)

    def get_state(self) -> Dict[str, Any]:
        """Get the operator's current state.

        Returns:
            Dictionary with operator state information.
        """
        return {
            "budget": self.budget,
            "inventory": self.inventory,
            "current_product": self.current_product,
            "current_channel": self.current_channel,
            "current_budget_pct": self.current_budget_pct,
            "cumulative_revenue": self.cumulative_revenue,
            "cumulative_cost": self.cumulative_cost,
            "cumulative_ad_spend": self.cumulative_ad_spend,
        }

    def reset(self) -> None:
        """Reset the operator's state for a new episode."""
        self.budget = self.initial_budget
        self.inventory = 0
        self.current_product = None
        self.current_channel = None
        self.current_budget_pct = 0.0
        self.cumulative_revenue = 0.0
        self.cumulative_cost = 0.0
        self.cumulative_ad_spend = 0.0
