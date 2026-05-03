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
    ad_rate: float = 0.50
    sponsor_rate: float = 100.00
    sponsorship_fill_rate: float = 0.8
    
    # Cost parameters
    content_cost: float = 500.00
    operational_cost: float = 300.00
    cpc: float = 2.50
    
    # Market parameters
    seasonal_factor: float = 1.0
    competitor_count: int = 5
    market_saturation: float = 0.3
    conversion_rate: float = 0.02
    
    # Additional parameters
    refund_rate: float = 0.01
    tax_rate: float = 0.25
    discount_rate: float = 0.1
    
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
        # At engagement 0, churn is reduced by 50%
        # At engagement 1, churn is unchanged
        engagement_factor = 1 - (engagement_score * 0.5)
        return self.churn_rate * engagement_factor
    
    def get_effective_growth_rate(self, engagement_score: float) -> float:
        """Calculate effective growth rate based on engagement score.
        
        Args:
            engagement_score: Engagement score between 0 and 1
            
        Returns:
            Effective growth rate adjusted for engagement
        """
        # Higher engagement increases growth
        # At engagement 0, growth is unchanged
        # At engagement 1, growth increases by 20%
        engagement_factor = 1 + (engagement_score * 0.2)
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
            "acquisition_channel_mix": self.acquisition_channel_mix
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SimConfig":
        """Create configuration from dictionary."""
        return cls(
            subscriber_count=data.get("subscriber_count", 1000),
            retention_rate=data.get("retention_rate", 0.95),
            growth_rate=data.get("growth_rate", 0.1),
            churn_rate=data.get("churn_rate", 0.05),
            engagement_rate=data.get("engagement_rate", 0.75),
            arpu=data.get("arpu", 5.00),
            ad_rate=data.get("ad_rate", 0.50),
            sponsor_rate=data.get("sponsor_rate", 100.00),
            sponsorship_fill_rate=data.get("sponsorship_fill_rate", 0.8),
            content_cost=data.get("content_cost", 500.00),
            operational_cost=data.get("operational_cost", 300.00),
            cpc=data.get("cpc", 2.50),
            seasonal_factor=data.get("seasonal_factor", 1.0),
            competitor_count=data.get("competitor_count", 5),
            market_saturation=data.get("market_saturation", 0.3),
            conversion_rate=data.get("conversion_rate", 0.02),
            refund_rate=data.get("refund_rate", 0.01),
            tax_rate=data.get("tax_rate", 0.25),
            discount_rate=data.get("discount_rate", 0.1),
            acquisition_channel_mix=data.get("acquisition_channel_mix", {
                "organic": 0.4,
                "paid": 0.3,
                "referral": 0.2,
                "social": 0.1
            })
        )
    
    def to_json(self) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "SimConfig":
        """Create configuration from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class NewsletterState:
    """State representation for a newsletter simulation week.
    
    This class tracks the state of the newsletter at the end of each week,
    including subscriber counts, revenue, costs, and engagement metrics.
    """
    
    # Week tracking
    week: int = 0
    
    # Subscriber metrics
    subscribers: int = 1000
    churned: int = 0
    acquired: int = 0
    
    # Financial metrics
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    cumulative_profit: float = 0.0
    
    # Revenue breakdown
    sponsor_revenue: float = 0.0
    ad_revenue: float = 0.0
    
    # Engagement metrics
    engagement_score: float = 0.75
    
    def __post_init__(self):
        """Validate state values after initialization."""
        # Validate week
        if self.week < 0:
            raise ValueError("week must be non-negative")
        
        # Validate subscribers
        if self.subscribers < 0:
            raise ValueError("subscribers must be non-negative")
        
        # Validate churned
        if self.churned < 0:
            raise ValueError("churned must be non-negative")
        
        # Validate acquired
        if self.acquired < 0:
            raise ValueError("acquired must be non-negative")
        
        # Validate engagement_score
        if not 0 <= self.engagement_score <= 1:
            raise ValueError("engagement_score must be between 0 and 1")
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary."""
        return {
            "week": self.week,
            "subscribers": self.subscribers,
            "churned": self.churned,
            "acquired": self.acquired,
            "revenue": self.revenue,
            "costs": self.costs,
            "profit": self.profit,
            "cumulative_profit": self.cumulative_profit,
            "sponsor_revenue": self.sponsor_revenue,
            "ad_revenue": self.ad_revenue,
            "engagement_score": self.engagement_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NewsletterState":
        """Create state from dictionary."""
        return cls(
            week=data.get("week", 0),
            subscribers=data.get("subscribers", 1000),
            churned=data.get("churned", 0),
            acquired=data.get("acquired", 0),
            revenue=data.get("revenue", 0.0),
            costs=data.get("costs", 0.0),
            profit=data.get("profit", 0.0),
            cumulative_profit=data.get("cumulative_profit", 0.0),
            sponsor_revenue=data.get("sponsor_revenue", 0.0),
            ad_revenue=data.get("ad_revenue", 0.0),
            engagement_score=data.get("engagement_score", 0.75)
        )
    
    def to_json(self) -> str:
        """Convert state to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "NewsletterState":
        """Create state from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def reset(self):
        """Reset state to initial values."""
        self.week = 0
        self.subscribers = 1000
        self.churned = 0
        self.acquired = 0
        self.revenue = 0.0
        self.costs = 0.0
        self.profit = 0.0
        self.cumulative_profit = 0.0
        self.sponsor_revenue = 0.0
        self.ad_revenue = 0.0
        self.engagement_score = 0.75


@dataclass
class SimulationHistory:
    """History of a newsletter simulation run.
    
    This class stores the complete history of a simulation run,
    including weekly data and aggregate statistics.
    """
    
    # Simulation parameters
    weeks: int = 52
    initial_subscribers: int = 1000
    
    # Aggregate statistics
    final_subscribers: int = 1000
    total_revenue: float = 0.0
    total_costs: float = 0.0
    net_profit: float = 0.0
    avg_subscribers: float = 0.0
    avg_churn_rate: float = 0.0
    total_acquired: int = 0
    final_cumulative_profit: float = 0.0
    
    # Weekly data
    weekly_data: list = field(default_factory=list)
    
    def add_weekly_data(self, state: NewsletterState):
        """Add weekly state data to history."""
        self.weekly_data.append(state)
    
    def get_statistics(self) -> Dict:
        """Calculate and return aggregate statistics."""
        if not self.weekly_data:
            return {
                "total_revenue": 0.0,
                "total_costs": 0.0,
                "net_profit": 0.0,
                "avg_subscribers": 0.0,
                "final_subscribers": self.initial_subscribers,
                "final_cumulative_profit": 0.0,
                "avg_churn_rate": 0.0,
                "total_acquired": 0
            }
        
        total_revenue = sum(s.revenue for s in self.weekly_data)
        total_costs = sum(s.costs for s in self.weekly_data)
        net_profit = total_revenue - total_costs
        avg_subscribers = sum(s.subscribers for s in self.weekly_data) / len(self.weekly_data)
        final_subscribers = self.weekly_data[-1].subscribers
        final_cumulative_profit = self.weekly_data[-1].cumulative_profit
        total_acquired = sum(s.acquired for s in self.weekly_data)
        
        # Calculate average churn rate
        total_churn_rate = 0.0
        for i in range(1, len(self.weekly_data)):
            prev_subscribers = self.weekly_data[i-1].subscribers
            churned = self.weekly_data[i].churned
            if prev_subscribers > 0:
                total_churn_rate += churned / prev_subscribers
        avg_churn_rate = total_churn_rate / len(self.weekly_data) if self.weekly_data else 0.0
        
        return {
            "total_revenue": total_revenue,
            "total_costs": total_costs,
            "net_profit": net_profit,
            "avg_subscribers": avg_subscribers,
            "final_subscribers": final_subscribers,
            "final_cumulative_profit": final_cumulative_profit,
            "avg_churn_rate": avg_churn_rate,
            "total_acquired": total_acquired
        }
    
    def get_weekly_data(self) -> list:
        """Get weekly data as a list."""
        return self.weekly_data
    
    def to_dict(self) -> Dict:
        """Convert history to dictionary."""
        return {
            "weeks": self.weeks,
            "initial_subscribers": self.initial_subscribers,
            "final_subscribers": self.final_subscribers,
            "total_revenue": self.total_revenue,
            "total_costs": self.total_costs,
            "net_profit": self.net_profit,
            "avg_subscribers": self.avg_subscribers,
            "avg_churn_rate": self.avg_churn_rate,
            "total_acquired": self.total_acquired,
            "final_cumulative_profit": self.final_cumulative_profit,
            "weekly_data": [s.to_dict() for s in self.weekly_data]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SimulationHistory":
        """Create history from dictionary."""
        history = cls(
            weeks=data.get("weeks", 52),
            initial_subscribers=data.get("initial_subscribers", 1000),
            final_subscribers=data.get("final_subscribers", 1000),
            total_revenue=data.get("total_revenue", 0.0),
            total_costs=data.get("total_costs", 0.0),
            net_profit=data.get("net_profit", 0.0),
            avg_subscribers=data.get("avg_subscribers", 0.0),
            avg_churn_rate=data.get("avg_churn_rate", 0.0),
            total_acquired=data.get("total_acquired", 0),
            final_cumulative_profit=data.get("final_cumulative_profit", 0.0)
        )
        
        for week_data in data.get("weekly_data", []):
            history.add_weekly_data(NewsletterState.from_dict(week_data))
        
        return history
    
    def to_json(self) -> str:
        """Convert history to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "SimulationHistory":
        """Create history from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
