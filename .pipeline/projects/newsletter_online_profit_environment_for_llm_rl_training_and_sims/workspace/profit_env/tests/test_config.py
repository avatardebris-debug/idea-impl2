"""Tests for config module."""

import pytest
from profit_env.config import SimConfig


class TestSimConfigInitialization:
    """Test configuration initialization."""
    
    def test_config_creation(self):
        config = SimConfig()
        
        assert config.subscriber_count == 1000
        assert config.engagement_rate == 0.75
        assert config.max_steps == 52
        assert config.cpc == 2.00
        assert config.arpu == 5.00
        assert config.sponsor_rate == 0.01
        assert config.ad_rate == 0.001
        assert config.content_cost == 100.0
        assert config.operational_cost == 50.0
        assert config.churn_rate == 0.05
        assert config.growth_rate == 0.1
        assert config.sponsorship_fill_rate == 0.5
    
    def test_config_with_custom_values(self):
        config = SimConfig(
            subscriber_count=5000,
            cpc=5.00,
            arpu=10.00,
            max_steps=100
        )
        
        assert config.subscriber_count == 5000
        assert config.cpc == 5.00
        assert config.arpu == 10.00
        assert config.max_steps == 100
    
    def test_config_default_values(self):
        config = SimConfig()
        
        assert config.subscriber_count == 1000
        assert config.engagement_rate == 0.75
        assert config.max_steps == 52
        assert config.cpc == 2.00
        assert config.arpu == 5.00
        assert config.sponsor_rate == 0.01
        assert config.ad_rate == 0.001
        assert config.content_cost == 100.0
        assert config.operational_cost == 50.0
        assert config.churn_rate == 0.05
        assert config.growth_rate == 0.1
        assert config.sponsorship_fill_rate == 0.5


class TestSimConfigValidation:
    """Test configuration validation."""
    
    def test_config_accepts_valid_values(self):
        config = SimConfig(
            subscriber_count=10000,
            cpc=10.00,
            arpu=100.00,
            max_steps=1000
        )
        
        assert config.subscriber_count == 10000
        assert config.cpc == 10.00
        assert config.arpu == 100.00
        assert config.max_steps == 1000
    
    def test_config_accepts_zero_values(self):
        config = SimConfig(
            subscriber_count=0,
            cpc=0.00,
            arpu=0.00,
            max_steps=0
        )
        
        assert config.subscriber_count == 0
        assert config.cpc == 0.00
        assert config.arpu == 0.00
        assert config.max_steps == 0
    
    def test_config_accepts_small_values(self):
        config = SimConfig(
            subscriber_count=1,
            cpc=0.01,
            arpu=0.01,
            max_steps=1
        )
        
        assert config.subscriber_count == 1
        assert config.cpc == 0.01
        assert config.arpu == 0.01
        assert config.max_steps == 1


class TestSimConfigProperties:
    """Test configuration properties."""
    
    def test_config_has_all_properties(self):
        config = SimConfig()
        
        assert hasattr(config, "subscriber_count")
        assert hasattr(config, "engagement_rate")
        assert hasattr(config, "max_steps")
        assert hasattr(config, "cpc")
        assert hasattr(config, "arpu")
        assert hasattr(config, "sponsor_rate")
        assert hasattr(config, "ad_rate")
        assert hasattr(config, "content_cost")
        assert hasattr(config, "operational_cost")
        assert hasattr(config, "churn_rate")
        assert hasattr(config, "growth_rate")
        assert hasattr(config, "sponsorship_fill_rate")
    
    def test_config_values_are_correct_types(self):
        config = SimConfig()
        
        assert isinstance(config.subscriber_count, int)
        assert isinstance(config.engagement_rate, float)
        assert isinstance(config.max_steps, int)
        assert isinstance(config.cpc, float)
        assert isinstance(config.arpu, float)
        assert isinstance(config.sponsor_rate, float)
        assert isinstance(config.ad_rate, float)
        assert isinstance(config.content_cost, float)
        assert isinstance(config.operational_cost, float)
        assert isinstance(config.churn_rate, float)
        assert isinstance(config.growth_rate, float)
        assert isinstance(config.sponsorship_fill_rate, float)


class TestSimConfigModification:
    """Test configuration modification."""
    
    def test_config_can_be_modified(self):
        config = SimConfig()
        
        config.subscriber_count = 5000
        config.cpc = 5.00
        config.arpu = 10.00
        
        assert config.subscriber_count == 5000
        assert config.cpc == 5.00
        assert config.arpu == 10.00
    
    def test_config_values_can_be_set_to_zero(self):
        config = SimConfig()
        
        config.subscriber_count = 0
        config.cpc = 0.00
        config.arpu = 0.00
        
        assert config.subscriber_count == 0
        assert config.cpc == 0.00
        assert config.arpu == 0.00


class TestSimConfigRealism:
    """Test configuration realism."""
    
    def test_config_reasonable_defaults(self):
        config = SimConfig()
        
        # Subscriber count should be reasonable
        assert config.subscriber_count > 0
        assert config.subscriber_count < 100000
        
        # CPC should be reasonable
        assert config.cpc > 0
        assert config.cpc < 100.00
        
        # ARPU should be reasonable
        assert config.arpu > 0
        assert config.arpu < 1000.00
        
        # Max steps should be reasonable
        assert config.max_steps > 0
        assert config.max_steps < 1000
        
        # Rates should be between 0 and 1
        assert 0 <= config.engagement_rate <= 1
        assert 0 <= config.sponsor_rate <= 1
        assert 0 <= config.ad_rate <= 1
        assert 0 <= config.churn_rate <= 1
        assert 0 <= config.growth_rate <= 1
        assert 0 <= config.sponsorship_fill_rate <= 1
    
    def test_config_cost_reasonable(self):
        config = SimConfig()
        
        # Costs should be positive
        assert config.content_cost > 0
        assert config.operational_cost > 0
        
        # Costs should be reasonable
        assert config.content_cost < 10000.0
        assert config.operational_cost < 10000.0


class TestSimConfigEdgeCases:
    """Test edge cases."""
    
    def test_config_with_very_large_values(self):
        config = SimConfig(
            subscriber_count=1000000,
            cpc=1000.00,
            arpu=10000.00,
            max_steps=10000
        )
        
        assert config.subscriber_count == 1000000
        assert config.cpc == 1000.00
        assert config.arpu == 10000.00
        assert config.max_steps == 10000
    
    def test_config_with_very_small_values(self):
        config = SimConfig(
            subscriber_count=1,
            cpc=0.01,
            arpu=0.01,
            max_steps=1
        )
        
        assert config.subscriber_count == 1
        assert config.cpc == 0.01
        assert config.arpu == 0.01
        assert config.max_steps == 1
    
    def test_config_with_extreme_rates(self):
        config = SimConfig(
            engagement_rate=0.0,
            sponsor_rate=0.0,
            ad_rate=0.0,
            churn_rate=1.0,
            growth_rate=1.0,
            sponsorship_fill_rate=0.0
        )
        
        assert config.engagement_rate == 0.0
        assert config.sponsor_rate == 0.0
        assert config.ad_rate == 0.0
        assert config.churn_rate == 1.0
        assert config.growth_rate == 1.0
        assert config.sponsorship_fill_rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
