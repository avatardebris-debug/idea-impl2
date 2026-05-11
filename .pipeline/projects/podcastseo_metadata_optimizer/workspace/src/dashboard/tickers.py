"""Dashboard ticker that carries live data."""

from src.dashboard.models import (
    WinRateMetric,
    BankrollCurvePoint,
    NashEquilibriumShift,
    DashboardState,
)


class DashboardTicker:
    """Carries live dashboard data."""

    def __init__(self, symbol: str = "", price: float = 0.0, timestamp: float = None,
                 current_win_rate: WinRateMetric = None,
                 bankroll_history: BankrollCurvePoint = None,
                 nash_distance: NashEquilibriumShift = None,
                 previous_price: float = 0.0):
        self.symbol = symbol
        self.price = price
        self.timestamp = timestamp if timestamp is not None else 0.0
        self.previous_price = previous_price
        self.current_win_rate = current_win_rate if current_win_rate is not None else WinRateMetric()
        self.bankroll_history = bankroll_history if bankroll_history is not None else BankrollCurvePoint()
        self.nash_distance = nash_distance if nash_distance is not None else NashEquilibriumShift()

    @property
    def price_color(self) -> str:
        if self.current_win_rate.value > 0.5:
            return "green"
        elif self.current_win_rate.value < 0.5:
            return "red"
        else:
            return "white"

    def update_from_state(self, state: DashboardState):
        """Update from a DashboardState."""
        self.current_win_rate = state.win_rate
        self.bankroll_history = state.bankroll
        self.nash_distance = state.nash_distance
        self.price = state.win_rate.value
        self.timestamp = state.timestamp

    def to_dict(self) -> dict:
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
        return cls(
            symbol=data["symbol"],
            price=data["price"],
            timestamp=data["timestamp"],
            previous_price=data["previous_price"],
            current_win_rate=WinRateMetric.from_dict(data["current_win_rate"]),
            bankroll_history=BankrollCurvePoint.from_dict(data["bankroll_history"]),
            nash_distance=NashEquilibriumShift.from_dict(data["nash_distance"]),
        )
