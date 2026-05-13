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
        current_payroll: Current total salary of rostered players.
    """

    def __init__(self, cap_limit: float):
        if cap_limit <= 0:
            raise ValueError("cap_limit must be positive")
        self.cap_limit = cap_limit
        self.current_payroll: float = 0.0
        self._roster: list[Player] = []

    @property
    def remaining_budget(self) -> float:
        """Return remaining budget under the cap."""
        return self.cap_limit - self.current_payroll

    @property
    def utilization(self) -> float:
        """Return cap utilization as a fraction (0.0 to 1.0+)."""
        if self.cap_limit <= 0:
            return 0.0
        return self.current_payroll / self.cap_limit

    def add_player(self, player: Player) -> None:
        """Add a player to the roster. Raises SalaryCapError if over cap."""
        if player.salary <= 0:
            raise ValueError(f"Player {player.name} has invalid salary: {player.salary}")
        if self.current_payroll + player.salary > self.cap_limit:
            raise SalaryCapError(
                f"Cannot add {player.name} (salary={player.salary}): "
                f"would exceed cap. Remaining budget={self.remaining_budget:.2f}",
                remaining=self.remaining_budget,
            )
        self._roster.append(player)
        self.current_payroll += player.salary

    def remove_player(self, player: Player) -> None:
        """Remove a player from the roster and reduce payroll."""
        if player not in self._roster:
            raise ValueError(f"Player {player.name} is not in the roster")
        self._roster.remove(player)
        self.current_payroll -= player.salary

    def get_roster(self) -> list[Player]:
        """Return a copy of the current roster."""
        return list(self._roster)

    def can_afford(self, player: Player) -> bool:
        """Check if the cap can afford a player without exceeding the limit."""
        return self.current_payroll + player.salary <= self.cap_limit

    def __repr__(self) -> str:
        return (
            f"SalaryCap(cap_limit={self.cap_limit:.2f}, "
            f"payroll={self.current_payroll:.2f}, "
            f"remaining={self.remaining_budget:.2f})"
        )
