"""Simulator module for the Newsletter Online Profit Environment."""

import numpy as np
from typing import List, Dict, Any, Optional
from .config import SimConfig
from .state import NewsletterState


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
    
    def run_simulation(self, weeks: int) -> List[Dict[str, Any]]:
        """Run a complete simulation.
        
        Args:
            weeks: Number of weeks to simulate.
            
        Returns:
            List of dictionaries containing weekly results.
        """
        self.history = []
        
        for _ in range(weeks):
            week_data = self.run_week()
        
        return self.history
    
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
