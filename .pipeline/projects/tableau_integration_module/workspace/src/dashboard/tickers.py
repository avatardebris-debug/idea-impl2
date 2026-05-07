"""DashboardTicker class extending src.ticker.Ticker.

Provides a ticker that carries all three dashboard metric types
and exposes price_color-style visual hints based on win rate sign.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict

from src.ticker import Ticker

from src.dashboard.models import (
    BankrollCurvePoint,
    DashboardState,
    NashEquilibriumShift,
    WinRateMetric,
)


@dataclass
class DashboardTicker(Ticker):
    """Ticker that carries card-game simulation metrics.

    Extends the base ``Ticker`` with three metric-specific fields:
      - current_win_rate:  WinRateMetric
      - bankroll_history:  BankrollCurvePoint
      - nash_distance:     NashEquilibriumShift

    The ``price_color`` property is overridden to return:
      - 'green'  when win rate > 0.5 (positive)
      - 'red'    when win rate < 0.5 (negative)
      - 'white'  when win rate == 0.5 (neutral)
    """

    current_win_rate: WinRateMetric = field(default_factory=WinRateMetric)
    bankroll_history: BankrollCurvePoint = field(default_factory=BankrollCurvePoint)
    nash_distance: NashEquilibriumShift = field(default_factory=NashEquilibriumShift)

    @property
    def price_color(self) -> str:
        """Return a color hint based on win rate relative to 0.5.

        - 'green'  if win rate > 0.5 (positive)
        - 'red'    if win rate < 0.5 (negative)
        - 'white'  if win rate == 0.5 (neutral)
        """
        wr = self.current_win_rate.value
        if wr > 0.5:
            return "green"
        elif wr < 0.5:
            return "red"
        return "white"

    def update_from_state(self, state: DashboardState) -> None:
        """Update all metric fields from a DashboardState snapshot."""
        self.current_win_rate = state.win_rate
        self.bankroll_history = state.bankroll
        self.nash_distance = state.nash_shift
        self.price = state.win_rate.value
        self.timestamp = state.timestamp
        # Update price/previous_price without overwriting timestamp
        self.previous_price = self.price
        self.price = self.price

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the full dashboard ticker to a plain dict."""
        base = super().to_dict()
        base.update({
            "current_win_rate": self.current_win_rate.to_dict(),
            "bankroll_history": self.bankroll_history.to_dict(),
            "nash_distance": self.nash_distance.to_dict(),
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardTicker":
        """Deserialize a DashboardTicker from a plain dict."""
        t = cls(
            symbol=data.get("symbol", "DASHBOARD"),
            price=float(data.get("price", 0.0)),
            timestamp=float(data.get("timestamp", time.time())),
            previous_price=float(data.get("previous_price", 0.0)),
        )
        if "current_win_rate" in data:
            t.current_win_rate = WinRateMetric.from_dict(data["current_win_rate"])
        if "bankroll_history" in data:
            t.bankroll_history = BankrollCurvePoint.from_dict(data["bankroll_history"])
        if "nash_distance" in data:
            t.nash_distance = NashEquilibriumShift.from_dict(data["nash_distance"])
        return t
