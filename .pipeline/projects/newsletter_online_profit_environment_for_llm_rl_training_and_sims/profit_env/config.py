"""Configuration for the newsletter profit simulator."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SimConfig:
    """Configuration for the newsletter profit simulator.

    Attributes:
        initial_subscribers: Starting number of subscribers
        initial_revenue: Starting monthly revenue
        growth_rate: Monthly subscriber growth rate
        churn_rate: Monthly subscriber churn rate
        revenue_per_subscriber: Revenue per subscriber per month
        content_cost: Monthly content cost
        marketing_cost: Monthly marketing cost
        platform_fee: Platform fee percentage
        max_months: Maximum simulation months
        seed: Random seed for reproducibility
    """

    initial_subscribers: int = 1000
    initial_revenue: float = 5000.0
    growth_rate: float = 0.05
    churn_rate: float = 0.02
    revenue_per_subscriber: float = 5.0
    content_cost: float = 1000.0
    marketing_cost: float = 500.0
    platform_fee: float = 0.05
    max_months: int = 12
    seed: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> SimConfig:
        """Create configuration from dictionary, ignoring extra fields."""
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def __repr__(self) -> str:
        """String representation of the configuration."""
        return (
            f"SimConfig(initial_subscribers={self.initial_subscribers}, "
            f"growth_rate={self.growth_rate}, churn_rate={self.churn_rate}, "
            f"max_months={self.max_months})"
        )
