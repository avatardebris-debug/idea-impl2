"""State module for the Newsletter Online Profit Environment."""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NewsletterState:
    """State representation for newsletter simulation.
    
    This class tracks the current state of the newsletter business
    including subscribers, revenue, costs, and engagement metrics.
    """
    
    # Time tracking
    week: int = 0
    
    # Core metrics
    subscribers: int = 1000
    revenue: float = 0.0
    costs: float = 0.0
    
    # Computed properties
    profit: float = 0.0
    cumulative_profit: float = 0.0
    
    # Subscriber dynamics
    churned: int = 0
    acquired: int = 0
    
    # Engagement and quality
    engagement_score: float = 0.75
    
    # Revenue breakdown
    sponsor_revenue: float = 0.0
    ad_revenue: float = 0.0
    
    # Rates and parameters
    churn_rate: float = 0.05
    growth_rate: float = 0.1
    arpu: float = 5.00
    
    # Additional computed fields (can be set explicitly)
    total_revenue: float = 0.0
    net_profit: float = 0.0
    
    def __post_init__(self):
        """Validate state values after initialization."""
        if self.week < 0:
            raise ValueError("week must be non-negative")
        if self.subscribers < 0:
            raise ValueError("subscribers must be non-negative")
        if not 0 <= self.engagement_score <= 1:
            raise ValueError("engagement_score must be between 0 and 1")
        
        # Compute profit from revenue and costs if not explicitly set
        if self.profit == 0.0:
            self.profit = self.revenue - self.costs
        
        # Compute total_revenue if not explicitly set
        if self.total_revenue == 0.0:
            self.total_revenue = self.revenue + self.sponsor_revenue + self.ad_revenue
        
        # Compute net_profit if not explicitly set
        if self.net_profit == 0.0:
            self.net_profit = self.total_revenue - self.costs
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary.
        
        Returns:
            Dictionary representation of state
        """
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
            "churn_rate": self.churn_rate,
            "growth_rate": self.growth_rate,
            "arpu": self.arpu,
            "total_revenue": self.total_revenue,
            "net_profit": self.net_profit
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NewsletterState":
        """Create state from dictionary.
        
        Args:
            data: Dictionary containing state data
            
        Returns:
            NewsletterState object
        """
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
            churn_rate=data.get("churn_rate", 0.05),
            growth_rate=data.get("growth_rate", 0.1),
            arpu=data.get("arpu", 5.00),
            total_revenue=data.get("total_revenue", 0.0),
            net_profit=data.get("net_profit", 0.0)
        )
    
    def to_json(self) -> str:
        """Convert state to JSON string.
        
        Returns:
            JSON string representation of state
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "NewsletterState":
        """Create state from JSON string.
        
        Args:
            json_str: JSON string containing state data
            
        Returns:
            NewsletterState object
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class SimulationRecord:
    """Record of a single simulation step.
    
    This class captures all relevant metrics for a single week of simulation.
    """
    
    # Time
    week: int = 0
    
    # Core metrics
    subscribers: int = 1000
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    
    # Cumulative metrics
    cumulative_profit: float = 0.0
    
    # Subscriber dynamics
    churned: int = 0
    acquired: int = 0
    
    # Engagement and quality
    engagement: float = 0.75
    
    # Revenue breakdown
    sponsor_revenue: float = 0.0
    ad_revenue: float = 0.0
    
    # Rates and parameters
    churn_rate: float = 0.05
    growth_rate: float = 0.1
    arpu: float = 5.00
    
    def to_dict(self) -> Dict:
        """Convert record to dictionary.
        
        Returns:
            Dictionary representation of record
        """
        return {
            "week": self.week,
            "subscribers": self.subscribers,
            "revenue": self.revenue,
            "costs": self.costs,
            "profit": self.profit,
            "cumulative_profit": self.cumulative_profit,
            "churned": self.churned,
            "acquired": self.acquired,
            "engagement": self.engagement,
            "sponsor_revenue": self.sponsor_revenue,
            "ad_revenue": self.ad_revenue,
            "churn_rate": self.churn_rate,
            "growth_rate": self.growth_rate,
            "arpu": self.arpu
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SimulationRecord":
        """Create record from dictionary.
        
        Args:
            data: Dictionary containing record data
            
        Returns:
            SimulationRecord object
        """
        return cls(
            week=data.get("week", 0),
            subscribers=data.get("subscribers", 1000),
            revenue=data.get("revenue", 0.0),
            costs=data.get("costs", 0.0),
            profit=data.get("profit", 0.0),
            cumulative_profit=data.get("cumulative_profit", 0.0),
            churned=data.get("churned", 0),
            acquired=data.get("acquired", 0),
            engagement=data.get("engagement", 0.75),
            sponsor_revenue=data.get("sponsor_revenue", 0.0),
            ad_revenue=data.get("ad_revenue", 0.0),
            churn_rate=data.get("churn_rate", 0.05),
            growth_rate=data.get("growth_rate", 0.1),
            arpu=data.get("arpu", 5.00)
        )
    
    def __len__(self) -> int:
        """Return the number of features in the record."""
        return len(self.to_dict())
    
    def __iter__(self):
        """Iterate over record values."""
        return iter(self.to_dict().values())
    
    def __getitem__(self, key) -> float:
        """Get record value by key."""
        return self.to_dict()[key]


@dataclass
class Observation:
    """Observation space for the newsletter environment.
    
    This class represents the observation that the agent receives from the environment.
    All values are normalized to be between 0 and 1 for consistent RL training.
    """
    
    # Core metrics (normalized)
    subscribers: float = 0.0
    revenue: float = 0.0
    profit: float = 0.0
    
    # Engagement and quality
    engagement: float = 0.75
    
    # Time
    week: float = 0.0
    
    # Cumulative metrics
    cumulative_profit: float = 0.0
    
    # Rates
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


class SimulationHistory:
    """History of simulation records.
    
    This class maintains a history of all simulation records and provides
    methods for accessing and analyzing the data.
    """
    
    def __init__(self):
        """Initialize simulation history."""
        self._records: List[SimulationRecord] = []
    
    def add_weekly_data(self, record: SimulationRecord):
        """Add a record to the history.
        
        Args:
            record: SimulationRecord to add
        """
        self._records.append(record)
    
    def add_record(self, record: SimulationRecord):
        """Add a record to the history.
        
        Args:
            record: SimulationRecord to add
        """
        self._records.append(record)
    
    def get_weekly_data(self) -> List[Dict]:
        """Get all weekly data as dictionaries.
        
        Returns:
            List of dictionaries containing weekly data
        """
        return [record.to_dict() for record in self._records]
    
    def get_week(self, week: int) -> Optional[SimulationRecord]:
        """Get record for a specific week.
        
        Args:
            week: Week number to retrieve (0-indexed)
            
        Returns:
            SimulationRecord for the week, or None if not found
        """
        if 0 <= week < len(self._records):
            return self._records[week]
        return None
    
    def get_weeks(self, start_week: int, end_week: int) -> List[SimulationRecord]:
        """Get records for a range of weeks.
        
        Args:
            start_week: Starting week index (0-indexed, inclusive)
            end_week: Ending week index (0-indexed, inclusive)
            
        Returns:
            List of SimulationRecord for the specified weeks
        """
        return [self._records[i] for i in range(start_week, min(end_week + 1, len(self._records)))]
    
    def get_statistics(self) -> Dict:
        """Get aggregated statistics from history.
        
        Returns:
            Dictionary containing aggregated statistics
        """
        if not self._records:
            return {
                "total_revenue": 0.0,
                "total_costs": 0.0,
                "net_profit": 0.0,
                "avg_subscribers": 0.0,
                "final_subscribers": 0,
                "final_cumulative_profit": 0.0,
                "avg_churn_rate": 0.0,
                "total_acquired": 0
            }
        
        total_revenue = sum(r.revenue for r in self._records)
        total_costs = sum(r.costs for r in self._records)
        net_profit = sum(r.profit for r in self._records)
        avg_subscribers = sum(r.subscribers for r in self._records) / len(self._records)
        final_subscribers = self._records[-1].subscribers
        final_cumulative_profit = self._records[-1].cumulative_profit
        avg_churn_rate = sum(r.churn_rate for r in self._records) / len(self._records)
        total_acquired = sum(r.acquired for r in self._records)
        
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
    
    def __len__(self) -> int:
        """Return the number of records in history."""
        return len(self._records)
    
    def __getitem__(self, index: int) -> SimulationRecord:
        """Get record by index.
        
        Args:
            index: Index of record to retrieve
            
        Returns:
            SimulationRecord at the specified index
        """
        return self._records[index]
    
    def __iter__(self):
        """Iterate over records."""
        return iter(self._records)
    
    def clear(self):
        """Clear all records from history."""
        self._records.clear()
