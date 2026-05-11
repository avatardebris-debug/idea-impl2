"""Dashboard ticker that extends Ticker with dashboard-specific metrics."""

import time
from src.ticker import Ticker
from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


class DashboardTicker(Ticker):
    """A ticker that tracks dashboard-specific metrics."""

    def __init__(
        self,
        symbol: str = "",
        current_win_rate: float | WinRateMetric = 0.0,
        bankroll_history: float | BankrollCurvePoint = 0.0,
        nash_distance: float | NashEquilibriumShift = 0.0,
    ):
        super().__init__(symbol=symbol)
        # Accept floats and convert to objects
        if isinstance(current_win_rate, (int, float)):
            self.current_win_rate = WinRateMetric(value=float(current_win_rate))
        else:
            self.current_win_rate = current_win_rate or WinRateMetric()
        if isinstance(bankroll_history, (int, float)):
            self.bankroll_history = BankrollCurvePoint(bankroll=float(bankroll_history))
        else:
            self.bankroll_history = bankroll_history or BankrollCurvePoint()
        if isinstance(nash_distance, (int, float)):
            self.nash_distance = NashEquilibriumShift(distance=float(nash_distance))
        else:
            self.nash_distance = nash_distance or NashEquilibriumShift()

    @property
    def price_color(self) -> str:
        """Return color based on win rate."""
        if self.current_win_rate.value > 0.5:
            return "green"
        elif self.current_win_rate.value < 0.5:
            return "red"
        else:
            return "white"

    def update_from_state(self, state: DashboardState) -> None:
        """Update ticker from a DashboardState."""
        self.current_win_rate = state.win_rate
        self.bankroll_history = state.bankroll
        self.nash_distance = state.nash_distance
        self.price = state.win_rate.value
        self.timestamp = state.timestamp

    def update_price(self, new_price: float) -> None:
        """Update the price and record the previous price."""
        self.previous_price = self.price
        self.price = new_price
        self.timestamp = time.time()

    @property
    def price_change(self) -> float:
        """Return the absolute price change."""
        return self.price - self.previous_price

    @property
    def price_change_percent(self) -> float:
        """Return the price change as a percentage.

        Returns 0.0 when the previous price is zero to avoid division by zero.
        """
        if self.previous_price == 0:
            return 0.0
        return (self.price - self.previous_price) / self.previous_price * 100

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "timestamp": self.timestamp,
            "previous_price": self.previous_price,
            "current_win_rate": self.current_win_rate.to_dict(),
            "bankroll_history": self.bankroll_history.to_dict(),
            "nash_distance": self.nash_distance.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DashboardTicker":
        """Deserialize from dictionary."""
        dt = cls(symbol=data.get("symbol", ""))
        dt.price = data.get("price", 0.0)
        dt.timestamp = data.get("timestamp", time.time())
        dt.previous_price = data.get("previous_price", 0.0)
        dt.current_win_rate = WinRateMetric.from_dict(data.get("current_win_rate", {}))
        dt.bankroll_history = BankrollCurvePoint.from_dict(data.get("bankroll_history", {}))
        dt.nash_distance = NashEquilibriumShift.from_dict(data.get("nash_distance", {}))
        return dt
