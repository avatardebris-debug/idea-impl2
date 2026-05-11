"""Dashboard data models."""

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WinRateMetric:
    """Tracks win rate statistics."""
    value: float = 0.0
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WinRateMetric":
        return cls(
            value=data.get("value", 0.0),
            total_games=data.get("total_games", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class BankrollCurvePoint:
    """Tracks bankroll curve data point."""
    step: int = 0
    bankroll: float = 0.0
    peak_bankroll: float = 0.0
    drawdown: float = 0.0
    history: List[float] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "bankroll": self.bankroll,
            "peak_bankroll": self.peak_bankroll,
            "drawdown": self.drawdown,
            "history": self.history,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BankrollCurvePoint":
        return cls(
            step=data.get("step", 0),
            bankroll=data.get("bankroll", 0.0),
            peak_bankroll=data.get("peak_bankroll", 0.0),
            drawdown=data.get("drawdown", 0.0),
            history=data.get("history", []),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class NashEquilibriumShift:
    """Tracks distance from Nash equilibrium."""
    distance: float = 0.0
    current_strategy: str = "unknown"
    nash_strategy: str = "nash_equilibrium"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "distance": self.distance,
            "current_strategy": self.current_strategy,
            "nash_strategy": self.nash_strategy,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NashEquilibriumShift":
        return cls(
            distance=data.get("distance", 0.0),
            current_strategy=data.get("current_strategy", "unknown"),
            nash_strategy=data.get("nash_strategy", "nash_equilibrium"),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class DashboardState:
    """Complete dashboard state."""
    win_rate: WinRateMetric = field(default_factory=WinRateMetric)
    bankroll: BankrollCurvePoint = field(default_factory=BankrollCurvePoint)
    nash_distance: NashEquilibriumShift = field(default_factory=NashEquilibriumShift)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "win_rate": self.win_rate.to_dict(),
            "bankroll": self.bankroll.to_dict(),
            "nash_distance": self.nash_distance.to_dict(),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DashboardState":
        return cls(
            win_rate=WinRateMetric.from_dict(data.get("win_rate", {})),
            bankroll=BankrollCurvePoint.from_dict(data.get("bankroll", {})),
            nash_distance=NashEquilibriumShift.from_dict(data.get("nash_distance", {})),
            timestamp=data.get("timestamp", time.time()),
        )
