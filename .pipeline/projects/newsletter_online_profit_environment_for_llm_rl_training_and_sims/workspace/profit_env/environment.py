"""Environment module for the Newsletter Online Profit Environment."""

import numpy as np
from typing import Dict, Any, Tuple, Optional

from .config import SimConfig
from .state import NewsletterState, SimulationHistory, SimulationRecord
from .simulator import NewsletterSimulator
from .observation import Observation


class NewsletterEnv:
    """Newsletter Online Profit Environment.
    
    A simulation environment for training RL agents to manage a newsletter business.
    The agent controls marketing, content, pricing, and retention strategies.
    """
    
    def __init__(self, config: Optional[SimConfig] = None):
        """Initialize the environment.
        
        Args:
            config: Simulation configuration. Uses default if None.
        """
        self.config = config or SimConfig()
        self.simulator = NewsletterSimulator(self.config, env=self)
        self.action_space = 4  # [marketing, content, pricing, retention]
        self.observation_space = 10  # 10 observation features
        self._rng = np.random.default_rng()
    
    def reset(self) -> Observation:
        """Reset the environment to initial state.
        
        Returns:
            Initial observation
        """
        self.simulator.reset()
        return self._create_observation()
    
    def step(self, action: np.ndarray) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """Execute one step in the environment.
        
        Args:
            action: Action array of shape (4,) with values in [0, 1]
            
        Returns:
            Tuple of (observation, reward, terminated, info)
        """
        # Validate action
        if len(action) != self.action_space:
            raise ValueError(f"Action must have {self.action_space} elements")
        
        # Execute step
        state, info = self.simulator.step(action)
        
        # Create observation
        observation = self._create_observation()
        
        # Calculate reward
        reward = self._calculate_reward(info)
        
        # Check termination
        terminated = state.week >= self.config.max_steps
        
        return observation, reward, terminated, info
    
    def _create_observation(self) -> Observation:
        """Create observation from current state.
        
        Returns:
            Observation object with current state features
        """
        state = self.simulator.state
        
        # Normalize values for observation
        subscribers_norm = min(state.subscribers / 10000.0, 1.0)
        revenue_norm = min(state.revenue / 10000.0, 1.0)
        profit_norm = min(state.profit / 1000.0, 1.0)
        engagement_norm = state.engagement_score
        
        return Observation(
            subscribers=subscribers_norm,
            revenue=revenue_norm,
            profit=profit_norm,
            engagement=engagement_norm,
            week=state.week / self.config.max_steps,
            cumulative_profit=state.cumulative_profit / 10000.0,
            churn_rate=state.churn_rate,
            growth_rate=state.growth_rate,
            sponsor_revenue=state.sponsor_revenue / 10000.0,
            ad_revenue=state.ad_revenue / 10000.0
        )
    
    def _calculate_reward(self, info: Dict) -> float:
        """Calculate reward for the current step.
        
        Args:
            info: Dictionary containing simulation info
            
        Returns:
            Reward value
        """
        # Primary reward: profit
        profit = info.get("profit", 0.0)
        
        # Secondary rewards
        subscriber_growth = info.get("acquired", 0) - info.get("churned", 0)
        engagement_bonus = info.get("engagement", 0.5) * 10
        
        # Combine rewards
        reward = profit * 0.7 + subscriber_growth * 0.2 + engagement_bonus * 0.1
        
        return reward
    
    def get_state(self) -> NewsletterState:
        """Get current simulation state.
        
        Returns:
            Current NewsletterState object
        """
        return self.simulator.state
    
    def get_history(self) -> SimulationHistory:
        """Get simulation history.
        
        Returns:
            SimulationHistory object with all recorded data
        """
        return self.simulator.history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics.
        
        Returns:
            Dictionary containing aggregated statistics
        """
        return self.simulator.get_statistics()
    
    def run_simulation(self, weeks: int) -> SimulationHistory:
        """Run simulation for specified number of weeks.
        
        Args:
            weeks: Number of weeks to simulate
            
        Returns:
            SimulationHistory object with results
        """
        self.simulator.run_simulation(weeks)
        return self.simulator.history
    
    def set_config(self, config: SimConfig):
        """Update simulation configuration.
        
        Args:
            config: New configuration to use
        """
        self.config = config
        self.simulator = NewsletterSimulator(config)
    
    def set_seed(self, seed: int):
        """Set random seed for reproducibility.
        
        Args:
            seed: Random seed value
        """
        self._rng = np.random.default_rng(seed)
        self.simulator.set_seed(seed)
