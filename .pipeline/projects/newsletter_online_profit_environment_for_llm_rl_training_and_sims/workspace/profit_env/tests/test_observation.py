"""Tests for observation module."""

import pytest
from profit_env.observation import Observation


class TestObservationInitialization:
    """Test observation initialization."""
    
    def test_observation_creation(self):
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
    
    def test_observation_with_custom_values(self):
        obs = Observation(
            subscribers=0.5,
            revenue=0.8,
            profit=0.3,
            engagement=0.9,
            week=0.5
        )
        
        assert obs.subscribers == 0.5
        assert obs.revenue == 0.8
        assert obs.profit == 0.3
        assert obs.engagement == 0.9
        assert obs.week == 0.5
    
    def test_observation_default_values(self):
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


class TestObservationValidation:
    """Test observation validation."""
    
    def test_observation_rejects_invalid_subscribers(self):
        with pytest.raises(ValueError):
            Observation(subscribers=-0.1)
        
        with pytest.raises(ValueError):
            Observation(subscribers=1.1)
    
    def test_observation_rejects_invalid_revenue(self):
        with pytest.raises(ValueError):
            Observation(revenue=-0.1)
        
        with pytest.raises(ValueError):
            Observation(revenue=1.1)
    
    def test_observation_rejects_invalid_engagement(self):
        with pytest.raises(ValueError):
            Observation(engagement=1.5)
        
        with pytest.raises(ValueError):
            Observation(engagement=-0.5)
    
    def test_observation_rejects_invalid_week(self):
        with pytest.raises(ValueError):
            Observation(week=-0.1)
        
        with pytest.raises(ValueError):
            Observation(week=1.1)
    
    def test_observation_accepts_valid_values(self):
        obs = Observation(
            subscribers=0.5,
            revenue=0.8,
            profit=0.3,
            engagement=0.9,
            week=0.5
        )
        
        assert obs.subscribers == 0.5
        assert obs.revenue == 0.8
        assert obs.profit == 0.3
        assert obs.engagement == 0.9
        assert obs.week == 0.5
    
    def test_observation_accepts_boundary_values(self):
        obs = Observation(
            subscribers=0.0,
            revenue=0.0,
            profit=0.0,
            engagement=0.0,
            week=0.0
        )
        
        assert obs.subscribers == 0.0
        assert obs.revenue == 0.0
        assert obs.profit == 0.0
        assert obs.engagement == 0.0
        assert obs.week == 0.0
        
        obs2 = Observation(
            subscribers=1.0,
            revenue=1.0,
            profit=1.0,
            engagement=1.0,
            week=1.0
        )
        
        assert obs2.subscribers == 1.0
        assert obs2.revenue == 1.0
        assert obs2.profit == 1.0
        assert obs2.engagement == 1.0
        assert obs2.week == 1.0


class TestObservationToDict:
    """Test observation to dictionary conversion."""
    
    def test_observation_to_dict(self):
        obs = Observation(
            subscribers=0.5,
            revenue=0.8,
            profit=0.3,
            engagement=0.9,
            week=0.5
        )
        
        obs_dict = obs.to_dict()
        
        assert obs_dict["subscribers"] == 0.5
        assert obs_dict["revenue"] == 0.8
        assert obs_dict["profit"] == 0.3
        assert obs_dict["engagement"] == 0.9
        assert obs_dict["week"] == 0.5
        assert "cumulative_profit" in obs_dict
        assert "churn_rate" in obs_dict
        assert "growth_rate" in obs_dict
        assert "sponsor_revenue" in obs_dict
        assert "ad_revenue" in obs_dict
    
    def test_observation_to_dict_all_fields(self):
        obs = Observation()
        
        obs_dict = obs.to_dict()
        
        assert len(obs_dict) == 10
        assert all(key in obs_dict for key in [
            "subscribers", "revenue", "profit", "engagement", "week",
            "cumulative_profit", "churn_rate", "growth_rate",
            "sponsor_revenue", "ad_revenue"
        ])


class TestObservationFromDict:
    """Test observation from dictionary creation."""
    
    def test_observation_from_dict(self):
        obs_dict = {
            "subscribers": 0.5,
            "revenue": 0.8,
            "profit": 0.3,
            "engagement": 0.9,
            "week": 0.5,
            "cumulative_profit": 0.7,
            "churn_rate": 0.03,
            "growth_rate": 0.15,
            "sponsor_revenue": 0.2,
            "ad_revenue": 0.1
        }
        
        obs = Observation.from_dict(obs_dict)
        
        assert obs.subscribers == 0.5
        assert obs.revenue == 0.8
        assert obs.profit == 0.3
        assert obs.engagement == 0.9
        assert obs.week == 0.5
        assert obs.cumulative_profit == 0.7
        assert obs.churn_rate == 0.03
        assert obs.growth_rate == 0.15
        assert obs.sponsor_revenue == 0.2
        assert obs.ad_revenue == 0.1
    
    def test_observation_from_dict_with_defaults(self):
        obs_dict = {
            "subscribers": 0.5,
            "revenue": 0.8
        }
        
        obs = Observation.from_dict(obs_dict)
        
        assert obs.subscribers == 0.5
        assert obs.revenue == 0.8
        assert obs.profit == 0.0
        assert obs.engagement == 0.75
        assert obs.week == 0.0
        assert obs.cumulative_profit == 0.0
        assert obs.churn_rate == 0.05
        assert obs.growth_rate == 0.1
        assert obs.sponsor_revenue == 0.0
        assert obs.ad_revenue == 0.0


class TestObservationNormalization:
    """Test observation normalization."""
    
    def test_observation_values_normalized(self):
        obs = Observation(
            subscribers=0.5,
            revenue=0.8,
            profit=0.3,
            engagement=0.9,
            week=0.5
        )
        
        # All values should be in [0, 1] range
        assert 0 <= obs.subscribers <= 1
        assert 0 <= obs.revenue <= 1
        assert 0 <= obs.profit <= 1
        assert 0 <= obs.engagement <= 1
        assert 0 <= obs.week <= 1
        assert 0 <= obs.cumulative_profit <= 1
        assert 0 <= obs.churn_rate <= 1
        assert 0 <= obs.growth_rate <= 1
        assert 0 <= obs.sponsor_revenue <= 1
        assert 0 <= obs.ad_revenue <= 1
    
    def test_observation_boundary_values(self):
        obs = Observation(
            subscribers=0.0,
            revenue=0.0,
            profit=0.0,
            engagement=0.0,
            week=0.0
        )
        
        assert obs.subscribers == 0.0
        assert obs.revenue == 0.0
        assert obs.profit == 0.0
        assert obs.engagement == 0.0
        assert obs.week == 0.0
    
    def test_observation_max_values(self):
        obs = Observation(
            subscribers=1.0,
            revenue=1.0,
            profit=1.0,
            engagement=1.0,
            week=1.0
        )
        
        assert obs.subscribers == 1.0
        assert obs.revenue == 1.0
        assert obs.profit == 1.0
        assert obs.engagement == 1.0
        assert obs.week == 1.0


class TestObservationProperties:
    """Test observation properties."""
    
    def test_observation_length(self):
        obs = Observation()
        
        assert len(obs) == 10
    
    def test_observation_iteration(self):
        obs = Observation()
        
        values = list(obs)
        
        assert len(values) == 10
        assert values[0] == obs.subscribers
        assert values[1] == obs.revenue
        assert values[2] == obs.profit
        assert values[3] == obs.engagement
        assert values[4] == obs.week
        assert values[5] == obs.cumulative_profit
        assert values[6] == obs.churn_rate
        assert values[7] == obs.growth_rate
        assert values[8] == obs.sponsor_revenue
        assert values[9] == obs.ad_revenue
    
    def test_observation_indexing(self):
        obs = Observation()
        
        assert obs[0] == obs.subscribers
        assert obs[1] == obs.revenue
        assert obs[2] == obs.profit
        assert obs[3] == obs.engagement
        assert obs[4] == obs.week
        assert obs[5] == obs.cumulative_profit
        assert obs[6] == obs.churn_rate
        assert obs[7] == obs.growth_rate
        assert obs[8] == obs.sponsor_revenue
        assert obs[9] == obs.ad_revenue
    
    def test_observation_contains(self):
        obs = Observation()
        
        assert "subscribers" in obs
        assert "revenue" in obs
        assert "profit" in obs
        assert "engagement" in obs
        assert "week" in obs
        assert "cumulative_profit" in obs
        assert "churn_rate" in obs
        assert "growth_rate" in obs
        assert "sponsor_revenue" in obs
        assert "ad_revenue" in obs


class TestObservationEquivalence:
    """Test observation equivalence."""
    
    def test_observation_equality(self):
        obs1 = Observation(
            subscribers=0.5,
            revenue=0.8,
            profit=0.3,
            engagement=0.9,
            week=0.5
        )
        
        obs2 = Observation(
            subscribers=0.5,
            revenue=0.8,
            profit=0.3,
            engagement=0.9,
            week=0.5
        )
        
        assert obs1 == obs2
    
    def test_observation_inequality(self):
        obs1 = Observation(subscribers=0.5)
        obs2 = Observation(subscribers=0.6)
        
        assert obs1 != obs2
    
    def test_observation_inequality_different_engagement(self):
        obs1 = Observation(engagement=0.5)
        obs2 = Observation(engagement=0.6)
        
        assert obs1 != obs2


class TestObservationConversion:
    """Test observation conversion methods."""
    
    def test_observation_to_list(self):
        obs = Observation(
            subscribers=0.5,
            revenue=0.8,
            profit=0.3,
            engagement=0.9,
            week=0.5
        )
        
        obs_list = obs.to_list()
        
        assert len(obs_list) == 10
        assert obs_list[0] == 0.5
        assert obs_list[1] == 0.8
        assert obs_list[2] == 0.3
        assert obs_list[3] == 0.9
        assert obs_list[4] == 0.5
    
    def test_observation_to_array(self):
        obs = Observation(
            subscribers=0.5,
            revenue=0.8,
            profit=0.3,
            engagement=0.9,
            week=0.5
        )
        
        obs_array = obs.to_array()
        
        assert len(obs_array) == 10
        assert obs_array[0] == 0.5
        assert obs_array[1] == 0.8
        assert obs_array[2] == 0.3
        assert obs_array[3] == 0.9
        assert obs_array[4] == 0.5
    
    def test_observation_from_list(self):
        obs_list = [0.5, 0.8, 0.3, 0.9, 0.5, 0.7, 0.03, 0.15, 0.2, 0.1]
        
        obs = Observation.from_list(obs_list)
        
        assert obs.subscribers == 0.5
        assert obs.revenue == 0.8
        assert obs.profit == 0.3
        assert obs.engagement == 0.9
        assert obs.week == 0.5
        assert obs.cumulative_profit == 0.7
        assert obs.churn_rate == 0.03
        assert obs.growth_rate == 0.15
        assert obs.sponsor_revenue == 0.2
        assert obs.ad_revenue == 0.1
    
    def test_observation_from_array(self):
        import numpy as np
        
        obs_array = np.array([0.5, 0.8, 0.3, 0.9, 0.5, 0.7, 0.03, 0.15, 0.2, 0.1])
        
        obs = Observation.from_array(obs_array)
        
        assert obs.subscribers == 0.5
        assert obs.revenue == 0.8
        assert obs.profit == 0.3
        assert obs.engagement == 0.9
        assert obs.week == 0.5
        assert obs.cumulative_profit == 0.7
        assert obs.churn_rate == 0.03
        assert obs.growth_rate == 0.15
        assert obs.sponsor_revenue == 0.2
        assert obs.ad_revenue == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
