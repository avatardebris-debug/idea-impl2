"""Tests for the dropshipping environment."""

import pytest
import numpy as np
import gymnasium as gym

from rl_dropshipping.src.env.dropshipping_env import DropshippingEnv


class TestDropshippingEnv:
    """Tests for DropshippingEnv."""

    def test_env_creation(self):
        """Test environment creation."""
        env = gym.make("Dropshipping-v0")
        assert env is not None
        assert env.observation_space.shape == (17,)
        assert env.action_space.n == 200
        env.close()

    def test_reset(self):
        """Test environment reset."""
        env = gym.make("Dropshipping-v0")
        obs, info = env.reset()
        assert isinstance(obs, np.ndarray)
        assert obs.shape == (17,)
        assert "episode_reward" in info
        env.close()

    def test_reset_with_seed(self):
        """Test environment reset with seed."""
        env = gym.make("Dropshipping-v0")
        obs1, _ = env.reset(seed=42)
        obs2, _ = env.reset(seed=42)
        np.testing.assert_array_equal(obs1, obs2)
        env.close()

    def test_step(self):
        """Test environment step."""
        env = gym.make("Dropshipping-v0")
        obs, info = env.reset()
        action = env.action_space.sample()
        next_obs, reward, terminated, truncated, info = env.step(action)
        assert isinstance(next_obs, np.ndarray)
        assert next_obs.shape == (17,)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        env.close()

    def test_step_after_done(self):
        """Test that step raises error after episode is done."""
        env = gym.make("Dropshipping-v0")
        raw_env = env.unwrapped
        obs, info = env.reset()
        # Run until done
        done = False
        while not done:
            action = env.action_space.sample()
            _, _, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        # Use unwrapped env to test done flag behavior
        with pytest.raises(RuntimeError, match="Episode is done"):
            raw_env.step(raw_env.action_space.sample())
        env.close()

    def test_observation_space(self):
        """Test observation space bounds."""
        env = gym.make("Dropshipping-v0")
        obs, _ = env.reset()
        assert obs.dtype == np.float64
        env.close()

    def test_action_space(self):
        """Test action space."""
        env = gym.make("Dropshipping-v0")
        action = env.action_space.sample()
        assert 0 <= action < env.action_space.n
        env.close()

    def test_episode_length(self):
        """Test that episode terminates at episode length."""
        env = gym.make("Dropshipping-v0")
        obs, info = env.reset()
        truncated = False
        for _ in range(env.spec.max_episode_steps + 1):
            action = env.action_space.sample()
            _, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        assert truncated or terminated
        env.close()

    def test_budget_tracking(self):
        """Test that budget is tracked correctly."""
        env = gym.make("Dropshipping-v0")
        obs, info = env.reset()
        unwrapped = env.unwrapped
        initial_budget = unwrapped.initial_budget
        for _ in range(10):
            action = env.action_space.sample()
            _, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        assert unwrapped.budget <= initial_budget
        env.close()

    def test_inventory_tracking(self):
        """Test that inventory is tracked correctly."""
        env = gym.make("Dropshipping-v0")
        obs, info = env.reset()
        unwrapped = env.unwrapped
        for _ in range(10):
            action = env.action_space.sample()
            _, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        assert unwrapped.inventory >= 0
        assert unwrapped.inventory <= unwrapped.max_inventory
        env.close()

    def test_info_dict(self):
        """Test that info dict contains expected keys."""
        env = gym.make("Dropshipping-v0")
        obs, info = env.reset()
        action = env.action_space.sample()
        _, _, _, _, info = env.step(action)
        assert "episode_reward" in info
        assert "step_revenue" in info
        assert "step_cost" in info
        assert "n_sales" in info
        env.close()

    def test_render_mode(self):
        """Test render mode."""
        env = gym.make("Dropshipping-v0", render_mode="ansi")
        obs, info = env.reset()
        env.render()
        action = env.action_space.sample()
        env.step(action)
        env.render()
        env.close()
