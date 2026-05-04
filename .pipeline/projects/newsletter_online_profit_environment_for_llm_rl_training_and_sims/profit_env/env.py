"""Gymnasium environment for newsletter profit simulation."""

from __future__ import annotations

import gymnasium as gym
import numpy as np
from typing import Optional

from .config import SimConfig
from .simulator import NewsletterSimulator
from .state import NewsletterState


class NewsletterEnv(gym.Env):
    """Gymnasium environment for newsletter profit simulation.

    Action space: 5 actions
        0: No action (default)
        1: Increase marketing spend
        2: Decrease marketing spend
        3: Increase content quality
        4: Decrease content quality

    Observation space: 8-dimensional normalized vector
        [month_normalized, subscribers_normalized, revenue_normalized,
         profit_normalized, cumulative_profit_normalized, growth_rate_normalized,
         churn_rate_normalized, marketing_cost_normalized]
    """

    metadata = {"render_modes": ["human"], "render_fps": 1}

    def __init__(
        self,
        config: Optional[SimConfig] = None,
        render_mode: Optional[str] = None,
    ) -> None:
        """Initialize the environment.

        Args:
            config: Simulation configuration.
            render_mode: Render mode for visualization.
        """
        super().__init__()

        self.config = config or SimConfig()
        self.render_mode = render_mode

        # Action space: 5 discrete actions
        self.action_space = gym.spaces.Discrete(5)

        # Observation space: 8 normalized values
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(8,), dtype=np.float64
        )

        self.simulator: Optional[NewsletterSimulator] = None
        self._max_subscribers = 10000.0
        self._max_revenue = 50000.0
        self._max_profit = 50000.0
        self._max_cumulative_profit = 100000.0
        self._max_month = 12.0

    def _get_obs(self) -> np.ndarray:
        """Get current observation, normalized to [0, 1]."""
        state = self.simulator.current_state
        obs = np.array([
            state.month / self._max_month,
            state.subscribers / self._max_subscribers,
            state.revenue / self._max_revenue,
            state.profit / self._max_profit,
            state.cumulative_profit / self._max_cumulative_profit,
            self.config.growth_rate,
            self.config.churn_rate,
            self.config.marketing_cost / self._max_revenue,
        ], dtype=np.float64)
        # Clip to [0, 1]
        obs = np.clip(obs, 0.0, 1.0)
        return obs

    def _get_info(self) -> dict:
        """Get current info dict."""
        state = self.simulator.current_state
        return {
            "month": state.month,
            "subscribers": state.subscribers,
            "revenue": state.revenue,
            "costs": state.costs,
            "profit": state.profit,
            "cumulative_profit": state.cumulative_profit,
            "is_terminated": state.is_terminated,
        }

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
    ):
        """Reset the environment.

        Args:
            seed: Random seed.
            options: Additional reset options.

        Returns:
            Tuple of (observation, info).
        """
        super().reset(seed=seed)
        self.config = SimConfig(seed=seed)
        self.simulator = NewsletterSimulator(self.config)
        self.simulator.reset()
        obs = self._get_obs()
        info = self._get_info()
        return obs, info

    def step(self, action: int):
        """Execute one environment step.

        Args:
            action: Action to take (0-4).

        Returns:
            Tuple of (observation, reward, terminated, truncated, info).
        """
        # Apply action effects
        if action == 1:
            # Increase marketing
            self.config.growth_rate = min(0.5, self.config.growth_rate + 0.02)
            self.config.marketing_cost = min(5000.0, self.config.marketing_cost + 100.0)
        elif action == 2:
            # Decrease marketing
            self.config.growth_rate = max(0.0, self.config.growth_rate - 0.02)
            self.config.marketing_cost = max(0.0, self.config.marketing_cost - 100.0)
        elif action == 3:
            # Increase content quality
            self.config.content_cost = min(10000.0, self.config.content_cost + 200.0)
            self.config.growth_rate = min(0.5, self.config.growth_rate + 0.01)
        elif action == 4:
            # Decrease content quality
            self.config.content_cost = max(0.0, self.config.content_cost - 200.0)
            self.config.churn_rate = min(1.0, self.config.churn_rate + 0.01)

        # Step the simulator
        state = self.simulator.step()

        # Calculate reward (cumulative profit)
        reward = float(state.cumulative_profit)

        # Check termination
        terminated = state.is_terminated
        truncated = False

        obs = self._get_obs()
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def render(self) -> Optional[str]:
        """Render the environment.

        Returns:
            String representation of the current state, or None if not in human mode.
        """
        if self.render_mode != "human":
            return None

        state = self.simulator.current_state
        render_str = (
            f"Month: {state.month}\n"
            f"Subscribers: {state.subscribers}\n"
            f"Revenue: ${state.revenue:.2f}\n"
            f"Profit: ${state.profit:.2f}\n"
            f"Cumulative Profit: ${state.cumulative_profit:.2f}\n"
        )
        return render_str

    def close(self) -> None:
        """Close the environment."""
        pass
