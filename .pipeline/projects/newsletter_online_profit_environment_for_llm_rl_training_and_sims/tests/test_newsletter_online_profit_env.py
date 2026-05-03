"""Tests for the Newsletter Online Profit Environment."""

import pytest
import numpy as np
from profit_env.config import SimConfig
from profit_env.state import NewsletterState, SimulationRecord, SimulationHistory
from profit_env.simulator import NewsletterSimulator
from profit_env.env import NewsletterOnlineProfitEnv


class TestNewsletterState:
    """Tests for NewsletterState class."""
    
    def test_initialization(self):
        """Test state initialization with default values."""
        state = NewsletterState()
        assert state.week == 0
        assert state.subscribers == 1000
        assert state.revenue == 0.0
        assert state.costs == 0.0
        assert state.cumulative_profit == 0.0
        assert state.churned == 0
        assert state.acquired == 0
        assert state.engagement_score == 0.75
        assert state.sponsor_revenue == 0.0
        assert state.ad_revenue == 0.0
        assert state.churn_rate == 0.05
        assert state.growth_rate == 0.1
        assert state.arpu == 5.00
    
    def test_initialization_with_values(self):
        """Test state initialization with custom values."""
        state = NewsletterState(
            week=10,
            subscribers=5000,
            revenue=10000.0,
            costs=5000.0,
            engagement_score=0.9
        )
        assert state.week == 10
        assert state.subscribers == 5000
        assert state.revenue == 10000.0
        assert state.costs == 5000.0
        assert state.engagement_score == 0.9
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = NewsletterState(week=5, subscribers=2000)
        state_dict = state.to_dict()
        
        assert state_dict["week"] == 5
        assert state_dict["subscribers"] == 2000
        assert "cumulative_profit" in state_dict
        assert "engagement_score" in state_dict
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        state_dict = {
            "week": 10,
            "subscribers": 3000,
            "revenue": 15000.0,
            "costs": 7500.0,
            "cumulative_profit": 7500.0,
            "churned": 100,
            "acquired": 200,
            "engagement_score": 0.85,
            "sponsor_revenue": 5000.0,
            "ad_revenue": 3000.0,
            "churn_rate": 0.04,
            "growth_rate": 0.12,
            "arpu": 6.00
        }
        
        state = NewsletterState.from_dict(state_dict)
        assert state.week == 10
        assert state.subscribers == 3000
        assert state.revenue == 15000.0
        assert state.costs == 7500.0
        assert state.cumulative_profit == 7500.0
        assert state.churned == 100
        assert state.acquired == 200
        assert state.engagement_score == 0.85
        assert state.sponsor_revenue == 5000.0
        assert state.ad_revenue == 3000.0
        assert state.churn_rate == 0.04
        assert state.growth_rate == 0.12
        assert state.arpu == 6.00
    
    def test_to_json(self):
        """Test JSON serialization."""
        state = NewsletterState(week=5, subscribers=2000)
        json_str = state.to_json()
        
        assert isinstance(json_str, str)
        assert "week" in json_str
        assert "2000" in json_str
    
    def test_from_json(self):
        """Test JSON deserialization."""
        state = NewsletterState(week=5, subscribers=2000)
        json_str = state.to_json()
        
        restored_state = NewsletterState.from_json(json_str)
        assert restored_state.week == state.week
        assert restored_state.subscribers == state.subscribers
    
    def test_validation_week_negative(self):
        """Test validation rejects negative week."""
        with pytest.raises(ValueError):
            NewsletterState(week=-1)
    
    def test_validation_subscribers_negative(self):
        """Test validation rejects negative subscribers."""
        with pytest.raises(ValueError):
            NewsletterState(subscribers=-100)
    
    def test_validation_engagement_invalid(self):
        """Test validation rejects invalid engagement score."""
        with pytest.raises(ValueError):
            NewsletterState(engagement_score=1.5)
        with pytest.raises(ValueError):
            NewsletterState(engagement_score=-0.1)


class TestSimulationRecord:
    """Tests for SimulationRecord class."""
    
    def test_initialization(self):
        """Test record initialization."""
        record = SimulationRecord(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            profit=2000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        assert record.week == 1
        assert record.subscribers == 1000
        assert record.revenue == 5000.0
        assert record.costs == 3000.0
        assert record.profit == 2000.0
        assert record.cumulative_profit == 2000.0
        assert record.churned == 50
        assert record.acquired == 100
        assert record.engagement == 0.8
        assert record.sponsor_revenue == 1000.0
        assert record.ad_revenue == 500.0
        assert record.churn_rate == 0.05
        assert record.growth_rate == 0.1
        assert record.arpu == 5.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        record = SimulationRecord(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            profit=2000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        record_dict = record.to_dict()
        assert record_dict["week"] == 1
        assert record_dict["subscribers"] == 1000
        assert record_dict["revenue"] == 5000.0
        assert record_dict["costs"] == 3000.0
        assert record_dict["profit"] == 2000.0
        assert record_dict["cumulative_profit"] == 2000.0
        assert record_dict["churned"] == 50
        assert record_dict["acquired"] == 100
        assert record_dict["engagement"] == 0.8
        assert record_dict["sponsor_revenue"] == 1000.0
        assert record_dict["ad_revenue"] == 500.0
        assert record_dict["churn_rate"] == 0.05
        assert record_dict["growth_rate"] == 0.1
        assert record_dict["arpu"] == 5.0
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        record_dict = {
            "week": 5,
            "subscribers": 2000,
            "revenue": 10000.0,
            "costs": 5000.0,
            "profit": 5000.0,
            "cumulative_profit": 25000.0,
            "churned": 100,
            "acquired": 200,
            "engagement": 0.85,
            "sponsor_revenue": 3000.0,
            "ad_revenue": 1500.0,
            "churn_rate": 0.04,
            "growth_rate": 0.12,
            "arpu": 6.0
        }
        
        record = SimulationRecord.from_dict(record_dict)
        assert record.week == 5
        assert record.subscribers == 2000
        assert record.revenue == 10000.0
        assert record.costs == 5000.0
        assert record.profit == 5000.0
        assert record.cumulative_profit == 25000.0
        assert record.churned == 100
        assert record.acquired == 200
        assert record.engagement == 0.85
        assert record.sponsor_revenue == 3000.0
        assert record.ad_revenue == 1500.0
        assert record.churn_rate == 0.04
        assert record.growth_rate == 0.12
        assert record.arpu == 6.0
    
    def test_to_json(self):
        """Test JSON serialization."""
        record = SimulationRecord(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            profit=2000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        json_str = record.to_json()
        assert isinstance(json_str, str)
        assert "week" in json_str
        assert "1000" in json_str
    
    def test_from_json(self):
        """Test JSON deserialization."""
        record = SimulationRecord(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            profit=2000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        json_str = record.to_json()
        restored_record = SimulationRecord.from_json(json_str)
        
        assert restored_record.week == record.week
        assert restored_record.subscribers == record.subscribers
        assert restored_record.profit == record.profit


class TestSimulationHistory:
    """Tests for SimulationHistory class."""
    
    def test_initialization(self):
        """Test history initialization."""
        history = SimulationHistory()
        assert len(history.records) == 0
    
    def test_add_record(self):
        """Test adding records."""
        history = SimulationHistory()
        
        record1 = SimulationRecord(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            profit=2000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        history.add_record(record1)
        assert len(history.records) == 1
        assert history.records[0].week == 1
    
    def test_add_weekly_data(self):
        """Test adding weekly data from state."""
        history = SimulationHistory()
        
        state = NewsletterState(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement_score=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        history.add_weekly_data(state)
        assert len(history.records) == 1
        assert history.records[0].week == 1
        assert history.records[0].subscribers == 1000
    
    def test_get_weekly_data(self):
        """Test getting weekly data."""
        history = SimulationHistory()
        
        record1 = SimulationRecord(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            profit=2000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        record2 = SimulationRecord(
            week=2,
            subscribers=1100,
            revenue=5500.0,
            costs=3200.0,
            profit=2300.0,
            cumulative_profit=4300.0,
            churned=55,
            acquired=110,
            engagement=0.85,
            sponsor_revenue=1100.0,
            ad_revenue=550.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        history.add_record(record1)
        history.add_record(record2)
        
        weekly_data = history.get_weekly_data()
        assert len(weekly_data) == 2
        assert weekly_data[0]["week"] == 1
        assert weekly_data[1]["week"] == 2
    
    def test_get_statistics(self):
        """Test getting statistics."""
        history = SimulationHistory()
        
        record1 = SimulationRecord(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            profit=2000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        record2 = SimulationRecord(
            week=2,
            subscribers=1100,
            revenue=5500.0,
            costs=3200.0,
            profit=2300.0,
            cumulative_profit=4300.0,
            churned=55,
            acquired=110,
            engagement=0.85,
            sponsor_revenue=1100.0,
            ad_revenue=550.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        history.add_record(record1)
        history.add_record(record2)
        
        stats = history.get_statistics()
        
        assert "total_weeks" in stats
        assert "avg_revenue" in stats
        assert "avg_profit" in stats
        assert "total_profit" in stats
        assert "final_subscribers" in stats
        assert "avg_engagement" in stats
        assert "avg_sponsor_revenue" in stats
        assert "avg_ad_revenue" in stats
        assert "churn_rate" in stats
        assert "growth_rate" in stats
        assert "arpu" in stats
        
        assert stats["total_weeks"] == 2
        assert stats["avg_revenue"] == 5250.0
        assert stats["avg_profit"] == 2150.0
        assert stats["total_profit"] == 4300.0
        assert stats["final_subscribers"] == 1100
    
    def test_clear(self):
        """Test clearing history."""
        history = SimulationHistory()
        
        record = SimulationRecord(
            week=1,
            subscribers=1000,
            revenue=5000.0,
            costs=3000.0,
            profit=2000.0,
            cumulative_profit=2000.0,
            churned=50,
            acquired=100,
            engagement=0.8,
            sponsor_revenue=1000.0,
            ad_revenue=500.0,
            churn_rate=0.05,
            growth_rate=0.1,
            arpu=5.0
        )
        
        history.add_record(record)
        assert len(history.records) == 1
        
        history.clear()
        assert len(history.records) == 0


class TestSimConfig:
    """Tests for SimConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SimConfig()
        
        assert config.subscriber_count == 1000
        assert config.engagement_rate == 0.75
        assert config.max_steps == 52
        assert config.sponsor_rate == 0.50
        assert config.sponsorship_fill_rate == 0.8
        assert config.ad_rate == 0.25
        assert config.arpu == 5.00
        assert config.content_cost == 1000.0
        assert config.operational_cost == 500.0
        assert config.cpc == 1.0
        assert config.growth_rate == 0.1
        assert config.churn_rate == 0.05
        assert config.seasonal == 1.0
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = SimConfig(
            subscriber_count=5000,
            engagement_rate=0.9,
            max_steps=104,
            sponsor_rate=1.0,
            ad_rate=0.5,
            arpu=10.0,
            content_cost=2000.0,
            operational_cost=1000.0,
            cpc=2.0,
            growth_rate=0.15,
            churn_rate=0.03,
            seasonal=1.2
        )
        
        assert config.subscriber_count == 5000
        assert config.engagement_rate == 0.9
        assert config.max_steps == 104
        assert config.sponsor_rate == 1.0
        assert config.sponsorship_fill_rate == 0.8
        assert config.ad_rate == 0.5
        assert config.arpu == 10.0
        assert config.content_cost == 2000.0
        assert config.operational_cost == 1000.0
        assert config.cpc == 2.0
        assert config.growth_rate == 0.15
        assert config.churn_rate == 0.03
        assert config.seasonal == 1.2
    
    def test_get_effective_churn_rate(self):
        """Test effective churn rate calculation."""
        config = SimConfig()
        
        # Higher engagement should reduce churn
        assert config.get_effective_churn_rate(0.9) < config.get_effective_churn_rate(0.5)
        assert config.get_effective_churn_rate(0.9) < config.churn_rate
        assert config.get_effective_churn_rate(0.5) > config.churn_rate
        
        # Test with seasonal factor
        config.seasonal = 1.2
        assert config.get_effective_churn_rate(0.75) == config.churn_rate * 1.2
    
    def test_get_effective_growth_rate(self):
        """Test effective growth rate calculation."""
        config = SimConfig()
        
        # Higher engagement should increase growth
        assert config.get_effective_growth_rate(0.9) > config.get_effective_growth_rate(0.5)
        assert config.get_effective_growth_rate(0.9) > config.growth_rate
        assert config.get_effective_growth_rate(0.5) < config.growth_rate
        
        # Test with seasonal factor
        config.seasonal = 1.2
        assert config.get_effective_growth_rate(0.75) == config.growth_rate * 1.2


class TestNewsletterSimulator:
    """Tests for NewsletterSimulator class."""
    
    def test_initialization(self):
        """Test simulator initialization."""
        simulator = NewsletterSimulator()
        
        assert simulator.action_space == 10
        assert simulator.config is not None
        assert simulator.history is not None
    
    def test_run_week(self):
        """Test running a single week."""
        config = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        simulator = NewsletterSimulator(config=config)
        result = simulator.run_week()
        
        assert "week" in result
        assert "subscribers" in result
        assert "revenue" in result
        assert "costs" in result
        assert "profit" in result
        assert "cumulative_profit" in result
        assert "churned" in result
        assert "acquired" in result
        assert "engagement" in result
        assert "sponsor_revenue" in result
        assert "ad_revenue" in result
        assert "churn_rate" in result
        assert "growth_rate" in result
        assert "arpu" in result
        
        assert result["week"] == 1
        assert result["subscribers"] > 0
        assert result["cumulative_profit"] == result["profit"]
    
    def test_run_simulation(self):
        """Test running multiple weeks."""
        config = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        simulator = NewsletterSimulator(config=config)
        results = simulator.run_simulation(5)
        
        assert len(results) == 5
        assert results[0]["week"] == 1
        assert results[4]["week"] == 5
    
    def test_run_simulation_with_seed(self):
        """Test reproducibility with seed."""
        config = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        simulator1 = NewsletterSimulator(config=config)
        results1 = simulator1.run_simulation(5, seed=42)
        
        simulator2 = NewsletterSimulator(config=config)
        results2 = simulator2.run_simulation(5, seed=42)
        
        assert results1 == results2
    
    def test_run_multiple_simulations(self):
        """Test running multiple simulations."""
        config = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        simulator = NewsletterSimulator(config=config)
        results = simulator.run_multiple_simulations(3, 5, seed=42)
        
        assert len(results) == 3
        assert all(len(sim) == 5 for sim in results)
    
    def test_get_statistics(self):
        """Test getting statistics."""
        config = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        simulator = NewsletterSimulator(config=config)
        simulator.run_simulation(5)
        
        stats = simulator.get_statistics()
        
        assert "total_weeks" in stats
        assert "avg_revenue" in stats
        assert "avg_profit" in stats
        assert "total_profit" in stats
        assert "final_subscribers" in stats
        assert "avg_engagement" in stats
        assert "avg_sponsor_revenue" in stats
        assert "avg_ad_revenue" in stats
        assert "churn_rate" in stats
        assert "growth_rate" in stats
        assert "arpu" in stats
    
    def test_reset(self):
        """Test resetting simulator."""
        config = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        simulator = NewsletterSimulator(config=config)
        simulator.run_simulation(5)
        
        assert len(simulator.history.records) == 5
        
        simulator.reset()
        
        assert len(simulator.history.records) == 0
    
    def test_set_seed(self):
        """Test setting seed."""
        config = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        simulator = NewsletterSimulator(config=config)
        simulator.set_seed(42)
        
        results1 = simulator.run_simulation(5)
        
        simulator.set_seed(42)
        results2 = simulator.run_simulation(5)
        
        assert results1 == results2
    
    def test_set_config(self):
        """Test setting new configuration."""
        config1 = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        config2 = SimConfig(
            subscriber_count=5000,
            engagement_rate=0.9,
            max_steps=10,
            sponsor_rate=1.0,
            sponsorship_fill_rate=0.8,
            ad_rate=0.5,
            arpu=10.0,
            content_cost=2000.0,
            operational_cost=1000.0,
            cpc=2.0,
            growth_rate=0.15,
            churn_rate=0.03,
            seasonal=1.2
        )
        
        simulator = NewsletterSimulator(config=config1)
        simulator.set_config(config2)
        
        assert simulator.config.subscriber_count == 5000
        assert simulator.config.engagement_rate == 0.9
        assert simulator.config.sponsor_rate == 1.0
    
    def test_get_history(self):
        """Test getting history."""
        config = SimConfig(
            subscriber_count=1000,
            engagement_rate=0.75,
            max_steps=10,
            sponsor_rate=0.50,
            sponsorship_fill_rate=0.8,
            ad_rate=0.25,
            arpu=5.00,
            content_cost=1000.0,
            operational_cost=500.0,
            cpc=1.0,
            growth_rate=0.1,
            churn_rate=0.05,
            seasonal=1.0
        )
        
        simulator = NewsletterSimulator(config=config)
        simulator.run_simulation(5)
        
        history = simulator.get_history()
        
        assert len(history) == 5
        assert history[0]["week"] == 1
        assert history[4]["week"] == 5


class TestNewsletterOnlineProfitEnv:
    """Tests for NewsletterOnlineProfitEnv class."""
    
    def test_initialization(self):
        """Test environment initialization."""
        env = NewsletterOnlineProfitEnv()
        
        assert env.observation_space.shape == (10,)
        assert env.action_space == 10
        assert env.config is not None
        assert env.simulator is not None
    
    def test_reset(self):
        """Test environment reset."""
        env = NewsletterOnlineProfitEnv()
        obs = env.reset()
        
        assert len(obs) == 10
        assert obs[0] == 1000  # subscribers
        assert obs[1] == 0.0  # revenue
        assert obs[2] == 0.0  # profit
        assert obs[3] == 0.75  # engagement
        assert obs[4] == 0.0  # cumulative_profit
        assert obs[5] == 0.05  # churn_rate
        assert obs[6] == 0.1  # growth_rate
        assert obs[7] == 0.0  # sponsor_revenue
        assert obs[8] == 0.0  # ad_revenue
        assert obs[9] == 5.0  # arpu
    
    def test_step(self):
        """Test environment step."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        obs, reward, done, info = env.step(action)
        
        assert len(obs) == 10
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)
        
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
    
    def test_step_invalid_action(self):
        """Test step with invalid action."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        # Invalid action - wrong shape
        with pytest.raises(ValueError):
            env.step(np.array([0.5, 0.5]))
        
        # Invalid action - wrong shape
        with pytest.raises(ValueError):
            env.step(np.array([0.5, 0.5, 0.5, 0.5, 0.5]))
    
    def test_step_reproducibility(self):
        """Test step reproducibility with seed."""
        env1 = NewsletterOnlineProfitEnv()
        env1.reset(seed=42)
        
        env2 = NewsletterOnlineProfitEnv()
        env2.reset(seed=42)
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        obs1, reward1, done1, info1 = env1.step(action)
        obs2, reward2, done2, info2 = env2.step(action)
        
        assert obs1 == obs2
        assert reward1 == reward2
        assert done1 == done2
        assert info1 == info2
    
    def test_max_steps(self):
        """Test that environment terminates at max steps."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        for _ in range(52):
            action = np.array([0.5, 0.5, 0.5, 0.5])
            obs, reward, done, info = env.step(action)
        
        assert done is True
    
    def test_observation_space(self):
        """Test observation space."""
        env = NewsletterOnlineProfitEnv()
        
        assert env.observation_space.shape == (10,)
        assert env.observation_space.dtype == np.float32
    
    def test_action_space(self):
        """Test action space."""
        env = NewsletterOnlineProfitEnv()
        
        assert env.action_space == 10
    
    def test_reward_is_profit(self):
        """Test that reward equals profit."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        obs, reward, done, info = env.step(action)
        
        assert reward == info["profit"]
    
    def test_cumulative_profit_tracking(self):
        """Test cumulative profit tracking."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        initial_cumulative = env.simulator.get_state().cumulative_profit
        
        action = np.array([0.5, 0.5, 0.5, 0.5])
        env.step(action)
        
        new_cumulative = env.simulator.get_state().cumulative_profit
        
        assert new_cumulative >= initial_cumulative


class TestIntegration:
    """Integration tests for the complete environment."""
    
    def test_full_simulation(self):
        """Test a full simulation with the environment."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        total_reward = 0.0
        done = False
        
        while not done:
            action = np.array([0.5, 0.5, 0.5, 0.5])
            obs, reward, done, info = env.step(action)
            total_reward += reward
        
        assert done is True
        assert total_reward == env.simulator.get_state().cumulative_profit
    
    def test_action_impact(self):
        """Test that actions have expected impact."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        # High marketing action
        high_marketing = np.array([1.0, 0.0, 0.0, 0.0])
        obs1, _, _, info1 = env.step(high_marketing)
        
        # Low marketing action
        low_marketing = np.array([0.0, 0.0, 0.0, 0.0])
        obs2, _, _, info2 = env.step(low_marketing)
        
        # High marketing should lead to higher growth
        assert info1["growth_rate"] >= info2["growth_rate"]
    
    def test_engagement_impact(self):
        """Test that engagement affects churn and growth."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        # High engagement actions
        high_engagement = np.array([0.5, 1.0, 0.0, 1.0])
        obs1, _, _, info1 = env.step(high_engagement)
        
        # Low engagement actions
        low_engagement = np.array([0.5, 0.0, 0.0, 0.0])
        obs2, _, _, info2 = env.step(low_engagement)
        
        # High engagement should lead to lower churn
        assert info1["churn_rate"] <= info2["churn_rate"]
    
    def test_pricing_impact(self):
        """Test that pricing affects ARPU."""
        env = NewsletterOnlineProfitEnv()
        env.reset()
        
        # High pricing action
        high_pricing = np.array([0.0, 0.0, 1.0, 0.0])
        obs1, _, _, info1 = env.step(high_pricing)
        
        # Low pricing action
        low_pricing = np.array([0.0, 0.0, 0.0, 0.0])
        obs2, _, _, info2 = env.step(low_pricing)
        
        # High pricing should lead to higher ARPU
        assert info1["arpu"] >= info2["arpu"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
