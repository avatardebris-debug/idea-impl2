"""Salary cap and financial constraints engine."""

from __future__ import annotations

from typing import Optional

from ffo.models.player import Player


class SalaryCapError(Exception):
    """Raised when a salary cap violation occurs."""

    def __init__(self, message: str, remaining: float = 0.0):
        self.remaining = remaining
        super().__init__(message)


class SalaryCap:
    """Tracks total payroll and enforces salary cap limits.

    Attributes:
        cap_limit: Maximum allowed total salary.
        current_usage: Current total salary of rostered players.
    """

    def __init__(self, cap_limit: float):
        if cap_limit < 0:
            raise ValueError("cap_limit must be non-negative")
        self.cap_limit = cap_limit
        self.current_usage: float = 0.0
        self._roster: list[Player] = []

    @property
    def remaining(self) -> float:
        """Return remaining budget under the cap."""
        return self.cap_limit - self.current_usage

    @property
    def utilization(self) -> float:
        """Return cap utilization as a fraction (0.0 to 1.0+)."""
        if self.cap_limit <= 0:
            return 0.0
        return self.current_usage / self.cap_limit

    def add_player(self, player: Player) -> None:
        """Add a player to the roster. Raises SalaryCapError if over cap."""
        if self.current_usage + player.salary > self.cap_limit:
            raise SalaryCapError(
                f"Cannot add {player.name} (salary={player.salary}): "
                f"would exceed cap. Remaining budget={self.remaining:.2f}",
                remaining=self.remaining,
            )
        self._roster.append(player)
        self.current_usage += player.salary

    def remove_player(self, player: Player) -> None:
        """Remove a player from the roster and reduce payroll."""
        if player not in self._roster:
            raise SalaryCapError(f"Player {player.name} not found in roster")
        self._roster.remove(player)
        self.current_usage -= player.salary

    def get_roster(self) -> list[Player]:
        """Return a copy of the current roster."""
        return list(self._roster)

    def can_afford(self, player: Player) -> bool:
        """Check if the cap can afford a player."""
        return self.current_usage + player.salary <= self.cap_limit

    def reset(self) -> None:
        """Clear the roster and reset payroll to zero."""
        self._roster.clear()
        self.current_usage = 0.0

    def __str__(self) -> str:
        return (
            f"SalaryCap(cap_limit={self.cap_limit:.2f}, "
            f"payroll={self.current_usage:.2f}, "
            f"remaining={self.remaining:.2f})"
        )

    def __repr__(self) -> str:
        return (
            f"SalaryCap(cap_limit={self.cap_limit}, "
            f"current_usage={self.current_usage}, "
            f"remaining={self.remaining})"
        )
