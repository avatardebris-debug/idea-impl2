"""Configuration module for the Newsletter Online Profit Environment."""

from dataclasses import dataclass, field


@dataclass
class SimConfig:
    """Simulation configuration for the newsletter profit environment.
    
    Default values represent a typical newsletter business scenario.
    """
    
    # Subscriber metrics
    subscriber_count: int = 1000
    retention_rate: float = 0.95
    churn_rate: float = 0.05
    growth_rate: float = 0.1
    
    # Revenue metrics
    cpc: float = 2.50  # Cost per click for acquisition
    arpu: float = 5.00  # Average revenue per user
    ad_rate: float = 0.50  # Revenue per subscriber from ads
    sponsor_rate: float = 100.00  # Revenue per sponsor
    sponsorship_fill_rate: float = 0.8  # Fraction of sponsors that fill
    refund_rate: float = 0.01  # Fraction of revenue refunded
    
    # Cost metrics
    content_cost: float = 500.00  # Weekly content production cost
    operational_cost: float = 300.00  # Weekly operational cost
    tax_rate: float = 0.25  # Tax rate on profits
    
    # Market metrics
    seasonal_factor: float = 1.0
    competitor_count: int = 5
    market_saturation: float = 0.3
    conversion_rate: float = 0.02
    engagement_rate: float = 0.75
    discount_rate: float = 0.1
    
    # Acquisition channel mix
    acquisition_channel_mix: dict = field(default_factory=lambda: {
        "organic": 0.4,
        "paid": 0.3,
        "social": 0.2,
        "referral": 0.1
    })
    
    def __post_init__(self):
        """Validate configuration values."""
        # Validate subscriber count
        if self.subscriber_count < 0:
            raise ValueError("subscriber_count must be non-negative")
        
        # Validate rates are in [0, 1] range
        if not (0 <= self.retention_rate <= 1):
            raise ValueError("retention_rate must be between 0 and 1")
        if not (0 <= self.churn_rate <= 1):
            raise ValueError("churn_rate must be between 0 and 1")
        if not (0 <= self.growth_rate <= 1):
            raise ValueError("growth_rate must be between 0 and 1")
        if not (0 <= self.tax_rate <= 1):
            raise ValueError("tax_rate must be between 0 and 1")
        if not (0 <= self.refund_rate <= 1):
            raise ValueError("refund_rate must be between 0 and 1")
        if not (0 <= self.sponsorship_fill_rate <= 1):
            raise ValueError("sponsorship_fill_rate must be between 0 and 1")
        if not (0 <= self.market_saturation <= 1):
            raise ValueError("market_saturation must be between 0 and 1")
        if not (0 <= self.conversion_rate <= 1):
            raise ValueError("conversion_rate must be between 0 and 1")
        if not (0 <= self.engagement_rate <= 1):
            raise ValueError("engagement_rate must be between 0 and 1")
        if not (0 <= self.discount_rate <= 1):
            raise ValueError("discount_rate must be between 0 and 1")
        
        # Validate churn + retention <= 1
        if self.churn_rate + self.retention_rate > 1.0:
            raise ValueError("churn_rate + retention_rate must be <= 1.0")
        
        # Validate non-negative costs and revenues
        if self.cpc < 0:
            raise ValueError("cpc must be non-negative")
        if self.arpu < 0:
            raise ValueError("arpu must be non-negative")
        if self.content_cost < 0:
            raise ValueError("content_cost must be non-negative")
        if self.operational_cost < 0:
            raise ValueError("operational_cost must be non-negative")
        
        # Validate growth with zero subscribers
        if self.subscriber_count == 0 and self.growth_rate > 0:
            raise ValueError("Cannot have growth_rate > 0 with subscriber_count = 0")
        
        # Validate competitor count
        if self.competitor_count < 0:
            raise ValueError("competitor_count must be non-negative")
        
        # Validate channel mix sums to 1
        channel_sum = sum(self.acquisition_channel_mix.values())
        if abs(channel_sum - 1.0) > 0.01:
            raise ValueError("acquisition_channel_mix must sum to approximately 1.0")
