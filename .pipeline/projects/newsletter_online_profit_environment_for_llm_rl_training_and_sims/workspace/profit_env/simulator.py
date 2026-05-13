"""Simulator module for the Newsletter Online Profit Environment."""

import json
import numpy as np
from typing import List, Dict, Any, Optional
from .config import SimConfig
from .state import NewsletterState


class SimulationHistory:
    """Tracks weekly simulation results with statistics and serialization."""

    def __init__(self, weeks: int = 52, initial_subscribers: int = 1000):
        self.weeks = weeks
        self.weekly_data: List[NewsletterState] = []
        self.initial_subscribers = initial_subscribers
        self.final_subscribers = initial_subscribers
        self.total_revenue = 0.0
        self.total_costs = 0.0
        self.net_profit = 0.0
        self.avg_subscribers = 0.0
        self.avg_churn_rate = 0.0
        self.total_acquired = 0
        self.final_cumulative_profit = 0.0

    def add_weekly_data(self, state: NewsletterState):
        self.weekly_data.append(state)
        self._update_stats()

    def _update_stats(self):
        if not self.weekly_data:
            return
        self.final_subscribers = self.weekly_data[-1].subscribers
        self.total_revenue = sum(s.revenue for s in self.weekly_data)
        self.total_costs = sum(s.costs for s in self.weekly_data)
        self.net_profit = self.total_revenue - self.total_costs
        self.avg_subscribers = sum(s.subscribers for s in self.weekly_data) / len(self.weekly_data)
        self.total_acquired = sum(s.acquired for s in self.weekly_data)
        self.final_cumulative_profit = self.weekly_data[-1].cumulative_profit
        total_churned = sum(s.churned for s in self.weekly_data)
        total_subs = sum(s.subscribers for s in self.weekly_data)
        self.avg_churn_rate = total_churned / total_subs if total_subs else 0.0

    def get_weekly_data(self) -> List[NewsletterState]:
        return list(self.weekly_data)

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "weeks": self.weeks,
            "initial_subscribers": self.initial_subscribers,
            "final_subscribers": self.final_subscribers,
            "total_revenue": self.total_revenue,
            "total_costs": self.total_costs,
            "net_profit": self.net_profit,
            "avg_subscribers": self.avg_subscribers,
            "avg_churn_rate": self.avg_churn_rate,
            "total_acquired": self.total_acquired,
            "final_cumulative_profit": self.final_cumulative_profit,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weeks": self.weeks,
            "initial_subscribers": self.initial_subscribers,
            "final_subscribers": self.final_subscribers,
            "total_revenue": self.total_revenue,
            "total_costs": self.total_costs,
            "net_profit": self.net_profit,
            "avg_subscribers": self.avg_subscribers,
            "avg_churn_rate": self.avg_churn_rate,
            "total_acquired": self.total_acquired,
            "final_cumulative_profit": self.final_cumulative_profit,
            "weekly_data": [s.to_dict() for s in self.weekly_data],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationHistory":
        h = cls(weeks=data.get("weeks", 52),
                initial_subscribers=data.get("initial_subscribers", 1000))
        h.final_subscribers = data.get("final_subscribers", h.initial_subscribers)
        h.total_revenue = data.get("total_revenue", 0.0)
        h.total_costs = data.get("total_costs", 0.0)
        h.net_profit = data.get("net_profit", 0.0)
        h.avg_subscribers = data.get("avg_subscribers", 0.0)
        h.avg_churn_rate = data.get("avg_churn_rate", 0.0)
        h.total_acquired = data.get("total_acquired", 0)
        h.final_cumulative_profit = data.get("final_cumulative_profit", 0.0)
        for wd in data.get("weekly_data", []):
            h.weekly_data.append(NewsletterState.from_dict(wd))
        return h

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "SimulationHistory":
        return cls.from_dict(json.loads(json_str))


class NewsletterSimulator:
    """Deterministic simulator for newsletter profit calculations.
    
    This simulator runs the newsletter business model without
    reinforcement learning components, useful for baseline analysis.
    """
    
    def __init__(self, config: Optional[SimConfig] = None):
        """Initialize the simulator.
        
        Args:
            config: Simulation configuration. If None, uses default config.
        """
        self.config = config or SimConfig()
        self.state = NewsletterState()
        self.history: List[Dict[str, Any]] = []
    
    def run_week(self) -> Dict[str, Any]:
        """Run one week of simulation.
        
        Returns:
            Dictionary containing the week's results.
        """
        # Advance week
        self.state.week += 1
        
        # Calculate subscriber dynamics
        churned = int(self.state.subscribers * self.config.churn_rate)
        acquired = int(self.state.subscribers * self.config.growth_rate)
        
        # Apply churn and acquisition
        self.state.subscribers = max(0, self.state.subscribers - churned + acquired)
        self.state.churned = churned
        self.state.acquired = acquired
        
        # Calculate revenue
        ad_revenue = self.state.subscribers * self.config.ad_rate * self.config.seasonal_factor
        sponsor_revenue = self.state.subscribers * self.config.sponsor_rate * self.config.sponsorship_fill_rate
        self.state.ad_revenue = ad_revenue
        self.state.sponsor_revenue = sponsor_revenue
        self.state.revenue = ad_revenue + sponsor_revenue
        
        # Calculate costs
        content_cost = self.config.content_cost
        operational_cost = self.config.operational_cost
        acquisition_cost = self.state.acquired * self.config.cpc
        self.state.costs = content_cost + operational_cost + acquisition_cost
        
        # Calculate profit
        self.state.profit = self.state.revenue - self.state.costs
        self.state.cumulative_profit += self.state.profit
        
        # Update engagement
        self.state.engagement_score = self.config.engagement_rate
        
        # Record history
        week_data = self.state.to_dict()
        self.history.append(week_data)
        
        return week_data
    
    def run_simulation(self, weeks: int) -> "SimulationHistory":
        """Run a complete simulation.
        
        Args:
            weeks: Number of weeks to simulate.
            
        Returns:
            SimulationHistory with all weekly data.
        """
        self.history = []
        self.state = NewsletterState(subscribers=self.config.subscriber_count)
        
        sim_history = SimulationHistory(
            weeks=weeks,
            initial_subscribers=self.config.subscriber_count,
        )
        
        for _ in range(weeks):
            self.run_week()
            # Snapshot current state
            snap = NewsletterState.from_dict(self.state.to_dict())
            sim_history.add_weekly_data(snap)
        
        return sim_history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics from simulation history.
        
        Returns:
            Dictionary containing summary statistics.
        """
        if not self.history:
            return {
                "total_revenue": 0.0,
                "total_costs": 0.0,
                "total_profit": 0.0,
                "avg_weekly_revenue": 0.0,
                "avg_weekly_profit": 0.0,
                "final_subscribers": 0,
                "total_churned": 0,
                "total_acquired": 0,
            }
        
        revenues = [h["revenue"] for h in self.history]
        profits = [h["profit"] for h in self.history]
        costs = [h["costs"] for h in self.history]
        
        return {
            "total_revenue": sum(revenues),
            "total_costs": sum(costs),
            "total_profit": sum(profits),
            "avg_weekly_revenue": np.mean(revenues),
            "avg_weekly_profit": np.mean(profits),
            "final_subscribers": self.history[-1]["subscribers"],
            "total_churned": sum(h["churned"] for h in self.history),
            "total_acquired": sum(h["acquired"] for h in self.history),
        }
    
    def reset(self):
        """Reset the simulator to initial state."""
        self.state.reset()
        self.history = []

