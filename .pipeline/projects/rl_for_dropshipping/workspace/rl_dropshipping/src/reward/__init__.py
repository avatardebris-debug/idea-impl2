"""Multi-objective reward function for RL dropshipping.

Combines profit, ROAS, inventory health, and budget efficiency into
a single scalar reward with configurable weights.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MultiObjectiveReward:
    """Multi-objective reward function for RL dropshipping.

    Combines:
    - profit_reward: Net profit (revenue - cost)
    - roas_reward: Return on ad spend
    - inventory_penalty: Penalty for stockouts or overstock
    - budget_efficiency: Reward for efficient budget usage

    Attributes:
        w_profit: Weight for profit reward.
        w_roas: Weight for ROAS reward.
        w_inventory: Weight for inventory penalty.
        w_budget: Weight for budget efficiency.
        roas_target: Target ROAS for normalization.
        max_inventory: Maximum inventory level for penalty calculation.
        stockout_penalty: Penalty per unit of stockout.
        overstock_penalty: Penalty per unit of overstock.
    """

    def __init__(
        self,
        w_profit: float = 0.4,
        w_roas: float = 0.3,
        w_inventory: float = 0.2,
        w_budget: float = 0.1,
        roas_target: float = 3.0,
        max_inventory: int = 100,
        stockout_penalty: float = -5.0,
        overstock_penalty: float = -0.5,
    ):
        self.w_profit = w_profit
        self.w_roas = w_roas
        self.w_inventory = w_inventory
        self.w_budget = w_budget
        self.roas_target = roas_target
        self.max_inventory = max_inventory
        self.stockout_penalty = stockout_penalty
        self.overstock_penalty = overstock_penalty

    def compute_profit_reward(self, revenue: float, cost: float) -> float:
        """Compute profit reward.

        Args:
            revenue: Total revenue.
            cost: Total cost (COGS + ad spend).

        Returns:
            Profit reward (normalized).
        """
        profit = revenue - cost
        # Normalize by a scale factor to keep rewards in reasonable range
        scale = max(abs(revenue), 1.0)
        return profit / scale

    def compute_roas_reward(self, revenue: float, ad_spend: float) -> float:
        """Compute ROAS reward.

        Args:
            revenue: Total revenue.
            ad_spend: Total ad spend.

        Returns:
            ROAS reward (normalized around target).
        """
        if ad_spend == 0:
            return 0.0
        roas = revenue / ad_spend
        # Reward is positive when ROAS > target, negative when below
        return (roas - self.roas_target) / self.roas_target

    def compute_inventory_penalty(self, stock: int, demand: int) -> float:
        """Compute inventory penalty.

        Args:
            stock: Current stock level.
            demand: Current demand.

        Returns:
            Inventory penalty (negative value).
        """
        if stock == 0 and demand > 0:
            # Stockout penalty
            return self.stockout_penalty * demand
        elif stock > self.max_inventory:
            # Overstock penalty
            excess = stock - self.max_inventory
            return self.overstock_penalty * excess
        return 0.0

    def compute_budget_efficiency(self, budget_used: float, budget_total: float) -> float:
        """Compute budget efficiency reward.

        Args:
            budget_used: Amount of budget used.
            budget_total: Total budget available.

        Returns:
            Budget efficiency reward.
        """
        if budget_total == 0:
            return 0.0
        utilization = budget_used / budget_total
        # Reward for using between 70% and 100% of budget
        if 0.7 <= utilization <= 1.0:
            return 1.0
        elif utilization < 0.7:
            return -1.0 * (0.7 - utilization) / 0.7
        else:
            return -1.0 * (utilization - 1.0) / 0.3

    def compute_reward(self, metrics: Dict[str, Any]) -> float:
        """Compute the combined multi-objective reward.

        Args:
            metrics: Dictionary with keys:
                - revenue: Total revenue
                - cost: Total cost (COGS + ad spend)
                - ad_spend: Total ad spend
                - stock: Current stock level
                - demand: Current demand
                - budget_used: Amount of budget used
                - budget_total: Total budget available

        Returns:
            Combined scalar reward.
        """
        revenue = metrics.get("revenue", 0.0)
        cost = metrics.get("cost", 0.0)
        ad_spend = metrics.get("ad_spend", 0.0)
        stock = metrics.get("stock", 0)
        demand = metrics.get("demand", 0)
        budget_used = metrics.get("budget_used", 0.0)
        budget_total = metrics.get("budget_total", 0.0)

        profit_reward = self.compute_profit_reward(revenue, cost)
        roas_reward = self.compute_roas_reward(revenue, ad_spend)
        inventory_penalty = self.compute_inventory_penalty(stock, demand)
        budget_efficiency = self.compute_budget_efficiency(budget_used, budget_total)

        total_reward = (
            self.w_profit * profit_reward
            + self.w_roas * roas_reward
            + self.w_inventory * inventory_penalty
            + self.w_budget * budget_efficiency
        )

        return total_reward

    def get_component_rewards(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Get individual component rewards.

        Args:
            metrics: Dictionary with reward metrics.

        Returns:
            Dictionary with individual reward components.
        """
        revenue = metrics.get("revenue", 0.0)
        cost = metrics.get("cost", 0.0)
        ad_spend = metrics.get("ad_spend", 0.0)
        stock = metrics.get("stock", 0)
        demand = metrics.get("demand", 0)
        budget_used = metrics.get("budget_used", 0.0)
        budget_total = metrics.get("budget_total", 0.0)

        return {
            "profit_reward": self.compute_profit_reward(revenue, cost),
            "roas_reward": self.compute_roas_reward(revenue, ad_spend),
            "inventory_penalty": self.compute_inventory_penalty(stock, demand),
            "budget_efficiency": self.compute_budget_efficiency(budget_used, budget_total),
        }
