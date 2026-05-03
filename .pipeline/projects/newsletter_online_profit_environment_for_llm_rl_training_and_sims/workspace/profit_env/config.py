"""Configuration module for the Newsletter Online Profit Environment."""

import json
from dataclasses import dataclass, field
from typing import Dict, Optional
from .state import NewsletterState


@dataclass
class SimConfig:
    """Configuration parameters for the newsletter simulation.
    
    This class holds all the configurable parameters for the simulation,
    including subscriber counts, rates, costs, and seasonal factors.
    """
    
    # Core parameters
    subscriber_count: int = 1000
    retention_rate: float = 0.95
    growth_rate: float = 0.1
    churn_rate: float = 0.05
    engagement_rate: float = 0.75
    
    # Revenue parameters
    arpu: float = 5.00
    ad_rate: float = 0.001
    sponsor_rate: float = 0.01
    sponsorship_fill_rate: float = 0.5
    
    # Cost parameters
    content_cost: float = 100.0
    operational_cost: float = 50.0
    cpc: float = 2.00
    
    # Market parameters
    seasonal_factor: float = 1.0
    competitor_count: int = 5
    market_saturation: float = 0.3
    conversion_rate: float = 0.02
    
    # Additional parameters
    refund_rate: float = 0.01
    tax_rate: float = 0.25
    discount_rate: float = 0.1
    
    # Simulation control
    max_steps: int = 52
    
    # Channel mix for acquisition
    acquisition_channel_mix: Dict[str, float] = field(default_factory=lambda: {
        "organic": 0.4,
        "paid": 0.3,
        "referral": 0.2,
        "social": 0.1
    })
    
    def __post_init__(self):
        """Validate configuration values after initialization."""
        # Validate subscriber_count
        if self.subscriber_count < 0:
            raise ValueError("subscriber_count must be non-negative")
        
        # Validate retention_rate
        if not 0 <= self.retention_rate <= 1:
            raise ValueError("retention_rate must be between 0 and 1")
        
        # Validate growth_rate
        if not 0 <= self.growth_rate <= 1:
            raise ValueError("growth_rate must be between 0 and 1")
        
        # Validate churn_rate
        if not 0 <= self.churn_rate <= 1:
            raise ValueError("churn_rate must be between 0 and 1")
        
        # Validate arpu
        if self.arpu < 0:
            raise ValueError("arpu must be non-negative")
        
        # Validate ad_rate
        if self.ad_rate < 0:
            raise ValueError("ad_rate must be non-negative")
        
        # Validate sponsor_rate
        if self.sponsor_rate < 0:
            raise ValueError("sponsor_rate must be non-negative")
        
        # Validate content_cost
        if self.content_cost < 0:
            raise ValueError("content_cost must be non-negative")
        
        # Validate operational_cost
        if self.operational_cost < 0:
            raise ValueError("operational_cost must be non-negative")
        
        # Validate cpc
        if self.cpc < 0:
            raise ValueError("cpc must be non-negative")
        
        # Validate seasonal_factor
        if not 0 <= self.seasonal_factor <= 2:
            raise ValueError("seasonal_factor must be between 0 and 2")
        
        # Validate competitor_count
        if self.competitor_count < 0:
            raise ValueError("competitor_count must be non-negative")
        
        # Validate market_saturation
        if not 0 <= self.market_saturation <= 1:
            raise ValueError("market_saturation must be between 0 and 1")
        
        # Validate conversion_rate
        if not 0 <= self.conversion_rate <= 1:
            raise ValueError("conversion_rate must be between 0 and 1")
        
        # Validate engagement_rate
        if not 0 <= self.engagement_rate <= 1:
            raise ValueError("engagement_rate must be between 0 and 1")
        
        # Validate sponsorship_fill_rate
        if not 0 <= self.sponsorship_fill_rate <= 1:
            raise ValueError("sponsorship_fill_rate must be between 0 and 1")
        
        # Validate refund_rate
        if not 0 <= self.refund_rate <= 1:
            raise ValueError("refund_rate must be between 0 and 1")
        
        # Validate tax_rate
        if not 0 <= self.tax_rate <= 1:
            raise ValueError("tax_rate must be between 0 and 1")
        
        # Validate discount_rate
        if not 0 <= self.discount_rate <= 1:
            raise ValueError("discount_rate must be between 0 and 1")
        
        # Validate max_steps
        if self.max_steps < 0:
            raise ValueError("max_steps must be non-negative")
        
        # Validate acquisition_channel_mix
        if not self._validate_channel_mix():
            raise ValueError("acquisition_channel_mix must sum to 1.0")
    
    def _validate_channel_mix(self) -> bool:
        """Validate that acquisition channel mix sums to 1.0."""
        total = sum(self.acquisition_channel_mix.values())
        return abs(total - 1.0) < 0.01
    
    def get_effective_churn_rate(self, engagement_score: float) -> float:
        """Calculate effective churn rate based on engagement score.
        
        Args:
            engagement_score: Engagement score between 0 and 1
            
        Returns:
            Effective churn rate adjusted for engagement
        """
        # Higher engagement reduces churn
        engagement_factor = 1.0 - (engagement_score * 0.5)
        return self.churn_rate * engagement_factor
    
    def get_effective_growth_rate(self, engagement_score: float) -> float:
        """Calculate effective growth rate based on engagement score.
        
        Args:
            engagement_score: Engagement score between 0 and 1
            
        Returns:
            Effective growth rate adjusted for engagement
        """
        # Higher engagement increases growth through referrals
        engagement_factor = 1.0 + (engagement_score * 0.2)
        return self.growth_rate * engagement_factor
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            "subscriber_count": self.subscriber_count,
            "retention_rate": self.retention_rate,
            "growth_rate": self.growth_rate,
            "churn_rate": self.churn_rate,
            "engagement_rate": self.engagement_rate,
            "arpu": self.arpu,
            "ad_rate": self.ad_rate,
            "sponsor_rate": self.sponsor_rate,
            "sponsorship_fill_rate": self.sponsorship_fill_rate,
            "content_cost": self.content_cost,
            "operational_cost": self.operational_cost,
            "cpc": self.cpc,
            "seasonal_factor": self.seasonal_factor,
            "competitor_count": self.competitor_count,
            "market_saturation": self.market_saturation,
            "conversion_rate": self.conversion_rate,
            "refund_rate": self.refund_rate,
            "tax_rate": self.tax_rate,
            "discount_rate": self.discount_rate,
            "max_steps": self.max_steps,
            "acquisition_channel_mix": self.acquisition_channel_mix
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SimConfig":
        """Create configuration from dictionary."""
        return cls(**data)
    
    def to_json(self) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SimConfig":
        """Create configuration from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
