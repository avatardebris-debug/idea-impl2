"""Tests for the Newsletter Online Profit Environment."""

import pytest
import json
import csv
import tempfile
import os
from profit_env.config import SimConfig
from profit_env.state import NewsletterState
from profit_env.simulator import NewsletterSimulator, SimulationHistory
from profit_env.cli import main, create_parser
import argparse


class TestSimConfig:
    """Tests for SimConfig class."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
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
    
    def test_custom_values(self):
        """Test that custom values are set correctly."""
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
        assert config.churn_rate == 0.08
        assert config.arpu == 10.00
        assert config.ad_rate == 1.00
        assert config.sponsor_rate == 200.00
        assert config.content_cost == 1000.00
        assert config.operational_cost == 500.00
        assert config.cpc == 5.00
        assert config.seasonal_factor == 1.2
        assert config.competitor_count == 10
        assert config.market_saturation == 0.5
        assert config.conversion_rate == 0.03
        assert config.engagement_rate == 0.85
        assert config.sponsorship_fill_rate == 0.9
        assert config.refund_rate == 0.02
        assert config.tax_rate == 0.30
        assert config.discount_rate == 0.15
    
    def test_invalid_subscriber_count(self):
        """Test that negative subscriber count raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(subscriber_count=-100)
    
    def test_invalid_retention_rate(self):
        """Test that retention rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(retention_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(retention_rate=-0.1)
    
    def test_invalid_growth_rate(self):
        """Test that growth rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(growth_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(growth_rate=-0.1)
    
    def test_invalid_churn_rate(self):
        """Test that churn rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(churn_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(churn_rate=-0.1)
    
    def test_invalid_arpu(self):
        """Test that negative arpu raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(arpu=-1.0)
    
    def test_invalid_ad_rate(self):
        """Test that negative ad_rate raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(ad_rate=-1.0)
    
    def test_invalid_sponsor_rate(self):
        """Test that negative sponsor_rate raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(sponsor_rate=-1.0)
    
    def test_invalid_content_cost(self):
        """Test that negative content_cost raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(content_cost=-1.0)
    
    def test_invalid_operational_cost(self):
        """Test that negative operational_cost raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(operational_cost=-1.0)
    
    def test_invalid_cpc(self):
        """Test that negative cpc raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(cpc=-1.0)
    
    def test_invalid_seasonal_factor(self):
        """Test that seasonal_factor outside [0,2] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(seasonal_factor=-1.0)
        with pytest.raises(ValueError):
            SimConfig(seasonal_factor=2.5)
    
    def test_invalid_competitor_count(self):
        """Test that negative competitor_count raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(competitor_count=-1)
    
    def test_invalid_market_saturation(self):
        """Test that market_saturation outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(market_saturation=1.5)
        with pytest.raises(ValueError):
            SimConfig(market_saturation=-0.1)
    
    def test_invalid_conversion_rate(self):
        """Test that conversion_rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(conversion_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(conversion_rate=-0.1)
    
    def test_invalid_engagement_rate(self):
        """Test that engagement_rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(engagement_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(engagement_rate=-0.1)
    
    def test_invalid_sponsorship_fill_rate(self):
        """Test that sponsorship_fill_rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(sponsorship_fill_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(sponsorship_fill_rate=-0.1)
    
    def test_invalid_refund_rate(self):
        """Test that refund_rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(refund_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(refund_rate=-0.1)
    
    def test_invalid_tax_rate(self):
        """Test that tax_rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(tax_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(tax_rate=-0.1)
    
    def test_invalid_discount_rate(self):
        """Test that discount_rate outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(discount_rate=1.5)
        with pytest.raises(ValueError):
            SimConfig(discount_rate=-0.1)
    
    def test_invalid_channel_mix(self):
        """Test that channel mix not summing to 1.0 raises ValueError."""
        with pytest.raises(ValueError):
            SimConfig(acquisition_channel_mix={
                "organic": 0.5,
                "paid": 0.3,
                "referral": 0.1
            })
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = SimConfig(subscriber_count=5000, retention_rate=0.90)
        result = config.to_dict()
        assert result["subscriber_count"] == 5000
        assert result["retention_rate"] == 0.90
        assert "acquisition_channel_mix" in result
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "subscriber_count": 5000,
            "retention_rate": 0.90,
            "growth_rate": 0.15,
            "churn_rate": 0.08,
            "arpu": 10.00,
            "ad_rate": 1.00,
            "sponsor_rate": 200.00,
            "content_cost": 1000.00,
            "operational_cost": 500.00,
            "cpc": 5.00,
            "seasonal": 1.2,
            "competitors": 10,
            "saturation": 0.5,
            "conversion": 0.03,
            "engagement": 0.85,
            "sponsor_fill": 0.9,
            "refund": 0.02,
            "tax": 0.30,
            "discount": 0.15,
            "acquisition_channel_mix": {
                "organic": 0.4,
                "paid": 0.3,
                "referral": 0.2,
                "social": 0.1
            }
        }
        config = SimConfig.from_dict(data)
        assert config.subscriber_count == 5000
        assert config.retention_rate == 0.90
        assert config.growth_rate == 0.15
        assert config.churn_rate == 0.08
        assert config.arpu == 10.00
        assert config.ad_rate == 1.00
        assert config.sponsor_rate == 200.00
        assert config.content_cost == 1000.00
        assert config.operational_cost == 500.00
        assert config.cpc == 5.00
        assert config.seasonal == 1.2
        assert config.competitors == 10
        assert config.saturation == 0.5
        assert config.conversion == 0.03
        assert config.engagement == 0.85
        assert config.sponsor_fill == 0.9
        assert config.refund == 0.02
        assert config.tax == 0.30
        assert config.discount == 0.15
    
    def test_to_json(self):
        """Test conversion to JSON string."""
        config = SimConfig(subscriber_count=5000, retention_rate=0.90)
        json_str = config.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["subscriber_count"] == 5000
        assert data["retention_rate"] == 0.90
    
    def test_from_json(self):
        """Test creation from JSON string."""
        json_str = json.dumps({
            "subscriber_count": 5000,
            "retention_rate": 0.90,
            "growth_rate": 0.15,
            "churn_rate": 0.08,
            "arpu": 10.00,
            "ad_rate": 1.00,
            "sponsor_rate": 200.00,
            "content_cost": 1000.00,
            "operational_cost": 500.00,
            "cpc": 5.00,
            "seasonal": 1.2,
            "competitors": 10,
            "saturation": 0.5,
            "conversion": 0.03,
            "engagement": 0.85,
            "sponsor_fill": 0.9,
            "refund": 0.02,
            "tax": 0.30,
            "discount": 0.15,
            "acquisition_channel_mix": {
                "organic": 0.4,
                "paid": 0.3,
                "referral": 0.2,
                "social": 0.1
            }
        })
        config = SimConfig.from_json(json_str)
        assert config.subscriber_count == 5000
        assert config.retention_rate == 0.90
        assert config.growth_rate == 0.15
        assert config.churn_rate == 0.08
        assert config.arpu == 10.00
        assert config.ad_rate == 1.00
        assert config.sponsor_rate == 200.00
        assert config.content_cost == 1000.00
        assert config.operational_cost == 500.00
        assert config.cpc == 5.00
        assert config.seasonal == 1.2
        assert config.competitors == 10
        assert config.saturation == 0.5
        assert config.conversion == 0.03
        assert config.engagement == 0.85
        assert config.sponsor_fill == 0.9
        assert config.refund == 0.02
        assert config.tax == 0.30
        assert config.discount == 0.15
    
    def test_get_effective_churn_rate(self):
        """Test effective churn rate calculation."""
        config = SimConfig(churn_rate=0.10)
        
        # At engagement 0, churn should be reduced by 50%
        churn = config.get_effective_churn_rate(0.0)
        assert churn == 0.05
        
        # At engagement 1, churn should be unchanged
        churn = config.get_effective_churn_rate(1.0)
        assert churn == 0.10
        
        # At engagement 0.5, churn should be reduced by 25%
        churn = config.get_effective_churn_rate(0.5)
        assert churn == 0.075
    
    def test_get_effective_growth_rate(self):
        """Test effective growth rate calculation."""
        config = SimConfig(growth_rate=0.10)
        
        # At engagement 0, growth should be unchanged
        growth = config.get_effective_growth_rate(0.0)
        assert growth == 0.10
        
        # At engagement 1, growth should increase by 20%
        growth = config.get_effective_growth_rate(1.0)
        assert growth == 0.12
        
        # At engagement 0.5, growth should increase by 10%
        growth = config.get_effective_growth_rate(0.5)
        assert growth == 0.11


class TestNewsletterState:
    """Tests for NewsletterState class."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        state = NewsletterState()
        assert state.week == 0
        assert state.subscribers == 1000
        assert state.churned == 0
        assert state.acquired == 0
        assert state.revenue == 0.0
        assert state.costs == 0.0
        assert state.profit == 0.0
        assert state.cumulative_profit == 0.0
        assert state.sponsor_revenue == 0.0
        assert state.ad_revenue == 0.0
        assert state.engagement_score == 0.75
    
    def test_invalid_week(self):
        """Test that negative week raises ValueError."""
        with pytest.raises(ValueError):
            NewsletterState(week=-1)
    
    def test_invalid_subscribers(self):
        """Test that negative subscribers raises ValueError."""
        with pytest.raises(ValueError):
            NewsletterState(subscribers=-100)
    
    def test_invalid_engagement_score(self):
        """Test that engagement_score outside [0,1] raises ValueError."""
        with pytest.raises(ValueError):
            NewsletterState(engagement_score=1.5)
        with pytest.raises(ValueError):
            NewsletterState(engagement_score=-0.1)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = NewsletterState(
            week=10,
            subscribers=5000,
            churned=100,
            acquired=200,
            revenue=10000.0,
            costs=5000.0,
            profit=5000.0,
            cumulative_profit=25000.0,
            sponsor_revenue=8000.0,
            ad_revenue=2000.0,
            engagement_score=0.85
        )
        result = state.to_dict()
        assert result["week"] == 10
        assert result["subscribers"] == 5000
        assert result["churned"] == 100
        assert result["acquired"] == 200
        assert result["revenue"] == 10000.0
        assert result["costs"] == 5000.0
        assert result["profit"] == 5000.0
        assert result["cumulative_profit"] == 25000.0
        assert result["sponsor_revenue"] == 8000.0
        assert result["ad_revenue"] == 2000.0
        assert result["engagement_score"] == 0.85
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "week": 10,
            "subscribers": 5000,
            "churned": 100,
            "acquired": 200,
            "revenue": 10000.0,
            "costs": 5000.0,
            "profit": 5000.0,
            "cumulative_profit": 25000.0,
            "sponsor_revenue": 8000.0,
            "ad_revenue": 2000.0,
            "engagement_score": 0.85
        }
        state = NewsletterState.from_dict(data)
        assert state.week == 10
        assert state.subscribers == 5000
        assert state.churned == 100
        assert state.acquired == 200
        assert state.revenue == 10000.0
        assert state.costs == 5000.0
        assert state.profit == 5000.0
        assert state.cumulative_profit == 25000.0
        assert state.sponsor_revenue == 8000.0
        assert state.ad_revenue == 2000.0
        assert state.engagement_score == 0.85
    
    def test_to_json(self):
        """Test conversion to JSON string."""
        state = NewsletterState(
            week=10,
            subscribers=5000,
            churned=100,
            acquired=200,
            revenue=10000.0,
            costs=5000.0,
            profit=5000.0,
            cumulative_profit=25000.0,
            sponsor_revenue=8000.0,
            ad_revenue=2000.0,
            engagement_score=0.85
        )
        json_str = state.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["week"] == 10
        assert data["subscribers"] == 5000
    
    def test_from_json(self):
        """Test creation from JSON string."""
        json_str = json.dumps({
            "week": 10,
            "subscribers": 5000,
            "churned": 100,
            "acquired": 200,
            "revenue": 10000.0,
            "costs": 5000.0,
            "profit": 5000.0,
            "cumulative_profit": 25000.0,
            "sponsor_revenue": 8000.0,
            "ad_revenue": 2000.0,
            "engagement_score": 0.85
        })
        state = NewsletterState.from_json(json_str)
        assert state.week == 10
        assert state.subscribers == 5000
        assert state.churned == 100
        assert state.acquired == 200
        assert state.revenue == 10000.0
        assert state.costs == 5000.0
        assert state.profit == 5000.0
        assert state.cumulative_profit == 25000.0
        assert state.sponsor_revenue == 8000.0
        assert state.ad_revenue == 2000.0
        assert state.engagement_score == 0.85
    
    def test_reset(self):
        """Test reset to initial values."""
        state = NewsletterState(
            week=10,
            subscribers=5000,
            churned=100,
            acquired=200,
            revenue=10000.0,
            costs=5000.0,
            profit=5000.0,
            cumulative_profit=25000.0,
            sponsor_revenue=8000.0,
            ad_revenue=2000.0,
            engagement_score=0.85
        )
        state.reset()
        assert state.week == 0
        assert state.subscribers == 1000
        assert state.churned == 0
        assert state.acquired == 0
        assert state.revenue == 0.0
        assert state.costs == 0.0
        assert state.profit == 0.0
        assert state.cumulative_profit == 0.0
        assert state.sponsor_revenue == 0.0
        assert state.ad_revenue == 0.0
        assert state.engagement_score == 0.75


class TestSimulationHistory:
    """Tests for SimulationHistory class."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        history = SimulationHistory()
        assert history.weeks == 52
        assert len(history.weekly_data) == 0
        assert history.initial_subscribers == 1000
        assert history.final_subscribers == 1000
        assert history.total_revenue == 0.0
        assert history.total_costs == 0.0
        assert history.net_profit == 0.0
        assert history.avg_subscribers == 0.0
        assert history.avg_churn_rate == 0.0
        assert history.total_acquired == 0
        assert history.final_cumulative_profit == 0.0
    
    def test_add_weekly_data(self):
        """Test adding weekly data."""
        history = SimulationHistory()
        state = NewsletterState(
            week=0,
            subscribers=1000,
            churned=0,
            acquired=0,
            revenue=0.0,
            costs=0.0,
            profit=0.0,
            cumulative_profit=0.0,
            sponsor_revenue=0.0,
            ad_revenue=0.0,
            engagement_score=0.75
        )
        history.add_weekly_data(state)
        assert len(history.weekly_data) == 1
        assert history.weekly_data[0].week == 0
    
    def test_get_statistics(self):
        """Test statistics calculation."""
        history = SimulationHistory()
        history.weeks = 52
        history.initial_subscribers = 1000
        
        # Add some weekly data
        for week in range(5):
            state = NewsletterState(
                week=week,
                subscribers=1000 + week * 100,
                churned=week * 10,
                acquired=week * 20,
                revenue=week * 1000.0,
                costs=week * 500.0,
                profit=week * 500.0,
                cumulative_profit=week * 2500.0,
                sponsor_revenue=week * 800.0,
                ad_revenue=week * 200.0,
                engagement_score=0.75 + week * 0.01
            )
            history.add_weekly_data(state)
        
        stats = history.get_statistics()
        assert stats["total_revenue"] == 10000.0
        assert stats["total_costs"] == 5000.0
        assert stats["net_profit"] == 5000.0
        assert stats["avg_subscribers"] == 1200.0
        assert stats["final_subscribers"] == 1500
        assert stats["final_cumulative_profit"] == 10000.0
        assert stats["avg_churn_rate"] == 0.0
        assert stats["total_acquired"] == 100
    
    def test_get_weekly_data(self):
        """Test getting weekly data."""
        history = SimulationHistory()
        for week in range(5):
            state = NewsletterState(
                week=week,
                subscribers=1000 + week * 100,
                churned=week * 10,
                acquired=week * 20,
                revenue=week * 1000.0,
                costs=week * 500.0,
                profit=week * 500.0,
                cumulative_profit=week * 2500.0,
                sponsor_revenue=week * 800.0,
                ad_revenue=week * 200.0,
                engagement_score=0.75 + week * 0.01
            )
            history.add_weekly_data(state)
        
        weekly_data = history.get_weekly_data()
        assert len(weekly_data) == 5
        assert weekly_data[0].week == 0
        assert weekly_data[4].week == 4
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        history = SimulationHistory()
        history.weeks = 52
        history.initial_subscribers = 1000
        
        state = NewsletterState(
            week=0,
            subscribers=1000,
            churned=0,
            acquired=0,
            revenue=0.0,
            costs=0.0,
            profit=0.0,
            cumulative_profit=0.0,
            sponsor_revenue=0.0,
            ad_revenue=0.0,
            engagement_score=0.75
        )
        history.add_weekly_data(state)
        
        result = history.to_dict()
        assert result["weeks"] == 52
        assert result["initial_subscribers"] == 1000
        assert len(result["weekly_data"]) == 1
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "weeks": 52,
            "initial_subscribers": 1000,
            "final_subscribers": 1500,
            "total_revenue": 10000.0,
            "total_costs": 5000.0,
            "net_profit": 5000.0,
            "avg_subscribers": 1200.0,
            "avg_churn_rate": 0.05,
            "total_acquired": 100,
            "final_cumulative_profit": 10000.0,
            "weekly_data": [
                {
                    "week": 0,
                    "subscribers": 1000,
                    "churned": 0,
                    "acquired": 0,
                    "revenue": 0.0,
                    "costs": 0.0,
                    "profit": 0.0,
                    "cumulative_profit": 0.0,
                    "sponsor_revenue": 0.0,
                    "ad_revenue": 0.0,
                    "engagement_score": 0.75
                }
            ]
        }
        history = SimulationHistory.from_dict(data)
        assert history.weeks == 52
        assert history.initial_subscribers == 1000
        assert len(history.weekly_data) == 1
    
    def test_to_json(self):
        """Test conversion to JSON string."""
        history = SimulationHistory()
        history.weeks = 52
        history.initial_subscribers = 1000
        
        state = NewsletterState(
            week=0,
            subscribers=1000,
            churned=0,
            acquired=0,
            revenue=0.0,
            costs=0.0,
            profit=0.0,
            cumulative_profit=0.0,
            sponsor_revenue=0.0,
            ad_revenue=0.0,
            engagement_score=0.75
        )
        history.add_weekly_data(state)
        
        json_str = history.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["weeks"] == 52
        assert data["initial_subscribers"] == 1000
    
    def test_from_json(self):
        """Test creation from JSON string."""
        json_str = json.dumps({
            "weeks": 52,
            "initial_subscribers": 1000,
            "final_subscribers": 1500,
            "total_revenue": 10000.0,
            "total_costs": 5000.0,
            "net_profit": 5000.0,
            "avg_subscribers": 1200.0,
            "avg_churn_rate": 0.05,
            "total_acquired": 100,
            "final_cumulative_profit": 10000.0,
            "weekly_data": [
                {
                    "week": 0,
                    "subscribers": 1000,
                    "churned": 0,
                    "acquired": 0,
                    "revenue": 0.0,
                    "costs": 0.0,
                    "profit": 0.0,
                    "cumulative_profit": 0.0,
                    "sponsor_revenue": 0.0,
                    "ad_revenue": 0.0,
                    "engagement_score": 0.75
                }
            ]
        })
        history = SimulationHistory.from_json(json_str)
        assert history.weeks == 52
        assert history.initial_subscribers == 1000
        assert len(history.weekly_data) == 1


class TestNewsletterSimulator:
    """Tests for NewsletterSimulator class."""
    
    def test_default_config(self):
        """Test that simulator uses default config."""
        simulator = NewsletterSimulator()
        assert simulator.config.subscriber_count == 1000
        assert simulator.config.retention_rate == 0.95
        assert simulator.config.growth_rate == 0.1
    
    def test_custom_config(self):
        """Test that simulator uses custom config."""
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
        simulator = NewsletterSimulator(config)
        assert simulator.config.subscriber_count == 5000
        assert simulator.config.retention_rate == 0.90
        assert simulator.config.growth_rate == 0.15
        assert simulator.config.churn_rate == 0.08
        assert simulator.config.arpu == 10.00
        assert simulator.config.ad_rate == 1.00
        assert simulator.config.sponsor_rate == 200.00
        assert simulator.config.content_cost == 1000.00
        assert simulator.config.operational_cost == 500.00
        assert simulator.config.cpc == 5.00
        assert simulator.config.seasonal_factor == 1.2
        assert simulator.config.competitor_count == 10
        assert simulator.config.market_saturation == 0.5
        assert simulator.config.conversion_rate == 0.03
        assert simulator.config.engagement_rate == 0.85
        assert simulator.config.sponsorship_fill_rate == 0.9
        assert simulator.config.refund_rate == 0.02
        assert simulator.config.tax_rate == 0.30
        assert simulator.config.discount_rate == 0.15
    
    def test_run_simulation(self):
        """Test running a simulation."""
        config = SimConfig(
            subscriber_count=1000,
            retention_rate=0.95,
            growth_rate=0.1,
            churn_rate=0.05,
            arpu=5.00,
            ad_rate=0.50,
            sponsor_rate=100.00,
            content_cost=500.00,
            operational_cost=300.00,
            cpc=2.50,
            seasonal=1.0,
            competitors=5,
            saturation=0.3,
            conversion=0.02,
            engagement=0.75,
            sponsor_fill=0.8,
            refund=0.01,
            tax=0.25,
            discount=0.1
        )
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.weeks == 10
        assert len(history.weekly_data) == 10
        assert history.initial_subscribers == 1000
        assert history.final_subscribers > 1000
        assert history.total_revenue > 0
        assert history.total_costs > 0
        assert history.net_profit > 0
        assert history.avg_subscribers > 1000
        assert history.total_acquired > 0
    
    def test_run_simulation_with_custom_weeks(self):
        """Test running simulation with custom number of weeks."""
        config = SimConfig()
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(20)
        
        assert history.weeks == 20
        assert len(history.weekly_data) == 20
    
    def test_run_simulation_with_custom_subscribers(self):
        """Test running simulation with custom initial subscribers."""
        config = SimConfig(subscriber_count=5000)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.initial_subscribers == 5000
        assert history.final_subscribers > 5000
    
    def test_run_simulation_with_custom_arpu(self):
        """Test running simulation with custom ARPU."""
        config = SimConfig(arpu=10.00)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0
    
    def test_run_simulation_with_custom_costs(self):
        """Test running simulation with custom costs."""
        config = SimConfig(
            content_cost=1000.00,
            operational_cost=500.00
        )
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_costs > 0
        stats = history.get_statistics()
        assert stats["total_costs"] > 0
    
    def test_run_simulation_with_custom_cpc(self):
        """Test running simulation with custom CPC."""
        config = SimConfig(cpc=5.00)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_costs > 0
        stats = history.get_statistics()
        assert stats["total_costs"] > 0
    
    def test_run_simulation_with_custom_seasonal(self):
        """Test running simulation with custom seasonal factor."""
        config = SimConfig(seasonal_factor=1.2)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0
    
    def test_run_simulation_with_custom_competitors(self):
        """Test running simulation with custom number of competitors."""
        config = SimConfig(competitor_count=10)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0
    
    def test_run_simulation_with_custom_saturation(self):
        """Test running simulation with custom market saturation."""
        config = SimConfig(market_saturation=0.5)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0
    
    def test_run_simulation_with_custom_conversion(self):
        """Test running simulation with custom conversion rate."""
        config = SimConfig(conversion_rate=0.03)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_acquired > 0
        stats = history.get_statistics()
        assert stats["total_acquired"] > 0
    
    def test_run_simulation_with_custom_engagement(self):
        """Test running simulation with custom engagement score."""
        config = SimConfig(engagement_rate=0.85)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0
    
    def test_run_simulation_with_custom_sponsor_fill(self):
        """Test running simulation with custom sponsor fill rate."""
        config = SimConfig(sponsorship_fill_rate=0.9)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0
    
    def test_run_simulation_with_custom_refund(self):
        """Test running simulation with custom refund rate."""
        config = SimConfig(refund=0.02)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0
    
    def test_run_simulation_with_custom_tax(self):
        """Test running simulation with custom tax rate."""
        config = SimConfig(tax=0.30)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0
    
    def test_run_simulation_with_custom_discount(self):
        """Test running simulation with custom discount rate."""
        config = SimConfig(discount=0.15)
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(10)
        
        assert history.total_revenue > 0
        stats = history.get_statistics()
        assert stats["total_revenue"] > 0


class TestCLI:
    """Tests for CLI functionality."""
    
    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser is not None
        assert isinstance(parser, argparse.ArgumentParser)
    
    def test_main_no_args(self):
        """Test main with no arguments."""
        result = main()
        assert result == 1
    
    def test_main_sim_run(self):
        """Test sim run command."""
        result = main(["sim", "run", "--weeks", "10", "--subscribers", "1000"])
        assert result == 0
    
    def test_main_sim_stats(self):
        """Test sim stats command."""
        result = main(["sim", "stats", "--weeks", "10", "--subscribers", "1000"])
        assert result == 0
    
    def test_main_sim_export_json(self):
        """Test sim export command with JSON format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name
        
        try:
            result = main([
                "sim", "export",
                "--weeks", "10",
                "--subscribers", "1000",
                "--output", temp_file,
                "--format", "json"
            ])
            assert result == 0
            assert os.path.exists(temp_file)
            
            with open(temp_file, "r") as f:
                data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 10
        finally:
            os.unlink(temp_file)
    
    def test_main_sim_export_csv(self):
        """Test sim export command with CSV format."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_file = f.name
        
        try:
            result = main([
                "sim", "export",
                "--weeks", "10",
                "--subscribers", "1000",
                "--output", temp_file,
                "--format", "csv"
            ])
            assert result == 0
            assert os.path.exists(temp_file)
            
            with open(temp_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) == 10
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
