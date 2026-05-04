"""Newsletter profit simulation state."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class NewsletterState:
    """Represents the state of the newsletter simulation at a given month.

    Attributes:
        month: Current month number (0-indexed)
        subscribers: Current number of subscribers
        revenue: Current monthly revenue
        costs: Current monthly costs
        profit: Current monthly profit
        cumulative_profit: Total profit accumulated so far
        is_terminated: Whether the simulation has terminated
        termination_reason: Reason for termination (if any)
    """

    month: int = 0
    subscribers: int = 0
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    cumulative_profit: float = 0.0
    is_terminated: bool = False
    termination_reason: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert state to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> NewsletterState:
        """Create state from dictionary."""
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def __repr__(self) -> str:
        """String representation of the state."""
        return (
            f"NewsletterState(month={self.month}, subscribers={self.subscribers}, "
            f"revenue=${self.revenue:.2f}, profit=${self.profit:.2f}, "
            f"cumulative=${self.cumulative_profit:.2f})"
        )
