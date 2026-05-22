"""Player data models for FFO."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Player:
    """Represents a player with financial and performance attributes.

    Attributes:
        name: Player name.
        position: Position code (e.g. 'GK', 'DEF', 'MID', 'FWD').
        overall_rating: Overall skill rating (0-100).
        age: Player age in years.
        contract_length: Remaining contract length in years.
        salary: Annual salary in dollars.
        value: Current market value in dollars.
    """

    name: str
    position: str
    overall_rating: float
    age: int
    contract_length: int
    salary: float
    value: float

    def to_dict(self) -> dict:
        """Serialize player to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Player:
        """Deserialize player from a dictionary."""
        return cls(**data)

    @property
    def value_per_salary(self) -> float:
        """Return value-to-salary ratio."""
        if self.salary <= 0:
            return float("inf")
        return self.value / self.salary

    @property
    def value_per_dollar(self) -> float:
        """Return value per dollar of salary (alias for value_per_salary)."""
        return self.value_per_salary

    def __lt__(self, other: Player) -> bool:
        """Compare players by value_per_salary (descending)."""
        return self.value_per_salary > other.value_per_salary

    def __le__(self, other: Player) -> bool:
        return self.value_per_salary >= other.value_per_salary

    def __gt__(self, other: Player) -> bool:
        return self.value_per_salary < other.value_per_salary

    def __ge__(self, other: Player) -> bool:
        return self.value_per_salary <= other.value_per_salary

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Player):
            return NotImplemented
        return self.name == other.name and self.salary == other.salary

    def __repr__(self) -> str:
        return (
            f"Player(name={self.name!r}, position={self.position!r}, "
            f"rating={self.overall_rating}, salary={self.salary}, "
            f"value={self.value})"
        )


@dataclass
class FreeAgent(Player):
    """Represents an available free agent player.

    Inherits all Player attributes and adds availability tracking.
    """

    available: bool = True
    agent_name: Optional[str] = None
    preferred_positions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize free agent to a dictionary."""
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> FreeAgent:
        """Deserialize free agent from a dictionary."""
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"FreeAgent(name={self.name!r}, position={self.position!r}, "
            f"rating={self.overall_rating}, salary={self.salary}, "
            f"value={self.value}, available={self.available})"
        )
