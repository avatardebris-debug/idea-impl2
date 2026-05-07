"""Dashboard data model classes for card game simulation metrics.

Defines the four core metric dataclasses:
  - WinRateMetric
  - BankrollCurvePoint
  - NashEquilibriumShift
  - DashboardState (aggregates all three)

Each class provides to_dict() / from_dict() serialization.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# WinRateMetric
# ---------------------------------------------------------------------------

@dataclass
class WinRateMetric:
    """Represents the current win rate for a card game simulation.

    Attributes:
        value: Win rate as a fraction between 0.0 and 1.0.
        total_games: Total number of games played.
        wins: Number of games won.
        losses: Number of games lost.
        timestamp: Unix timestamp of the measurement.
    """

    value: float = 0.0
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "value": self.value,
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WinRateMetric":
        """Deserialize from a plain dict."""
        return cls(
            value=float(data["value"]),
            total_games=int(data["total_games"]),
            wins=int(data["wins"]),
            losses=int(data["losses"]),
            timestamp=float(data.get("timestamp", time.time())),
        )


# ---------------------------------------------------------------------------
# BankrollCurvePoint
# ---------------------------------------------------------------------------

@dataclass
class BankrollCurvePoint:
    """A single point on the bankroll (equity) curve.

    Attributes:
        step: Simulation step / round number.
        bankroll: Current bankroll value.
        peak_bankroll: Running peak bankroll up to this step.
        drawdown: Current drawdown from peak (negative value).
        timestamp: Unix timestamp of the measurement.
    """

    step: int = 0
    bankroll: float = 0.0
    peak_bankroll: float = 0.0
    drawdown: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "step": self.step,
            "bankroll": self.bankroll,
            "peak_bankroll": self.peak_bankroll,
            "drawdown": self.drawdown,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BankrollCurvePoint":
        """Deserialize from a plain dict."""
        return cls(
            step=int(data["step"]),
            bankroll=float(data["bankroll"]),
            peak_bankroll=float(data["peak_bankroll"]),
            drawdown=float(data["drawdown"]),
            timestamp=float(data.get("timestamp", time.time())),
        )


# ---------------------------------------------------------------------------
# NashEquilibriumShift
# ---------------------------------------------------------------------------

@dataclass
class NashEquilibriumShift:
    """Represents the distance from the Nash equilibrium strategy.

    Attributes:
        distance: L2 distance from the Nash equilibrium strategy profile.
        current_strategy: Name or identifier of the current strategy.
        nash_strategy: Name or identifier of the Nash equilibrium strategy.
        timestamp: Unix timestamp of the measurement.
    """

    distance: float = 0.0
    current_strategy: str = "unknown"
    nash_strategy: str = "nash_equilibrium"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "distance": self.distance,
            "current_strategy": self.current_strategy,
            "nash_strategy": self.nash_strategy,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NashEquilibriumShift":
        """Deserialize from a plain dict."""
        return cls(
            distance=float(data["distance"]),
            current_strategy=str(data.get("current_strategy", "unknown")),
            nash_strategy=str(data.get("nash_strategy", "nash_equilibrium")),
            timestamp=float(data.get("timestamp", time.time())),
        )


# ---------------------------------------------------------------------------
# DashboardState
# ---------------------------------------------------------------------------

@dataclass
class DashboardState:
    """Aggregates all three metric types for a single dashboard snapshot.

    Attributes:
        win_rate: Current win rate metric.
        bankroll: Current bankroll curve point.
        nash_shift: Current Nash equilibrium shift.
        timestamp: Unix timestamp of the snapshot.
    """

    win_rate: WinRateMetric = field(default_factory=WinRateMetric)
    bankroll: BankrollCurvePoint = field(default_factory=BankrollCurvePoint)
    nash_shift: NashEquilibriumShift = field(default_factory=NashEquilibriumShift)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "win_rate": self.win_rate.to_dict(),
            "bankroll": self.bankroll.to_dict(),
            "nash_shift": self.nash_shift.to_dict(),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardState":
        """Deserialize from a plain dict."""
        return cls(
            win_rate=WinRateMetric.from_dict(data["win_rate"]),
            bankroll=BankrollCurvePoint.from_dict(data["bankroll"]),
            nash_shift=NashEquilibriumShift.from_dict(data["nash_shift"]),
            timestamp=float(data.get("timestamp", time.time())),
        )
