"""Simulator module for the Newsletter Online Profit Environment."""

import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from .config import SimConfig
from .state import NewsletterState, SimulationHistory, SimulationRecord


class NewsletterSimulator:
    """Newsletter simulation engine.
    
    This class runs the newsletter simulation week by week,
    tracking subscriber growth, revenue, costs, and profitability.
    """
    
    def __init__(self, config: Optional[SimConfig] = None, env=None):
        """Initialize the simulator with configuration.
        
        Args:
            config: Simulation configuration parameters. If None, uses default config.
            env: Optional environment reference for integration
        """
        self.config = config if config is not None else SimConfig()
        self.env = env
        self.state = NewsletterState(
            subscribers=self.config.subscriber_count,
            engagement_score=self.config.engagement_rate
        )
        self.history = SimulationHistory()
        self._rng = np.random.default_rng()
        self._action_space = 10
    
    @property
    def action_space(self) -> int:
        """Return the action space size."""
        return self._action_space
    
    def run_week(self) -> Dict:
        """Execute one week of simulation.
        
        Returns:
            Dictionary containing week's simulation data
        """
        # Calculate subscriber changes
        churned = int(self.state.subscribers * self.config.get_effective_churn_rate(self.state.engagement_score))
        acquired = int(self.state.subscribers * self.config.get_effective_growth_rate(self.state.engagement_score))
        
        # Apply seasonal factor
        seasonal_multiplier = self.config.seasonal_factor
        
        # Update subscribers
        self.state.subscribers = max(0, self.state.subscribers - churned + acquired)
        
        # Calculate revenue
        sponsor_revenue = self.state.subscribers * self.config.sponsor_rate * self.config.sponsorship_fill_rate
        ad_revenue = self.state.subscribers * self.config.ad_rate
        subscription_revenue = self.state.subscribers * self.config.arpu
        total_revenue = subscription_revenue + sponsor_revenue + ad_revenue
        
        # Calculate costs
        content_cost = self.config.content_cost
        operational_cost = self.config.operational_cost
        acquisition_cost = acquired * self.config.cpc
        total_costs = content_cost + operational_cost + acquisition_cost
        
        # Calculate profit
        profit = total_revenue - total_costs
        self.state.cumulative_profit += profit
        
        # Update engagement score
        self.state.engagement_score = self.config.engagement_rate
        
        # Update state
        self.state.week += 1
        self.state.revenue = total_revenue
        self.state.costs = total_costs
        self.state.sponsor_revenue = sponsor_revenue
        self.state.ad_revenue = ad_revenue
        self.state.churned = churned
        self.state.acquired = acquired
        
        # Record history - add as SimulationRecord
        record = SimulationRecord(
            week=self.state.week,
            subscribers=self.state.subscribers,
            revenue=self.state.revenue,
            costs=self.state.costs,
            profit=self.state.profit,
            cumulative_profit=self.state.cumulative_profit,
            churned=self.state.churned,
            acquired=self.state.acquired,
            engagement=self.state.engagement_score,
            sponsor_revenue=self.state.sponsor_revenue,
            ad_revenue=self.state.ad_revenue,
            churn_rate=self.state.churn_rate,
            growth_rate=self.state.growth_rate,
            arpu=self.state.arpu
        )
        self.history.add_record(record)
        
        return self.state.to_dict()
    
    def step(self, action: int) -> Tuple[NewsletterState, Dict]:
        """Execute one step with action.
        
        Args:
            action: Action integer in range [0, 9]
            
        Returns:
            Tuple of (state, info)
        """
        # Run the week
        record = self.run_week()
        
        return self.state, record
    
    def run_simulation(self, weeks: int, seed: Optional[int] = None) -> List[Dict]:
        """Run simulation for specified number of weeks.
        
        Args:
            weeks: Number of weeks to simulate
            seed: Optional random seed for reproducibility
            
        Returns:
            List of dictionaries containing weekly simulation data
        """
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        
        for _ in range(weeks):
            self.run_week()
        
        return self.history.get_weekly_data()
    
    def run_multiple_simulations(self, num_simulations: int, weeks: int, seed: Optional[int] = None) -> List[List[Dict]]:
        """Run multiple simulations.
        
        Args:
            num_simulations: Number of simulations to run
            weeks: Number of weeks per simulation
            seed: Optional random seed for reproducibility
            
        Returns:
            List of lists containing weekly simulation data for each simulation
        """
        histories = []
        for i in range(num_simulations):
            sim_seed = seed + i if seed is not None else None
            self.reset()
            if sim_seed is not None:
                self._rng = np.random.default_rng(sim_seed)
            history = self.run_simulation(weeks)
            histories.append(history)
        
        return histories
    
    def get_statistics(self) -> Dict:
        """Get simulation statistics.
        
        Returns:
            Dictionary containing aggregated statistics
        """
        stats = self.history.get_statistics()
        
        # Add additional statistics
        records = self.history.get_weekly_data()
        if records:
            stats["avg_engagement"] = sum(r["engagement"] for r in records) / len(records)
            stats["avg_sponsor_revenue"] = sum(r["sponsor_revenue"] for r in records) / len(records)
            stats["avg_ad_revenue"] = sum(r["ad_revenue"] for r in records) / len(records)
        else:
            stats["avg_engagement"] = 0.0
            stats["avg_sponsor_revenue"] = 0.0
            stats["avg_ad_revenue"] = 0.0
        
        # Add expected keys for tests
        stats["churn_rate"] = self.state.churn_rate
        stats["growth_rate"] = self.state.growth_rate
        stats["arpu"] = self.state.arpu
        
        return stats
    
    def reset(self):
        """Reset simulator to initial state."""
        self.state = NewsletterState(
            subscribers=self.config.subscriber_count,
            engagement_score=self.config.engagement_rate
        )
        self.history = SimulationHistory()
    
    def get_state(self) -> NewsletterState:
        """Get current simulation state.
        
        Returns:
            Current NewsletterState object
        """
        return self.state
    
    def set_seed(self, seed: int):
        """Set random seed for reproducibility.
        
        Args:
            seed: Random seed value
        """
        self._rng = np.random.default_rng(seed)
        self.reset()
    
    def set_config(self, config: SimConfig):
        """Set simulation configuration.
        
        Args:
            config: New configuration parameters
        """
        self.config = config
        self.reset()
    
    def get_history(self) -> SimulationHistory:
        """Get simulation history.
        
        Returns:
            SimulationHistory object with all recorded data
        """
        return self.history
