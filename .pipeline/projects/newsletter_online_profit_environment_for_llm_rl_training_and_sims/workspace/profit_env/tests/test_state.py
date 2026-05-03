"""Tests for state module."""

import pytest
import json
from profit_env.config import SimConfig
from profit_env.state import NewsletterState, SimulationHistory


class TestNewsletterStateInitialization:
    """Test state initialization."""
    
    def test_state_creation(self):
        state = NewsletterState()
        
        assert state.week == 0
        assert state.subscribers == 1000
        assert state.revenue == 0.0
        assert state.costs == 0.0
        assert state.profit == 0.0
        assert state.cumulative_profit == 0.0
        assert state.churned == 0
        assert state.acquired == 0
        assert state.engagement_score == 0.75
        assert state.sponsor_revenue == 0.0
        assert state.ad_revenue == 0.0
        assert state.churn_rate == 0.05
        assert state.growth_rate == 0.1
        assert state.arpu == 5.00
    
    def test_state_with_custom_values(self):
        state = NewsletterState(
            week=5,
            subscribers=5000,
            revenue=10000.0,
            costs=8000.0,
            engagement_score=0.9
        )
        
        assert state.week == 5
        assert state.subscribers == 5000
        assert state.revenue == 10000.0
        assert state.costs == 8000.0
        assert state.engagement_score == 0.9
    
    def test_state_default_values(self):
        state = NewsletterState()
        
        assert state.week == 0
        assert state.subscribers == 1000
        assert state.revenue == 0.0
        assert state.costs == 0.0
        assert state.profit == 0.0
        assert state.cumulative_profit == 0.0
        assert state.churned == 0
        assert state.acquired == 0
        assert state.engagement_score == 0.75
        assert state.sponsor_revenue == 0.0
        assert state.ad_revenue == 0.0
        assert state.churn_rate == 0.05
        assert state.growth_rate == 0.1
        assert state.arpu == 5.00


class TestNewsletterStateValidation:
    """Test state validation."""
    
    def test_state_rejects_negative_week(self):
        with pytest.raises(ValueError):
            NewsletterState(week=-1)
    
    def test_state_rejects_negative_subscribers(self):
        with pytest.raises(ValueError):
            NewsletterState(subscribers=-100)
    
    def test_state_rejects_invalid_engagement_score(self):
        with pytest.raises(ValueError):
            NewsletterState(engagement_score=1.5)
        
        with pytest.raises(ValueError):
            NewsletterState(engagement_score=-0.5)
    
    def test_state_accepts_valid_values(self):
        state = NewsletterState(
            week=100,
            subscribers=100000,
            engagement_score=1.0
        )
        
        assert state.week == 100
        assert state.subscribers == 100000
        assert state.engagement_score == 1.0
    
    def test_state_accepts_zero_values(self):
        state = NewsletterState(
            week=0,
            subscribers=0,
            engagement_score=0.0
        )
        
        assert state.week == 0
        assert state.subscribers == 0
        assert state.engagement_score == 0.0


class TestNewsletterStateToDict:
    """Test state to dictionary conversion."""
    
    def test_state_to_dict(self):
        state = NewsletterState(
            week=5,
            subscribers=5000,
            revenue=10000.0,
            costs=8000.0,
            engagement_score=0.9
        )
        
        state_dict = state.to_dict()
        
        assert state_dict["week"] == 5
        assert state_dict["subscribers"] == 5000
        assert state_dict["revenue"] == 10000.0
        assert state_dict["costs"] == 8000.0
        assert state_dict["engagement_score"] == 0.9
        assert "profit" in state_dict
        assert "cumulative_profit" in state_dict
        assert "churned" in state_dict
        assert "acquired" in state_dict
        assert "sponsor_revenue" in state_dict
        assert "ad_revenue" in state_dict
        assert "churn_rate" in state_dict
        assert "growth_rate" in state_dict
        assert "arpu" in state_dict
    
    def test_state_to_dict_all_fields(self):
        state = NewsletterState()
        
        state_dict = state.to_dict()
        
        assert len(state_dict) == 16
        assert all(key in state_dict for key in [
            "week", "subscribers", "revenue", "costs", "profit",
            "cumulative_profit", "churned", "acquired", "engagement_score",
            "sponsor_revenue", "ad_revenue", "churn_rate", "growth_rate", "arpu",
            "total_revenue", "net_profit"
        ])


class TestNewsletterStateFromDict:
    """Test state from dictionary creation."""
    
    def test_state_from_dict(self):
        state_dict = {
            "week": 5,
            "subscribers": 5000,
            "revenue": 10000.0,
            "costs": 8000.0,
            "engagement_score": 0.9,
            "profit": 2000.0,
            "cumulative_profit": 5000.0,
            "churned": 100,
            "acquired": 200,
            "sponsor_revenue": 1000.0,
            "ad_revenue": 500.0,
            "churn_rate": 0.03,
            "growth_rate": 0.15,
            "arpu": 10.00,
            "total_revenue": 13000.0,
            "net_profit": 5000.0
        }
        
        state = NewsletterState.from_dict(state_dict)
        
        assert state.week == 5
        assert state.subscribers == 5000
        assert state.revenue == 10000.0
        assert state.costs == 8000.0
        assert state.engagement_score == 0.9
        assert state.profit == 2000.0
        assert state.cumulative_profit == 5000.0
        assert state.churned == 100
        assert state.acquired == 200
        assert state.sponsor_revenue == 1000.0
        assert state.ad_revenue == 500.0
        assert state.churn_rate == 0.03
        assert state.growth_rate == 0.15
        assert state.arpu == 10.00
        assert state.total_revenue == 13000.0
        assert state.net_profit == 5000.0
    
    def test_state_from_dict_with_defaults(self):
        state_dict = {
            "week": 5,
            "subscribers": 5000
        }
        
        state = NewsletterState.from_dict(state_dict)
        
        assert state.week == 5
        assert state.subscribers == 5000
        assert state.revenue == 0.0
        assert state.costs == 0.0
        assert state.engagement_score == 0.75
        assert state.churn_rate == 0.05
        assert state.growth_rate == 0.1
        assert state.arpu == 5.00


class TestNewsletterStateSerialization:
    """Test state serialization."""
    
    def test_state_json_serialization(self):
        state = NewsletterState(
            week=5,
            subscribers=5000,
            revenue=10000.0,
            costs=8000.0,
            engagement_score=0.9
        )
        
        json_str = state.to_json()
        
        assert isinstance(json_str, str)
        
        # Parse and verify
        parsed = json.loads(json_str)
        assert parsed["week"] == 5
        assert parsed["subscribers"] == 5000
        assert parsed["revenue"] == 10000.0
        assert parsed["costs"] == 8000.0
        assert parsed["engagement_score"] == 0.9
    
    def test_state_json_deserialization(self):
        state = NewsletterState(
            week=5,
            subscribers=5000,
            revenue=10000.0,
            costs=8000.0,
            engagement_score=0.9
        )
        
        json_str = state.to_json()
        restored_state = NewsletterState.from_json(json_str)
        
        assert restored_state.week == state.week
        assert restored_state.subscribers == state.subscribers
        assert restored_state.revenue == state.revenue
        assert restored_state.costs == state.costs
        assert restored_state.engagement_score == state.engagement_score
        assert restored_state.profit == state.profit
        assert restored_state.cumulative_profit == state.cumulative_profit
        assert restored_state.churned == state.churned
        assert restored_state.acquired == state.acquired
        assert restored_state.sponsor_revenue == state.sponsor_revenue
        assert restored_state.ad_revenue == state.ad_revenue
        assert restored_state.churn_rate == state.churn_rate
        assert restored_state.growth_rate == state.growth_rate
        assert restored_state.arpu == state.arpu
        assert restored_state.total_revenue == state.total_revenue
        assert restored_state.net_profit == state.net_profit


class TestNewsletterStateEquivalence:
    """Test state equivalence."""
    
    def test_state_equality(self):
        state1 = NewsletterState(
            week=5,
            subscribers=5000,
            engagement_score=0.9
        )
        
        state2 = NewsletterState(
            week=5,
            subscribers=5000,
            engagement_score=0.9
        )
        
        assert state1 == state2
    
    def test_state_inequality(self):
        state1 = NewsletterState(week=5, subscribers=5000)
        state2 = NewsletterState(week=5, subscribers=6000)
        
        assert state1 != state2
    
    def test_state_inequality_different_week(self):
        state1 = NewsletterState(week=5, subscribers=5000)
        state2 = NewsletterState(week=6, subscribers=5000)
        
        assert state1 != state2


class TestNewsletterStateProperties:
    """Test state properties."""
    
    def test_state_profit_calculation(self):
        state = NewsletterState(
            revenue=10000.0,
            costs=8000.0
        )
        
        assert state.profit == 2000.0
    
    def test_state_cumulative_profit_calculation(self):
        state = NewsletterState(
            revenue=10000.0,
            costs=8000.0,
            cumulative_profit=5000.0
        )
        
        assert state.cumulative_profit == 7000.0
    
    def test_state_total_revenue(self):
        state = NewsletterState(
            revenue=10000.0,
            sponsor_revenue=2000.0,
            ad_revenue=1000.0
        )
        
        assert state.total_revenue == 13000.0
    
    def test_state_net_profit(self):
        state = NewsletterState(
            revenue=10000.0,
            costs=8000.0,
            sponsor_revenue=2000.0,
            ad_revenue=1000.0
        )
        
        assert state.net_profit == 5000.0


class TestSimulationHistory:
    """Test simulation history functionality."""
    
    def test_history_creation(self):
        history = SimulationHistory()
        
        assert len(history) == 0
        assert history.get_weekly_data() == []
    
    def test_history_add_record(self):
        history = SimulationHistory()
        
        record = NewsletterState(week=0, subscribers=1000)
        history.add_weekly_data(record)
        
        assert len(history) == 1
        assert history[0].week == 0
        assert history[0].subscribers == 1000
    
    def test_history_get_week(self):
        history = SimulationHistory()
        
        history.add_weekly_data(NewsletterState(week=0, subscribers=1000))
        history.add_weekly_data(NewsletterState(week=1, subscribers=1100))
        
        assert history.get_week(0).subscribers == 1000
        assert history.get_week(1).subscribers == 1100
        assert history.get_week(5) is None
    
    def test_history_get_weeks(self):
        history = SimulationHistory()
        
        for i in range(5):
            history.add_weekly_data(NewsletterState(week=i, subscribers=1000 + i * 100))
        
        weeks = history.get_weeks(1, 3)
        
        assert len(weeks) == 3
        assert weeks[0].week == 1
        assert weeks[2].week == 3
    
    def test_history_get_statistics(self):
        history = SimulationHistory()
        
        history.add_weekly_data(NewsletterState(
            week=0,
            subscribers=1000,
            revenue=1000.0,
            costs=800.0,
            profit=200.0,
            cumulative_profit=200.0,
            churned=50,
            acquired=100
        ))
        
        stats = history.get_statistics()
        
        assert stats["total_revenue"] == 1000.0
        assert stats["total_costs"] == 800.0
        assert stats["net_profit"] == 200.0
        assert stats["final_subscribers"] == 1000
        assert stats["total_acquired"] == 100
    
    def test_history_iteration(self):
        history = SimulationHistory()
        
        for i in range(3):
            history.add_weekly_data(NewsletterState(week=i))
        
        weeks = [record.week for record in history]
        
        assert weeks == [0, 1, 2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
