"""State module for the Newsletter Online Profit Environment."""

import json
from dataclasses import dataclass, field


@dataclass
class NewsletterState:
    """State of the newsletter simulation at a given week."""
    
    # Core metrics
    week: int = 0
    subscribers: int = 1000
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    
    # Cumulative metrics
    cumulative_profit: float = 0.0
    
    # Subscriber dynamics
    churned: int = 0
    acquired: int = 0
    
    # Engagement
    engagement_score: float = 0.75
    
    # Revenue breakdown
    sponsor_revenue: float = 0.0
    ad_revenue: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert state to a dictionary."""
        return {
            "week": self.week,
            "subscribers": self.subscribers,
            "revenue": self.revenue,
            "costs": self.costs,
            "profit": self.profit,
            "cumulative_profit": self.cumulative_profit,
            "churned": self.churned,
            "acquired": self.acquired,
            "engagement_score": self.engagement_score,
            "sponsor_revenue": self.sponsor_revenue,
            "ad_revenue": self.ad_revenue,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "NewsletterState":
        """Create a state from a dictionary."""
        return cls(
            week=data.get("week", 0),
            subscribers=data.get("subscribers", 1000),
            revenue=data.get("revenue", 0.0),
            costs=data.get("costs", 0.0),
            profit=data.get("profit", 0.0),
            cumulative_profit=data.get("cumulative_profit", 0.0),
            churned=data.get("churned", 0),
            acquired=data.get("acquired", 0),
            engagement_score=data.get("engagement_score", 0.75),
            sponsor_revenue=data.get("sponsor_revenue", 0.0),
            ad_revenue=data.get("ad_revenue", 0.0),
        )
    
    def to_json(self) -> str:
        """Convert state to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "NewsletterState":
        """Create a state from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def reset(self):
        """Reset state to initial values."""
        self.week = 0
        self.subscribers = 1000
        self.revenue = 0.0
        self.costs = 0.0
        self.profit = 0.0
        self.cumulative_profit = 0.0
        self.churned = 0
        self.acquired = 0
        self.engagement_score = 0.75
        self.sponsor_revenue = 0.0
        self.ad_revenue = 0.0
    
    def __post_init__(self):
        """Validate state values."""
        if self.week < 0:
            raise ValueError("week must be non-negative")
        if self.subscribers < 0:
            raise ValueError("subscribers must be non-negative")
        if not (0 <= self.engagement_score <= 1):
            raise ValueError("engagement_score must be between 0 and 1")
