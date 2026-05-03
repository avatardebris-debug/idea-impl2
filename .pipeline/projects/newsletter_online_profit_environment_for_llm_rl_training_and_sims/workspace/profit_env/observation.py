"""Observation module for the Newsletter Online Profit Environment."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Observation:
    """Observation representation for the newsletter environment.
    
    This class represents the observation space available to the agent,
    containing normalized state features that the agent can use to make decisions.
    """
    
    # Core metrics (normalized to [0, 1])
    subscribers: float = 0.0
    revenue: float = 0.0
    profit: float = 0.0
    
    # Engagement and quality
    engagement: float = 0.75
    
    # Time
    week: float = 0.0
    
    # Cumulative metrics
    cumulative_profit: float = 0.0
    
    # Rates and parameters
    churn_rate: float = 0.05
    growth_rate: float = 0.1
    
    # Revenue breakdown
    sponsor_revenue: float = 0.0
    ad_revenue: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert observation to dictionary.
        
        Returns:
            Dictionary representation of observation
        """
        return {
            "subscribers": self.subscribers,
            "revenue": self.revenue,
            "profit": self.profit,
            "engagement": self.engagement,
            "week": self.week,
            "cumulative_profit": self.cumulative_profit,
            "churn_rate": self.churn_rate,
            "growth_rate": self.growth_rate,
            "sponsor_revenue": self.sponsor_revenue,
            "ad_revenue": self.ad_revenue
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Observation":
        """Create observation from dictionary.
        
        Args:
            data: Dictionary containing observation data
            
        Returns:
            Observation object
        """
        return cls(
            subscribers=data.get("subscribers", 0.0),
            revenue=data.get("revenue", 0.0),
            profit=data.get("profit", 0.0),
            engagement=data.get("engagement", 0.75),
            week=data.get("week", 0.0),
            cumulative_profit=data.get("cumulative_profit", 0.0),
            churn_rate=data.get("churn_rate", 0.05),
            growth_rate=data.get("growth_rate", 0.1),
            sponsor_revenue=data.get("sponsor_revenue", 0.0),
            ad_revenue=data.get("ad_revenue", 0.0)
        )
    
    def __len__(self) -> int:
        """Return the number of features in the observation."""
        return len(self.to_dict())
    
    def __iter__(self):
        """Iterate over observation values."""
        return iter(self.to_dict().values())
    
    def __getitem__(self, key) -> float:
        """Get observation value by key."""
        return self.to_dict()[key]
