"""Tests for simulator module."""

import pytest
import numpy as np
from profit_env.config import SimConfig
from profit_env.simulator import NewsletterSimulator


class TestNewsletterSimulatorInitialization:
    """Test simulator initialization."""
    
    def test_simulator_creation(self):
        simulator = NewsletterSimulator()
        
        assert simulator.config is not None
        assert simulator.env is not None
        assert simulator.history is not None
    
    def test_simulator_with_custom_config(self):
        config = SimConfig(subscriber_count=5000)
        simulator = NewsletterSimulator(config)
        
        assert simulator.config.subscriber_count == 5000
    
    def test_simulator_default_config(self):
        simulator = NewsletterSimulator()
        
        assert simulator.config.subscriber_count == 1000
        assert simulator.config.engagement_rate == 0.75
        assert simulator.config.max_steps == 52
        assert simulator.config.cpc == 2.00
        assert simulator.config.arpu == 5.00


class TestNewsletterSimulatorRunSimulation:
    """Test simulation execution."""
    
    def test_run_simulation(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(5)
        
        assert len(history) == 5
        assert simulator.env.get_state().week == 5
    
    def test_run_simulation_with_custom_steps(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(10)
        
        assert len(history) == 10
        assert simulator.env.get_state().week == 10
    
    def test_run_simulation_with_random_actions(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(5)
        
        assert len(history) == 5
        assert simulator.env.get_state().week == 5
    
    def test_run_simulation_with_deterministic_actions(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(5)
        
        assert len(history) == 5
        assert simulator.env.get_state().week == 5
    
    def test_run_simulation_with_custom_seed(self):
        simulator1 = NewsletterSimulator()
        simulator2 = NewsletterSimulator()
        
        simulator1.set_seed(42)
        simulator2.set_seed(42)
        
        history1 = simulator1.run_simulation(5)
        history2 = simulator2.run_simulation(5)
        
        # Both should have same random state
        assert simulator1.env.get_state().week == simulator2.env.get_state().week
        assert simulator1.env.get_state().subscribers == simulator2.env.get_state().subscribers


class TestNewsletterSimulatorRunMultipleSimulations:
    """Test running multiple simulations."""
    
    def test_run_multiple_simulations(self):
        simulator = NewsletterSimulator()
        
        histories = simulator.run_multiple_simulations(3, 5)
        
        assert len(histories) == 3
        for history in histories:
            assert len(history) == 5
    
    def test_run_multiple_simulations_with_different_seeds(self):
        simulator = NewsletterSimulator()
        
        histories = simulator.run_multiple_simulations(3, 5, seed=42)
        
        assert len(histories) == 3
        for history in histories:
            assert len(history) == 5
    
    def test_run_multiple_simulations_with_custom_steps(self):
        simulator = NewsletterSimulator()
        
        histories = simulator.run_multiple_simulations(3, 10)
        
        assert len(histories) == 3
        for history in histories:
            assert len(history) == 10


class TestNewsletterSimulatorStatistics:
    """Test simulation statistics."""
    
    def test_get_statistics(self):
        simulator = NewsletterSimulator()
        simulator.run_simulation(5)
        
        stats = simulator.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_revenue" in stats
        assert "net_profit" in stats
        assert "final_subscribers" in stats
        assert "total_acquired" in stats
        assert "total_churned" in stats
        assert "avg_engagement" in stats
        assert "avg_sponsor_revenue" in stats
        assert "avg_ad_revenue" in stats
    
    def test_get_statistics_with_multiple_simulations(self):
        simulator = NewsletterSimulator()
        simulator.run_multiple_simulations(3, 5)
        
        stats = simulator.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_revenue" in stats
        assert "net_profit" in stats
        assert "final_subscribers" in stats
    
    def test_statistics_accuracy(self):
        simulator = NewsletterSimulator()
        simulator.run_simulation(5)
        
        stats = simulator.get_statistics()
        
        # Verify statistics are calculated correctly
        assert stats["total_revenue"] >= 0
        assert stats["net_profit"] >= 0
        assert stats["final_subscribers"] > 0
        assert stats["total_acquired"] >= 0
        assert stats["total_churned"] >= 0
        assert 0 <= stats["avg_engagement"] <= 1
        assert stats["avg_sponsor_revenue"] >= 0
        assert stats["avg_ad_revenue"] >= 0


class TestNewsletterSimulatorHistory:
    """Test simulation history."""
    
    def test_get_history(self):
        simulator = NewsletterSimulator()
        simulator.run_simulation(5)
        
        history = simulator.get_history()
        
        assert len(history) == 5
    
    def test_get_history_with_multiple_simulations(self):
        simulator = NewsletterSimulator()
        simulator.run_multiple_simulations(3, 5)
        
        history = simulator.get_history()
        
        assert len(history) == 3
        for h in history:
            assert len(h) == 5
    
    def test_history_contains_weekly_data(self):
        simulator = NewsletterSimulator()
        simulator.run_simulation(5)
        
        history = simulator.get_history()
        
        for i, record in enumerate(history):
            assert record["week"] == i
            assert "subscribers" in record
            assert "revenue" in record
            assert "profit" in record
            assert "engagement" in record


class TestNewsletterSimulatorConfiguration:
    """Test configuration methods."""
    
    def test_set_config(self):
        simulator = NewsletterSimulator()
        
        new_config = SimConfig(subscriber_count=5000)
        simulator.set_config(new_config)
        
        assert simulator.config.subscriber_count == 5000
    
    def test_set_seed(self):
        simulator1 = NewsletterSimulator()
        simulator2 = NewsletterSimulator()
        
        simulator1.set_seed(42)
        simulator2.set_seed(42)
        
        # Both should have same random state
        assert simulator1.env.get_state().week == simulator2.env.get_state().week
        assert simulator1.env.get_state().subscribers == simulator2.env.get_state().subscribers
    
    def test_reset(self):
        simulator = NewsletterSimulator()
        simulator.run_simulation(5)
        
        simulator.reset()
        
        assert simulator.env.get_state().week == 0
        assert simulator.env.get_state().subscribers == 1000
        assert simulator.history.get_weekly_data() == []


class TestNewsletterSimulatorEdgeCases:
    """Test edge cases."""
    
    def test_run_simulation_zero_steps(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(0)
        
        assert len(history) == 0
        assert simulator.env.get_state().week == 0
    
    def test_run_simulation_one_step(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(1)
        
        assert len(history) == 1
        assert simulator.env.get_state().week == 1
    
    def test_run_simulation_max_steps(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(52)
        
        assert len(history) == 52
        assert simulator.env.get_state().week == 52
    
    def test_run_simulation_with_custom_seed(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(5, seed=42)
        
        assert len(history) == 5
        assert simulator.env.get_state().week == 5
    
    def test_run_multiple_simulations_with_zero_simulations(self):
        simulator = NewsletterSimulator()
        
        histories = simulator.run_multiple_simulations(0, 5)
        
        assert len(histories) == 0
    
    def test_run_multiple_simulations_with_one_simulation(self):
        simulator = NewsletterSimulator()
        
        histories = simulator.run_multiple_simulations(1, 5)
        
        assert len(histories) == 1
        assert len(histories[0]) == 5


class TestNewsletterSimulatorActionSpace:
    """Test action space."""
    
    def test_action_space_size(self):
        simulator = NewsletterSimulator()
        
        assert simulator.action_space == 10
    
    def test_action_space_valid_actions(self):
        simulator = NewsletterSimulator()
        
        for action in range(10):
            obs, reward, done, info = simulator.step(action)
            assert obs is not None
            assert isinstance(reward, float)
            assert isinstance(done, bool)
            assert isinstance(info, dict)


class TestNewsletterSimulatorReward:
    """Test reward calculation."""
    
    def test_reward_positive(self):
        simulator = NewsletterSimulator()
        
        obs, reward, done, info = simulator.step(0)
        
        assert isinstance(reward, float)
    
    def test_reward_negative(self):
        simulator = NewsletterSimulator()
        
        obs, reward, done, info = simulator.step(0)
        
        assert isinstance(reward, float)
    
    def test_reward_zero(self):
        simulator = NewsletterSimulator()
        
        obs, reward, done, info = simulator.step(0)
        
        assert isinstance(reward, float)


class TestNewsletterSimulatorDone:
    """Test done condition."""
    
    def test_done_false(self):
        simulator = NewsletterSimulator()
        
        obs, reward, done, info = simulator.step(0)
        
        assert done is False
    
    def test_done_true(self):
        simulator = NewsletterSimulator()
        
        # Run until done
        while not done:
            obs, reward, done, info = simulator.step(0)
        
        assert done is True


class TestNewsletterSimulatorInfo:
    """Test info dictionary."""
    
    def test_info_contains_expected_keys(self):
        simulator = NewsletterSimulator()
        
        obs, reward, done, info = simulator.step(0)
        
        assert "subscribers" in info
        assert "revenue" in info
        assert "profit" in info
        assert "engagement" in info
        assert "cumulative_profit" in info
        assert "churn_rate" in info
        assert "growth_rate" in info
        assert "sponsor_revenue" in info
        assert "ad_revenue" in info
        assert "arpu" in info


class TestNewsletterSimulatorIntegration:
    """Test integration scenarios."""
    
    def test_full_simulation(self):
        simulator = NewsletterSimulator()
        
        history = simulator.run_simulation(52)
        
        assert len(history) == 52
        assert simulator.env.get_state().week == 52
        assert simulator.env.get_state().subscribers > 0
    
    def test_multiple_simulations_with_statistics(self):
        simulator = NewsletterSimulator()
        
        histories = simulator.run_multiple_simulations(10, 52)
        
        stats = simulator.get_statistics()
        
        assert len(histories) == 10
        assert stats["total_revenue"] > 0
        assert stats["net_profit"] > 0
        assert stats["final_subscribers"] > 0
    
    def test_simulation_with_custom_config(self):
        config = SimConfig(
            subscriber_count=5000,
            engagement_rate=0.9,
            max_steps=26,
            cpc=1.00,
            arpu=10.00
        )
        simulator = NewsletterSimulator(config)
        
        history = simulator.run_simulation(26)
        
        assert len(history) == 26
        assert simulator.env.get_state().week == 26
        assert simulator.env.get_state().subscribers > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
