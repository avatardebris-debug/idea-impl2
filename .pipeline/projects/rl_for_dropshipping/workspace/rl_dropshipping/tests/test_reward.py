"""Tests for multi-objective reward function."""

import pytest
from rl_dropshipping.src.reward import MultiObjectiveReward


class TestMultiObjectiveReward:
    """Tests for MultiObjectiveReward."""

    def setup_method(self):
        """Create a fresh reward function for each test."""
        self.reward_fn = MultiObjectiveReward()

    # --- Profit reward ---

    def test_profit_reward_positive(self):
        """Profit reward is positive when revenue > cost."""
        reward = self.reward_fn.compute_profit_reward(revenue=100.0, cost=50.0)
        assert reward > 0.0

    def test_profit_reward_negative(self):
        """Profit reward is negative when revenue < cost."""
        reward = self.reward_fn.compute_profit_reward(revenue=50.0, cost=100.0)
        assert reward < 0.0

    def test_profit_reward_zero(self):
        """Profit reward is zero when revenue == cost."""
        reward = self.reward_fn.compute_profit_reward(revenue=100.0, cost=100.0)
        assert reward == 0.0

    def test_profit_reward_normalized(self):
        """Profit reward is normalized by revenue scale."""
        reward_small = self.reward_fn.compute_profit_reward(revenue=10.0, cost=5.0)
        reward_large = self.reward_fn.compute_profit_reward(revenue=1000.0, cost=500.0)
        # Both should be 0.5 (50% profit) since normalized
        assert abs(reward_small - 0.5) < 0.01
        assert abs(reward_large - 0.5) < 0.01

    # --- ROAS reward ---

    def test_roas_reward_positive(self):
        """ROAS reward is positive when ROAS > target."""
        reward = self.reward_fn.compute_roas_reward(revenue=300.0, ad_spend=100.0)
        # ROAS = 3.0, target = 3.0, so reward should be 0
        assert abs(reward) < 0.01

    def test_roas_reward_negative(self):
        """ROAS reward is negative when ROAS < target."""
        reward = self.reward_fn.compute_roas_reward(revenue=150.0, ad_spend=100.0)
        # ROAS = 1.5, target = 3.0, so reward should be negative
        assert reward < 0.0

    def test_roas_reward_zero_ad_spend(self):
        """ROAS reward is zero when ad_spend is zero."""
        reward = self.reward_fn.compute_roas_reward(revenue=100.0, ad_spend=0.0)
        assert reward == 0.0

    def test_roas_reward_above_target(self):
        """ROAS reward is positive when ROAS > target."""
        reward = self.reward_fn.compute_roas_reward(revenue=600.0, ad_spend=100.0)
        # ROAS = 6.0, target = 3.0, so reward should be positive
        assert reward > 0.0

    # --- Inventory penalty ---

    def test_inventory_penalty_stockout(self):
        """Inventory penalty is negative when stockout occurs."""
        penalty = self.reward_fn.compute_inventory_penalty(stock=0, demand=5)
        assert penalty < 0.0
        assert penalty == self.reward_fn.stockout_penalty * 5

    def test_inventory_penalty_overstock(self):
        """Inventory penalty is negative when overstock occurs."""
        penalty = self.reward_fn.compute_inventory_penalty(stock=150, demand=10)
        assert penalty < 0.0
        assert penalty == self.reward_fn.overstock_penalty * 50

    def test_inventory_penalty_no_penalty(self):
        """Inventory penalty is zero when stock is healthy."""
        penalty = self.reward_fn.compute_inventory_penalty(stock=50, demand=10)
        assert penalty == 0.0

    def test_inventory_penalty_no_demand(self):
        """Inventory penalty is zero when demand is zero."""
        penalty = self.reward_fn.compute_inventory_penalty(stock=0, demand=0)
        assert penalty == 0.0

    # --- Budget efficiency ---

    def test_budget_efficiency_optimal(self):
        """Budget efficiency is 1.0 when utilization is optimal."""
        efficiency = self.reward_fn.compute_budget_efficiency(
            budget_used=80.0, budget_total=100.0
        )
        assert efficiency == 1.0

    def test_budget_efficiency_low(self):
        """Budget efficiency is negative when utilization is low."""
        efficiency = self.reward_fn.compute_budget_efficiency(
            budget_used=50.0, budget_total=100.0
        )
        assert efficiency < 0.0

    def test_budget_efficiency_zero_total(self):
        """Budget efficiency is zero when total budget is zero."""
        efficiency = self.reward_fn.compute_budget_efficiency(
            budget_used=0.0, budget_total=0.0
        )
        assert efficiency == 0.0

    def test_budget_efficiency_over_budget(self):
        """Budget efficiency is negative when over budget."""
        efficiency = self.reward_fn.compute_budget_efficiency(
            budget_used=120.0, budget_total=100.0
        )
        assert efficiency < 0.0

    # --- Combined reward ---

    def test_combined_reward_positive(self):
        """Combined reward is positive when all components are positive."""
        metrics = {
            "revenue": 300.0,
            "cost": 100.0,
            "ad_spend": 100.0,
            "stock": 50,
            "demand": 10,
            "budget_used": 80.0,
            "budget_total": 100.0,
        }
        reward = self.reward_fn.compute_reward(metrics)
        assert reward > 0.0

    def test_combined_reward_negative(self):
        """Combined reward is negative when components are negative."""
        metrics = {
            "revenue": 50.0,
            "cost": 100.0,
            "ad_spend": 100.0,
            "stock": 0,
            "demand": 10,
            "budget_used": 50.0,
            "budget_total": 100.0,
        }
        reward = self.reward_fn.compute_reward(metrics)
        assert reward < 0.0

    def test_combined_reward_zero(self):
        """Combined reward is zero when all components are zero."""
        metrics = {
            "revenue": 100.0,
            "cost": 100.0,
            "ad_spend": 100.0,
            "stock": 50,
            "demand": 10,
            "budget_used": 80.0,
            "budget_total": 100.0,
        }
        # profit_reward = 0, roas_reward = 0, inventory_penalty = 0, budget_efficiency = 1.0
        # total = 0.4*0 + 0.3*0 + 0.2*0 + 0.1*1.0 = 0.1
        reward = self.reward_fn.compute_reward(metrics)
        assert reward == pytest.approx(0.1, rel=1e-3)

    # --- Component rewards ---

    def test_get_component_rewards(self):
        """get_component_rewards returns correct components."""
        metrics = {
            "revenue": 300.0,
            "cost": 100.0,
            "ad_spend": 100.0,
            "stock": 50,
            "demand": 10,
            "budget_used": 80.0,
            "budget_total": 100.0,
        }
        components = self.reward_fn.get_component_rewards(metrics)
        assert "profit_reward" in components
        assert "roas_reward" in components
        assert "inventory_penalty" in components
        assert "budget_efficiency" in components

    # --- Custom weights ---

    def test_custom_weights(self):
        """Custom weights are applied correctly."""
        reward_fn = MultiObjectiveReward(
            w_profit=0.5,
            w_roas=0.3,
            w_inventory=0.1,
            w_budget=0.1,
        )
        metrics = {
            "revenue": 300.0,
            "cost": 100.0,
            "ad_spend": 100.0,
            "stock": 50,
            "demand": 10,
            "budget_used": 80.0,
            "budget_total": 100.0,
        }
        reward = reward_fn.compute_reward(metrics)
        # profit_reward = 0.6667, roas_reward = 0, inventory_penalty = 0, budget_efficiency = 1.0
        # total = 0.5*0.6667 + 0.3*0 + 0.1*0 + 0.1*1.0 = 0.3333 + 0.1 = 0.4333
        assert reward == pytest.approx(0.4333, rel=1e-3)
