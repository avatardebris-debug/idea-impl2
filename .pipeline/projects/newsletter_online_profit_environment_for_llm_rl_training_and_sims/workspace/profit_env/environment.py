"""Environment module for the Newsletter Online Profit Environment."""

import gymnasium as gym
import numpy as np
from typing import Dict, Tuple, Any, Optional
from .config import SimConfig
from .state import NewsletterState
from .simulator import NewsletterSimulator


class NewsletterEnv(gym.Env):
    """Gymnasium environment for the newsletter business simulation.
    
    This environment wraps the NewsletterSimulator and provides a standard
    Gymnasium interface for reinforcement learning training.
    """
    
    metadata = {"render_modes": ["human"], "render_fps": 1}
    
    def __init__(
        self,
        config: Optional[SimConfig] = None,
        max_steps: int = 52,
        render_mode: Optional[str] = None,
    ):
        """Initialize the environment.
        
        Args:
            config: Simulation configuration. Uses default if None.
            max_steps: Maximum number of steps per episode.
            render_mode: Rendering mode for visualization.
        """
        super().__init__()
        
        self.config = config or SimConfig()
        self.max_steps = max_steps
        self.render_mode = render_mode
        
        # Action space: [content_quality, marketing_spend, pricing_tier, engagement]
        self.action_space = gym.spaces.Box(
            low=0.0,
            high=1.0,
            shape=(4,),
            dtype=np.float32,
        )
        
        # Observation space
        self.observation_space = gym.spaces.Dict({
            "subscriber_count": gym.spaces.Box(low=0.0, high=1e6, dtype=np.float32),
            "churn_rate": gym.spaces.Box(low=0.0, high=1.0, dtype=np.float32),
            "acquisition_rate": gym.spaces.Box(low=0.0, high=1.0, dtype=np.float32),
            "revenue": gym.spaces.Box(low=0.0, high=1e6, dtype=np.float32),
            "costs": gym.spaces.Box(low=0.0, high=1e6, dtype=np.float32),
            "profit": gym.spaces.Box(low=-1e6, high=1e6, dtype=np.float32),
            "engagement_score": gym.spaces.Box(low=0.0, high=1.0, dtype=np.float32),
            "week_number": gym.spaces.Box(low=0.0, high=52.0, dtype=np.float32),
            "seasonal_factor": gym.spaces.Box(low=0.0, high=2.0, dtype=np.float32),
            "competitor_pressure": gym.spaces.Box(low=0.0, high=1.0, dtype=np.float32),
        })
        
        self.simulator = NewsletterSimulator(self.config)
        self.current_step = 0
        self._last_obs = None
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """Reset the environment to initial state.
        
        Args:
            seed: Random seed for reproducibility.
            options: Additional reset options.
            
        Returns:
            Tuple of (observation, info).
        """
        if seed is not None:
            np.random.seed(seed)
        
        self.simulator.reset()
        self.current_step = 0
        
        # Initial observation
        obs = self._get_observation()
        info = {
            "initial_subscribers": self.config.subscriber_count,
            "week": 0,
            "subscribers": self.config.subscriber_count,
            "revenue": 0.0,
            "costs": 0.0,
            "profit": 0.0,
            "churned": 0,
            "acquired": 0,
        }
        
        self._last_obs = obs
        return obs, info
    
    def step(self, action: np.ndarray) -> Tuple[Dict[str, float], float, bool, bool, Dict[str, Any]]:
        """Execute one step in the environment.
        
        Args:
            action: Action vector [content_quality, marketing_spend, pricing_tier, engagement].
            
        Returns:
            Tuple of (observation, reward, terminated, truncated, info).
        """
        # Clamp action values to [0, 1]
        action = np.clip(action, 0.0, 1.0)
        
        # Apply action effects to config
        content_quality = action[0]
        marketing_spend = action[1]
        pricing_tier = action[2]
        engagement_action = action[3]
        
        # Calculate seasonal factor based on week
        seasonal_factor = 1.0 + 0.2 * np.sin(2 * np.pi * self.current_step / 52)
        
        # Calculate competitor pressure
        competitor_pressure = self.config.competitor_count / 10.0
        
        # Update config with action effects
        effective_growth = self.config.growth_rate * (1 + marketing_spend)
        effective_churn = self.config.churn_rate * (1 - engagement_action * 0.5)
        effective_arpu = self.config.arpu * (1 + pricing_tier * 0.5)
        
        # Run simulation week
        self.simulator.run_week()
        
        # Apply action-modified parameters
        self.simulator.state.subscribers = max(
            0,
            self.simulator.state.subscribers + 
            int(self.simulator.state.subscribers * marketing_spend * 0.1) -
            int(self.simulator.state.subscribers * effective_churn * 0.1)
        )
        
        # Update current step
        self.current_step += 1
        
        # Calculate reward (scaled profit)
        reward = self.simulator.state.profit / 1000.0
        
        # Check termination conditions
        terminated = False
        if self.simulator.state.subscribers <= 0:
            terminated = True
        if self.current_step >= self.max_steps:
            terminated = True
        
        # Get observation
        obs = self._get_observation()
        
        # Build info dict
        info = {
            "week": self.simulator.state.week,
            "subscribers": self.simulator.state.subscribers,
            "revenue": self.simulator.state.revenue,
            "costs": self.simulator.state.costs,
            "profit": self.simulator.state.profit,
            "churned": self.simulator.state.churned,
            "acquired": self.simulator.state.acquired,
            "seasonal_factor": seasonal_factor,
            "competitor_pressure": competitor_pressure,
        }
        
        truncated = False
        
        return obs, reward, terminated, truncated, info
    
    def _get_observation(self) -> Dict[str, float]:
        """Get current observation from the simulator state."""
        state = self.simulator.state
        
        return {
            "subscriber_count": float(state.subscribers),
            "churn_rate": float(self.config.churn_rate),
            "acquisition_rate": float(self.config.growth_rate),
            "revenue": float(state.revenue),
            "costs": float(state.costs),
            "profit": float(state.profit),
            "engagement_score": float(state.engagement_score),
            "week_number": float(state.week),
            "seasonal_factor": float(self.config.seasonal_factor),
            "competitor_pressure": float(self.config.competitor_count / 10.0),
        }
    
    def render(self) -> Optional[str]:
        """Render the current state of the environment."""
        if self.render_mode != "human":
            return None
        
        state = self.simulator.state
        output = f"Week {state.week}: {state.subscribers} subscribers, "
        output += f"${state.revenue:.2f} revenue, ${state.costs:.2f} costs, "
        output += f"${state.profit:.2f} profit"
        
        if self.render_mode == "human":
            print(output)
        
        return output
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulation statistics."""
        return self.simulator.get_statistics()
    
    def close(self) -> None:
        """Clean up the environment."""
        pass
