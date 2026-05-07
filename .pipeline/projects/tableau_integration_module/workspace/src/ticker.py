"""Base Ticker class for real-time metric streams.

Provides a lightweight ticker that holds a symbol, price, and timestamp,
and supports color-coded visual hints based on price direction.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Ticker:
    """Base ticker representing a real-time data point.

    Attributes:
        symbol: Identifier for the ticker (e.g., 'WIN_RATE', 'BANKROLL').
        price: Current numeric value.
        timestamp: Unix timestamp of the last update.
        previous_price: The price from the previous update.
        _color: Internal color hint derived from price direction.
    """

    symbol: str = ""
    price: float = 0.0
    timestamp: float = field(default_factory=time.time)
    previous_price: float = 0.0
    _color: str = "white"

    @property
    def price_color(self) -> str:
        """Return a color hint based on price direction.

        - 'green' if price increased from previous.
        - 'red' if price decreased from previous.
        - 'white' if price is unchanged or first update.
        """
        if self.previous_price == 0.0:
            return "white"
        if self.price > self.previous_price:
            return "green"
        elif self.price < self.previous_price:
            return "red"
        return "white"

    def update(self, price: float) -> None:
        """Update the ticker with a new price value."""
        self.previous_price = self.price
        self.price = price
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ticker to a plain dict."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "timestamp": self.timestamp,
            "previous_price": self.previous_price,
            "price_color": self.price_color,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticker":
        """Deserialize a Ticker from a plain dict."""
        t = cls(
            symbol=data.get("symbol", ""),
            price=float(data.get("price", 0.0)),
            timestamp=float(data.get("timestamp", time.time())),
            previous_price=float(data.get("previous_price", 0.0)),
        )
        return t
