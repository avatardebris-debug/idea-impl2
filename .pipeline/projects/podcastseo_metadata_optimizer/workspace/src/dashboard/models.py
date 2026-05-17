"""Data models for the dashboard."""

import time


class WinRateMetric:
    """Win rate metric."""

    def __init__(self, value: float = 0.0, total_games: int = 0, wins: int = 0, losses: int = 0, timestamp: float = None):
        self.value = value
        self.total_games = total_games
        self.wins = wins
        self.losses = losses
        self.timestamp = timestamp if timestamp is not None else time.time()

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
            value=data["value"],
            total_games=data["total_games"],
            wins=data["wins"],
            losses=data["losses"],
            timestamp=data["timestamp"],
        )


class BankrollCurvePoint:
    """A single point on the bankroll curve."""

    def __init__(self, step: int = 0, bankroll: float = 0.0, peak_bankroll: float = 0.0, drawdown: float = 0.0, timestamp: float = None, history: list = None):
        self.step = step
        self.bankroll = bankroll
        self.peak_bankroll = peak_bankroll
        self.drawdown = drawdown
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.history = history if history is not None else []

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "bankroll": self.bankroll,
            "peak_bankroll": self.peak_bankroll,
            "drawdown": self.drawdown,
            "timestamp": self.timestamp,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BankrollCurvePoint":
        return cls(
            step=data["step"],
            bankroll=data["bankroll"],
            peak_bankroll=data["peak_bankroll"],
            drawdown=data["drawdown"],
            timestamp=data["timestamp"],
            history=data["history"],
        )


class NashEquilibriumShift:
    """Distance from Nash equilibrium."""

    def __init__(self, distance: float = 0.0, current_strategy: str = "unknown", nash_strategy: str = "nash_equilibrium", timestamp: float = None):
        self.distance = distance
        self.current_strategy = current_strategy
        self.nash_strategy = nash_strategy
        self.timestamp = timestamp if timestamp is not None else time.time()

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
            distance=data["distance"],
            current_strategy=data["current_strategy"],
            nash_strategy=data["nash_strategy"],
            timestamp=data["timestamp"],
        )


class DashboardState:
    """Complete dashboard state."""

    def __init__(self, win_rate: WinRateMetric = None, bankroll: BankrollCurvePoint = None, nash_distance: NashEquilibriumShift = None, timestamp: float = None):
        self.win_rate = win_rate if win_rate is not None else WinRateMetric()
        self.bankroll = bankroll if bankroll is not None else BankrollCurvePoint()
        self.nash_distance = nash_distance if nash_distance is not None else NashEquilibriumShift()
        self.timestamp = timestamp if timestamp is not None else time.time()

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
            win_rate=WinRateMetric.from_dict(data["win_rate"]),
            bankroll=BankrollCurvePoint.from_dict(data["bankroll"]),
            nash_distance=NashEquilibriumShift.from_dict(data["nash_distance"]),
            timestamp=data["timestamp"],
        )
