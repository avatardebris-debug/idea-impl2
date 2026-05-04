"""Newsletter profit simulation engine."""

from __future__ import annotations

import random
from typing import List, Optional

from .config import SimConfig
from .state import NewsletterState


class NewsletterSimulator:
    """Simulates newsletter profit dynamics over time."""

    def __init__(self, config: SimConfig) -> None:
        """Initialize the simulator.

        Args:
            config: Simulation configuration.
        """
        self.config = config
        if config.seed is not None:
            random.seed(config.seed)
        self.current_state = NewsletterState(
            month=0,
            subscribers=config.initial_subscribers,
            revenue=config.initial_revenue,
            costs=config.content_cost + config.marketing_cost,
            profit=config.initial_revenue - (config.content_cost + config.marketing_cost),
            cumulative_profit=0.0,
        )
        self.history: List[NewsletterState] = [NewsletterState.from_dict(self.current_state.to_dict())]

    def reset(self) -> NewsletterState:
        """Reset the simulation to initial state.

        Returns:
            Initial state.
        """
        if self.config.seed is not None:
            random.seed(self.config.seed)
        self.current_state = NewsletterState(
            month=0,
            subscribers=self.config.initial_subscribers,
            revenue=self.config.initial_revenue,
            costs=self.config.content_cost + self.config.marketing_cost,
            profit=self.config.initial_revenue - (self.config.content_cost + self.config.marketing_cost),
            cumulative_profit=0.0,
        )
        self.history = [NewsletterState.from_dict(self.current_state.to_dict())]
        return self.current_state

    def step(self) -> NewsletterState:
        """Advance simulation by one month.

        Returns:
            Updated state.
        """
        # Advance month
        self.current_state.month += 1

        # Update subscribers
        new_subs = self.current_state.subscribers
        growth = int(new_subs * self.config.growth_rate)
        churn = int(new_subs * self.config.churn_rate)
        new_subs = new_subs + growth - churn
        new_subs = max(0, new_subs)
        self.current_state.subscribers = new_subs

        # Update revenue
        self.current_state.revenue = self.current_state.subscribers * self.config.revenue_per_subscriber

        # Update costs
        self.current_state.costs = self.config.content_cost + self.config.marketing_cost

        # Update profit
        self.current_state.profit = self.current_state.revenue - self.current_state.costs

        # Update cumulative profit
        self.current_state.cumulative_profit += self.current_state.profit

        # Check termination
        if self.current_state.subscribers == 0:
            self.current_state.is_terminated = True
            self.current_state.termination_reason = "No subscribers remaining"
        elif self.current_state.month >= self.config.max_months:
            self.current_state.is_terminated = True
            self.current_state.termination_reason = "Maximum months reached"

        # Add to history
        self.history.append(NewsletterState.from_dict(self.current_state.to_dict()))

        return self.current_state

    def run(self) -> List[NewsletterState]:
        """Run the full simulation.

        Returns:
            List of states over time.
        """
        while not self.current_state.is_terminated:
            self.step()
        return self.history

    def get_metrics(self) -> dict:
        """Get current metrics.

        Returns:
            Dictionary of current metrics.
        """
        return {
            "month": self.current_state.month,
            "subscribers": self.current_state.subscribers,
            "revenue": self.current_state.revenue,
            "profit": self.current_state.profit,
            "cumulative_profit": self.current_state.cumulative_profit,
        }
