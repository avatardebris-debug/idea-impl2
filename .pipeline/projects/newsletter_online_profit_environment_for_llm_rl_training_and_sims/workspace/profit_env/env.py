"""Environment module for the Newsletter Online Profit Environment."""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Any, Optional
from .config import SimConfig
from .state import NewsletterState


class NewsletterEnv(gym.Env):
    """Gymnasium environment for newsletter profit simulation.
    
    This environment simulates a newsletter business where the agent
    can control the acquisition channel mix to optimize profit.
    """
    
    metadata = {'render.modes': ['human']}
    
    def __init__(self, config: Optional[SimConfig] = None):
        """Initialize the environment.
        
        Args:
            config: Simulation configuration. If None, uses default config.
        """
        super().__init__()
        
        self.config = config or SimConfig()
        self.state = NewsletterState()
        self.done = False
        
        # Action space: 4 values for channel mix adjustments (organic, paid, social, referral)
        self.action_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0, 0.0]),
            high=np.array([1.0, 1.0, 1.0, 1.0]),
            dtype=np.float32
        )
        
        # Observation space: current state metrics
        self.observation_space = spaces.Dict({
            "subscribers": spaces.Box(low=0, high=np.inf, dtype=np.float32),
            "revenue": spaces.Box(low=-np.inf, high=np.inf, dtype=np.float32),
            "costs": spaces.Box(low=-np.inf, high=np.inf, dtype=np.float32),
            "profit": spaces.Box(low=-np.inf, high=np.inf, dtype=np.float32),
            "engagement": spaces.Box(low=0, high=1, dtype=np.float32),
        })
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """Reset the environment to initial state.
        
        Args:
            seed: Random seed for reproducibility.
            options: Additional options for reset.
            
        Returns:
            Tuple of (observation, info)
        """
        super().reset(seed=seed)
        
        self.state.reset()
        self.done = False
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def step(self, action: np.ndarray) -> Tuple[Dict[str, float], float, bool, bool, Dict[str, Any]]:
        """Execute one time step in the environment.
        
        Args:
            action: Action vector representing channel mix adjustments.
            
        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        # Validate action
        if not isinstance(action, np.ndarray):
            action = np.array(action)
        
        # Apply action to update channel mix
        self._apply_action(action)
        
        # Advance simulation
        self._advance_week()
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check termination conditions
        terminated = self._check_terminated()
        truncated = self._check_truncated()
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, reward, terminated, truncated, info
    
    def _apply_action(self, action: np.ndarray):
        """Apply action to update channel mix.
        
        Args:
            action: Action vector representing channel mix adjustments.
        """
        # Normalize action to sum to 1
        action_sum = action.sum()
        if action_sum > 0:
            normalized_action = action / action_sum
        else:
            normalized_action = np.ones(4) / 4
        
        # Update channel mix
        self.config.acquisition_channel_mix = {
            "organic": float(normalized_action[0]),
            "paid": float(normalized_action[1]),
            "social": float(normalized_action[2]),
            "referral": float(normalized_action[3])
        }
    
    def _advance_week(self):
        """Advance the simulation by one week."""
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
    
    def _calculate_reward(self) -> float:
        """Calculate reward based on current state.
        
        Returns:
            Reward value proportional to profit.
        """
        # Reward is proportional to profit
        return float(self.state.profit)
    
    def _check_terminated(self) -> bool:
        """Check if episode is terminated.
        
        Returns:
            True if episode should terminate.
        """
        # Terminate if subscribers reach 0
        return self.state.subscribers <= 0
    
    def _check_truncated(self) -> bool:
        """Check if episode is truncated.
        
        Returns:
            True if episode should be truncated.
        """
        # Truncate after max weeks (52)
        return self.state.week >= 52
    
    def _get_observation(self) -> Dict[str, float]:
        """Get current observation.
        
        Returns:
            Dictionary containing current state metrics.
        """
        return {
            "subscribers": float(self.state.subscribers),
            "revenue": float(self.state.revenue),
            "costs": float(self.state.costs),
            "profit": float(self.state.profit),
            "engagement": float(self.state.engagement_score),
        }
    
    def _get_info(self) -> Dict[str, Any]:
        """Get current info.
        
        Returns:
            Dictionary containing detailed state information.
        """
        return {
            "week": self.state.week,
            "subscribers": self.state.subscribers,
            "revenue": self.state.revenue,
            "costs": self.state.costs,
            "profit": self.state.profit,
            "cumulative_profit": self.state.cumulative_profit,
            "churned": self.state.churned,
            "acquired": self.state.acquired,
            "engagement_score": self.state.engagement_score,
            "sponsor_revenue": self.state.sponsor_revenue,
            "ad_revenue": self.state.ad_revenue,
            "channel_mix": self.config.acquisition_channel_mix,
        }
    
    def render(self, mode: str = 'human'):
        """Render the environment.
        
        Args:
            mode: Rendering mode.
        """
        if mode == 'human':
            print(f"Week {self.state.week}: {self.state.subscribers} subscribers, "
                  f"Revenue: ${self.state.revenue:.2f}, "
                  f"Profit: ${self.state.profit:.2f}")
    
    def close(self):
        """Close the environment."""
        pass
