"""Tests for environment module."""

import pytest
import numpy as np
from profit_env.config import SimConfig
from profit_env.environment import NewsletterEnv
from profit_env.observation import Observation


class TestNewsletterEnvInitialization:
    """Test environment initialization."""
    
    def test_env_creation(self):
        env = NewsletterEnv()
        
        assert env.action_space == 4
        assert env.observation_space == 10
    
    def test_env_with_custom_config(self):
        config = SimConfig(subscriber_count=5000)
        env = NewsletterEnv(config)
        
        assert env.config.subscriber_count == 5000
    
    def test_env_observation_space(self):
        env = NewsletterEnv()
        
        assert env.observation_space == 10


class TestNewsletterEnvReset:
    """Test environment reset functionality."""
    
    def test_reset_returns_observation(self):
        env = NewsletterEnv()
        
        observation = env.reset()
        
        assert isinstance(observation, Observation)
        assert observation.subscribers > 0
        assert 0 <= observation.week <= 1
    
    def test_reset_initializes_state(self):
        env = NewsletterEnv()
        
        observation = env.reset()
        
        assert observation.subscribers > 0
        assert observation.revenue >= 0
        assert observation.profit >= 0
        assert 0 <= observation.engagement <= 1
    
    def test_reset_sets_week_to_zero(self):
        env = NewsletterEnv()
        
        observation = env.reset()
        
        assert observation.week == 0


class TestNewsletterEnvStep:
    """Test environment step functionality."""
    
    def test_step_returns_tuple(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        observation, reward, terminated, info = env.step(action)
        
        assert isinstance(observation, Observation)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(info, dict)
    
    def test_step_validates_action_shape(self):
        env = NewsletterEnv()
        env.reset()
        
        # Test with wrong shape
        with pytest.raises(ValueError):
            env.step(np.array([0.5, 0.5]))
        
        # Test with correct shape
        action = np.array([0.5, 0.5, 0.5, 0.5])
        observation, reward, terminated, info = env.step(action)
        
        assert observation is not None
    
    def test_step_updates_state(self):
        env = NewsletterEnv()
        env.reset()
        
        initial_subscribers = env.get_state().subscribers
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        env.step(action)
        
        assert env.get_state().subscribers != initial_subscribers or env.get_state().week > 0
    
    def test_step_calculates_reward(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        observation, reward, terminated, info = env.step(action)
        
        assert isinstance(reward, float)
        # Reward should be based on profit and growth
        assert "profit" in info
        assert "subscribers" in info
    
    def test_step_updates_engagement(self):
        env = NewsletterEnv()
        env.reset()
        
        initial_engagement = env.get_state().engagement_score
        
        action = np.array([1.0, 1.0, 0.0, 1.0])
        env.step(action)
        
        assert env.get_state().engagement_score >= initial_engagement
    
    def test_step_updates_growth_rate(self):
        env = NewsletterEnv()
        env.reset()
        
        initial_growth = env.get_state().growth_rate
        
        action = np.array([1.0, 0.0, 0.0, 0.0])
        env.step(action)
        
        assert env.get_state().growth_rate >= initial_growth
    
    def test_step_updates_churn_rate(self):
        env = NewsletterEnv()
        env.reset()
        
        initial_churn = env.get_state().churn_rate
        
        action = np.array([0.0, 0.0, 0.0, 1.0])
        env.step(action)
        
        assert env.get_state().churn_rate <= initial_churn


class TestNewsletterEnvTermination:
    """Test environment termination conditions."""
    
    def test_termination_after_max_steps(self):
        config = SimConfig(max_steps=5)
        env = NewsletterEnv(config)
        env.reset()
        
        terminated = False
        for _ in range(5):
            action = np.array([0.5, 0.5, 0.5, 0.5])
            _, _, terminated, _ = env.step(action)
        
        assert terminated
    
    def test_no_termination_before_max_steps(self):
        config = SimConfig(max_steps=10)
        env = NewsletterEnv(config)
        env.reset()
        
        for _ in range(5):
            action = np.array([0.5, 0.5, 0.5, 0.5])
            _, _, terminated, _ = env.step(action)
            assert not terminated


class TestNewsletterEnvObservation:
    """Test observation creation."""
    
    def test_observation_contains_all_features(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        observation, _, _, _ = env.step(action)
        
        assert hasattr(observation, "subscribers")
        assert hasattr(observation, "revenue")
        assert hasattr(observation, "profit")
        assert hasattr(observation, "engagement")
        assert hasattr(observation, "week")
        assert hasattr(observation, "cumulative_profit")
        assert hasattr(observation, "churn_rate")
        assert hasattr(observation, "growth_rate")
        assert hasattr(observation, "sponsor_revenue")
        assert hasattr(observation, "ad_revenue")
    
    def test_observation_normalized(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        observation, _, _, _ = env.step(action)
        
        # Check that values are normalized
        assert 0 <= observation.subscribers <= 1
        assert 0 <= observation.revenue <= 1
        assert 0 <= observation.profit <= 1
        assert 0 <= observation.engagement <= 1
        assert 0 <= observation.week <= 1


class TestNewsletterEnvStateAccess:
    """Test state access methods."""
    
    def test_get_state_returns_current_state(self):
        env = NewsletterEnv()
        env.reset()
        
        state = env.get_state()
        
        assert state is not None
        assert state.week == 0
        assert state.subscribers == 1000
    
    def test_get_history_returns_history(self):
        env = NewsletterEnv()
        env.reset()
        
        history = env.get_history()
        
        assert history is not None
        assert len(history) == 0
    
    def test_get_statistics(self):
        env = NewsletterEnv()
        env.reset()
        
        stats = env.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_revenue" in stats
        assert "net_profit" in stats


class TestNewsletterEnvSimulation:
    """Test simulation methods."""
    
    def test_run_simulation(self):
        env = NewsletterEnv()
        env.reset()
        
        history = env.run_simulation(5)
        
        assert len(history) == 5
        assert env.get_state().week == 5
    
    def test_run_simulation_with_random_actions(self):
        env = NewsletterEnv()
        env.reset()
        
        for _ in range(5):
            action = np.random.rand(4)
            env.step(action)
        
        history = env.get_history()
        
        assert len(history) == 5


class TestNewsletterEnvConfiguration:
    """Test configuration methods."""
    
    def test_set_config(self):
        env = NewsletterEnv()
        
        new_config = SimConfig(subscriber_count=5000)
        env.set_config(new_config)
        
        assert env.config.subscriber_count == 5000
    
    def test_set_seed(self):
        env1 = NewsletterEnv()
        env2 = NewsletterEnv()
        
        env1.set_seed(42)
        env2.set_seed(42)
        
        # Both should have same random state
        assert env1._rng.bit_generator.state == env2._rng.bit_generator.state


class TestNewsletterEnvObservationSpace:
    """Test observation space properties."""
    
    def test_observation_length(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        observation, _, _, _ = env.step(action)
        
        assert len(observation) == 10
    
    def test_observation_dict_conversion(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        observation, _, _, _ = env.step(action)
        
        obs_dict = observation.to_dict()
        
        assert len(obs_dict) == 10
        assert "subscribers" in obs_dict
        assert "revenue" in obs_dict
        assert "profit" in obs_dict


class TestNewsletterEnvReward:
    """Test reward calculation."""
    
    def test_reward_positive_with_profit(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        _, reward, _, _ = env.step(action)
        
        # Reward should be positive when there's profit
        assert reward >= 0
    
    def test_reward_includes_growth_component(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([1.0, 0.5, 0.5, 0.5])
        _, reward, _, info = env.step(action)
        
        # Reward should include subscriber growth component
        assert "acquired" in info
        assert "churned" in info
    
    def test_reward_includes_engagement_component(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 1.0, 0.5, 0.5])
        _, reward, _, info = env.step(action)
        
        # Reward should include engagement component
        assert "engagement_score" in info


class TestNewsletterEnvEdgeCases:
    """Test edge cases and error handling."""
    
    def test_action_with_wrong_length(self):
        env = NewsletterEnv()
        env.reset()
        
        with pytest.raises(ValueError):
            env.step(np.array([0.5, 0.5]))
        
        with pytest.raises(ValueError):
            env.step(np.array([0.5, 0.5, 0.5, 0.5, 0.5]))
    
    def test_action_values_in_range(self):
        env = NewsletterEnv()
        env.reset()
        
        # Test with values outside [0, 1]
        action = np.array([1.5, -0.5, 0.5, 0.5])
        observation, reward, terminated, info = env.step(action)
        
        # Environment should handle out-of-range values
        assert observation is not None
        assert isinstance(reward, float)
    
    def test_very_short_simulation(self):
        env = NewsletterEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        observation, reward, terminated, info = env.step(action)
        
        assert observation is not None
        assert not terminated
    
    def test_very_long_simulation(self):
        config = SimConfig(max_steps=100)
        env = NewsletterEnv(config)
        env.reset()
        
        for _ in range(100):
            action = np.array([0.5, 0.5, 0.5, 0.5])
            _, _, terminated, _ = env.step(action)
        
        assert terminated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
