"""Comprehensive tests for the Newsletter Online Profit Environment."""

import numpy as np
import pytest
from profit_env import (
    NewsletterEnv,
    NewsletterSimulator,
    SimConfig,
    NewsletterState,
    SimulationHistory,
    Observation,
)


class TestSimConfig:
    """Tests for SimConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SimConfig()
        assert config.subscriber_count == 1000
        assert config.retention_rate == 0.95
        assert config.growth_rate == 0.1
        assert config.churn_rate == 0.05
        assert config.arpu == 5.00
        assert config.ad_rate == 0.50
        assert config.sponsor_rate == 100.00
        assert config.content_cost == 500.00
        assert config.operational_cost == 300.00
        assert config.cpc == 2.50
        assert config.seasonal_factor == 1.0
        assert config.competitor_count == 5
        assert config.market_saturation == 0.3
        assert config.conversion_rate == 0.02
        assert config.engagement_rate == 0.75
        assert config.sponsorship_fill_rate == 0.8
        assert config.refund_rate == 0.01
        assert config.tax_rate == 0.25
        assert config.discount_rate == 0.1
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SimConfig(
            subscriber_count=5000,
            retention_rate=0.90,
            growth_rate=0.15,
            churn_rate=0.08,
            arpu=10.00,
            ad_rate=1.00,
            sponsor_rate=200.00,
            content_cost=1000.00,
            operational_cost=500.00,
            cpc=5.00,
            seasonal_factor=1.2,
            competitor_count=10,
            market_saturation=0.5,
            conversion_rate=0.03,
            engagement_rate=0.85,
            sponsorship_fill_rate=0.9,
            refund_rate=0.02,
            tax_rate=0.30,
            discount_rate=0.15
        )
        assert config.subscriber_count == 5000
        assert config.retention_rate == 0.90
        assert config.growth_rate == 0.15


class TestNewsletterState:
    """Tests for NewsletterState class."""
    
    def test_initial_state(self):
        """Test initial state creation."""
        state = NewsletterState()
        assert state.subscribers == 1000
        assert state.cumulative_profit == 0.0
        assert state.week == 0
        assert state.acquired == 0
        assert state.churned == 0
        assert state.engagement_score == 0.75
        assert state.sponsor_revenue == 0.0
        assert state.ad_revenue == 0.0
        assert state.costs == 0.0  # Fixed: use 'costs' not 'total_costs'
    
    def test_state_update(self):
        """Test state update with new values."""
        state = NewsletterState()
        state.subscribers = 1500
        state.cumulative_profit = 5000.0
        state.week = 10
        state.acquired = 200
        state.churned = 50
        
        assert state.subscribers == 1500
        assert state.cumulative_profit == 5000.0
        assert state.week == 10
        assert state.acquired == 200
        assert state.churned == 50


class TestSimulationHistory:
    """Tests for SimulationHistory class."""
    
    def test_empty_history(self):
        """Test empty history statistics."""
        history = SimulationHistory()
        stats = history.get_statistics()
        assert stats['total_revenue'] == 0.0
        assert stats['total_costs'] == 0.0
        assert stats['net_profit'] == 0.0
        assert stats['avg_subscribers'] == 0.0
        assert stats['final_subscribers'] == 0
        assert stats['final_cumulative_profit'] == 0.0
        assert stats['avg_churn_rate'] == 0.0
        assert stats['total_acquired'] == 0
    
    def test_add_records(self):
        """Test adding records to history."""
        history = SimulationHistory()
        history.add_record({'week': 1, 'subscribers': 1000, 'profit': 1000.0})
        history.add_record({'week': 2, 'subscribers': 1100, 'profit': 1200.0})
        
        assert len(history) == 2
        assert history[0]['week'] == 1
        assert history[1]['week'] == 2
    
    def test_get_week(self):
        """Test getting specific week data."""
        history = SimulationHistory()
        history.add_record({'week': 1, 'subscribers': 1000, 'profit': 1000.0})
        history.add_record({'week': 2, 'subscribers': 1100, 'profit': 1200.0})
        
        week1 = history.get_week(0)  # 0-indexed
        assert week1 is not None
        assert week1['week'] == 1
        
        week5 = history.get_week(5)
        assert week5 is None
    
    def test_get_weeks(self):
        """Test getting range of weeks."""
        history = SimulationHistory()
        history.add_record({'week': 1, 'subscribers': 1000, 'profit': 1000.0})
        history.add_record({'week': 2, 'subscribers': 1100, 'profit': 1200.0})
        history.add_record({'week': 3, 'subscribers': 1200, 'profit': 1400.0})
        
        weeks = history.get_weeks(0, 1)  # 0-indexed
        assert len(weeks) == 2
        assert weeks[0]['week'] == 1
        assert weeks[1]['week'] == 2
    
    def test_statistics_calculation(self):
        """Test statistics calculation from history."""
        history = SimulationHistory()
        history.add_record({
            'week': 1,
            'subscribers': 1000,
            'revenue': 10000.0,
            'costs': 5000.0,
            'profit': 5000.0,
            'cumulative_profit': 5000.0,
            'churned': 50,
            'acquired': 100,
            'engagement_score': 0.75,
            'sponsor_revenue': 8000.0,
            'ad_revenue': 2000.0
        })
        history.add_record({
            'week': 2,
            'subscribers': 1050,
            'revenue': 11000.0,
            'costs': 5200.0,
            'profit': 5800.0,
            'cumulative_profit': 10800.0,
            'churned': 52,
            'acquired': 103,
            'engagement_score': 0.76,
            'sponsor_revenue': 8800.0,
            'ad_revenue': 2200.0
        })
        
        stats = history.get_statistics()
        assert stats['total_revenue'] == 21000.0
        assert stats['total_costs'] == 10200.0
        assert stats['net_profit'] == 10800.0
        assert stats['avg_subscribers'] == 1025.0
        assert stats['final_subscribers'] == 1050
        assert stats['final_cumulative_profit'] == 10800.0
        assert stats['total_acquired'] == 203


class TestObservation:
    """Tests for Observation class."""
    
    def test_default_observation(self):
        """Test default observation values."""
        obs = Observation()
        assert obs.subscribers == 0.0
        assert obs.revenue == 0.0
        assert obs.profit == 0.0
        assert obs.engagement == 0.75
        assert obs.week == 0.0
        assert obs.cumulative_profit == 0.0
        assert obs.churn_rate == 0.05
        assert obs.growth_rate == 0.1
        assert obs.sponsor_revenue == 0.0
        assert obs.ad_revenue == 0.0
    
    def test_observation_to_dict(self):
        """Test conversion to dictionary."""
        obs = Observation(
            subscribers=1000.0,
            revenue=5000.0,
            profit=2000.0,
            engagement=0.85,
            week=10.0,
            cumulative_profit=15000.0,
            churn_rate=0.03,
            growth_rate=0.12,
            sponsor_revenue=4000.0,
            ad_revenue=1000.0
        )
        
        data = obs.to_dict()
        assert data['subscribers'] == 1000.0
        assert data['revenue'] == 5000.0
        assert data['profit'] == 2000.0
        assert data['engagement'] == 0.85
        assert data['week'] == 10.0
        assert data['cumulative_profit'] == 15000.0
        assert data['churn_rate'] == 0.03
        assert data['growth_rate'] == 0.12
        assert data['sponsor_revenue'] == 4000.0
        assert data['ad_revenue'] == 1000.0
    
    def test_observation_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'subscribers': 1000.0,
            'revenue': 5000.0,
            'profit': 2000.0,
            'engagement': 0.85,
            'week': 10.0,
            'cumulative_profit': 15000.0,
            'churn_rate': 0.03,
            'growth_rate': 0.12,
            'sponsor_revenue': 4000.0,
            'ad_revenue': 1000.0
        }
        
        obs = Observation.from_dict(data)
        assert obs.subscribers == 1000.0
        assert obs.revenue == 5000.0
        assert obs.profit == 2000.0
        assert obs.engagement == 0.85
        assert obs.week == 10.0
        assert obs.cumulative_profit == 15000.0
        assert obs.churn_rate == 0.03
        assert obs.growth_rate == 0.12
        assert obs.sponsor_revenue == 4000.0
        assert obs.ad_revenue == 1000.0
    
    def test_observation_length(self):
        """Test observation length."""
        obs = Observation()
        assert len(obs) == 10
    
    def test_observation_iteration(self):
        """Test observation iteration."""
        obs = Observation()
        values = list(obs)
        assert len(values) == 10
    
    def test_observation_getitem(self):
        """Test observation item access."""
        obs = Observation(subscribers=1000.0)
        assert obs['subscribers'] == 1000.0
        assert obs['revenue'] == 0.0


class TestNewsletterEnv:
    """Tests for NewsletterEnv class."""
    
    def test_env_initialization(self):
        """Test environment initialization."""
        env = NewsletterEnv()
        assert env.observation_space is not None
        assert env.action_space is not None
        assert env.config is not None
        assert env.simulator is not None
    
    def test_env_reset(self):
        """Test environment reset."""
        env = NewsletterEnv()
        obs = env.reset()
        
        assert isinstance(obs, Observation)
        # Observation subscribers is normalized (0.0 to 1.0)
        assert 0.0 <= obs.subscribers <= 1.0
        assert obs.week == 0.0
        assert obs.cumulative_profit == 0.0
    
    def test_env_reset_with_config(self):
        """Test environment reset with custom config."""
        config = SimConfig(subscriber_count=5000, max_steps=10)
        env = NewsletterEnv(config=config)
        obs = env.reset()
        
        assert isinstance(obs, Observation)
        # Observation subscribers is normalized (0.0 to 1.0)
        assert 0.0 <= obs.subscribers <= 1.0
        assert obs.week == 0.0
    
    def test_env_step(self):
        """Test environment step."""
        env = NewsletterEnv()
        obs = env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        obs, reward, terminated, info = env.step(action)
        
        assert isinstance(obs, Observation)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(info, dict)
    
    def test_env_step_bounds(self):
        """Test action bounds."""
        env = NewsletterEnv()
        obs = env.reset()
        
        # Test with minimum action
        action_min = np.array([0.0, 0.0, 0.0, 0.0])
        obs, reward, terminated, info = env.step(action_min)
        
        # Test with maximum action
        action_max = np.array([1.0, 1.0, 1.0, 1.0])
        obs, reward, terminated, info = env.step(action_max)
        
        # Test with out-of-bounds action (should be clipped)
        action_out = np.array([2.0, -1.0, 1.5, -0.5])
        obs, reward, terminated, info = env.step(action_out)
    
    def test_env_max_steps(self):
        """Test environment max steps termination."""
        config = SimConfig(max_steps=5)
        env = NewsletterEnv(config=config)
        obs = env.reset()
        
        terminated = False
        for i in range(10):
            action = np.array([0.5, 0.5, 0.5, 0.5])
            obs, reward, terminated, info = env.step(action)
            if terminated:
                assert i == 4  # Should terminate at step 5 (0-indexed)
                break
        
        assert terminated
    
    def test_env_reward_calculation(self):
        """Test reward calculation."""
        env = NewsletterEnv()
        obs = env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        obs, reward, terminated, info = env.step(action)
        
        # Reward should be a reasonable value
        assert isinstance(reward, float)
        assert not np.isnan(reward)
        assert not np.isinf(reward)
    
    def test_env_info_dict(self):
        """Test info dictionary contents."""
        env = NewsletterEnv()
        obs = env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        obs, reward, terminated, info = env.step(action)
        
        assert 'subscribers' in info
        assert 'revenue' in info
        assert 'costs' in info
        assert 'profit' in info
        assert 'acquired' in info
        assert 'churned' in info
        assert 'engagement_score' in info
        assert 'sponsor_revenue' in info
        assert 'ad_revenue' in info


class TestNewsletterSimulator:
    """Tests for NewsletterSimulator class."""
    
    def test_simulator_initialization(self):
        """Test simulator initialization."""
        config = SimConfig(subscriber_count=1000, max_steps=10)
        sim = NewsletterSimulator(config)
        
        assert sim.config is not None
        assert sim.state is not None
        assert sim.history is not None
    
    def test_simulator_run(self):
        """Test simulator run."""
        config = SimConfig(subscriber_count=1000, max_steps=10)
        sim = NewsletterSimulator(config)
        history = sim.run_simulation(10)
        
        assert len(history) == 10
        assert history[0]['week'] == 1
        assert history[9]['week'] == 10
    
    def test_simulator_statistics(self):
        """Test simulator statistics."""
        config = SimConfig(subscriber_count=1000, max_steps=10)
        sim = NewsletterSimulator(config)
        history = sim.run_simulation(10)
        
        stats = history.get_statistics()
        
        assert 'total_revenue' in stats
        assert 'total_costs' in stats
        assert 'net_profit' in stats
        assert 'avg_subscribers' in stats
        assert 'final_subscribers' in stats
        assert 'final_cumulative_profit' in stats
        assert 'avg_churn_rate' in stats
        assert 'total_acquired' in stats
    
    def test_simulator_set_seed(self):
        """Test simulator seed setting for reproducibility."""
        config = SimConfig(subscriber_count=1000, max_steps=5)
        
        sim1 = NewsletterSimulator(config)
        sim1.set_seed(42)
        history1 = sim1.run_simulation(5)
        
        sim2 = NewsletterSimulator(config)
        sim2.set_seed(42)
        history2 = sim2.run_simulation(5)
        
        # Results should be identical with same seed
        for i in range(5):
            assert history1[i]['subscribers'] == history2[i]['subscribers']
            assert history1[i]['profit'] == history2[i]['profit']


class TestIntegration:
    """Integration tests for the complete environment."""
    
    def test_full_simulation_loop(self):
        """Test complete simulation loop."""
        env = NewsletterEnv()
        obs = env.reset()
        
        total_reward = 0.0
        terminated = False
        
        for i in range(20):
            action = np.array([0.5, 0.5, 0.5, 0.5])
            obs, reward, terminated, info = env.step(action)
            total_reward += reward
            
            if terminated:
                break
        
        assert isinstance(total_reward, float)
        assert not np.isnan(total_reward)
    
    def test_env_and_simulator_consistency(self):
        """Test consistency between env and simulator."""
        config = SimConfig(subscriber_count=1000, max_steps=10)
        
        env = NewsletterEnv(config=config)
        env_obs = env.reset()
        
        sim = NewsletterSimulator(config=config)
        sim_history = sim.run_simulation(10)
        
        # Both should start with same subscriber count
        # env_obs.subscribers is normalized (0.0 to 1.0)
        # 1000 subscribers / 10000 max = 0.1 normalized
        assert env_obs.subscribers == 0.1  # Normalized value (1000/10000)
        # sim_history[0] is after first week, so subscribers may have changed
        assert sim_history[0]['subscribers'] > 0  # Should have subscribers
    
    def test_cli_export_functionality(self):
        """Test CLI export functionality."""
        import tempfile
        import os
        from profit_env.cli import main
        import sys
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, 'test.json')
            csv_file = os.path.join(tmpdir, 'test.csv')
            
            # Test JSON export
            sys.argv = ['profit_env', 'sim', 'export', '--weeks', '5', 
                       '--output', json_file, '--format', 'json']
            result = main()
            assert result == 0
            assert os.path.exists(json_file)
            
            # Test CSV export
            sys.argv = ['profit_env', 'sim', 'export', '--weeks', '5',
                       '--output', csv_file, '--format', 'csv']
            result = main()
            assert result == 0
            assert os.path.exists(csv_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
