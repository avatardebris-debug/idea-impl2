"""Ticker module for tracking price changes with color indicators."""

import time


class Ticker:
    """A ticker that tracks a symbol's price and color-coded changes."""

    def __init__(self, symbol: str = "", price: float = 0.0):
        self.symbol = symbol
        self.price = price
        self.previous_price = 0.0
        self._color = "white"
        self.timestamp = time.time()

    @property
    def price_color(self) -> str:
        """Return color based on price change direction."""
        if self.previous_price == 0.0:
            return "white"
        if self.price > self.previous_price:
            return "green"
        elif self.price < self.previous_price:
            return "red"
        else:
            return "white"

    def update(self, new_price: float) -> None:
        """Update the ticker with a new price."""
        self.previous_price = self.price
        self.price = new_price
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        """Serialize the ticker to a dictionary."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "previous_price": self.previous_price,
            "timestamp": self.timestamp,
            "price_color": self.price_color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ticker":
        """Deserialize a ticker from a dictionary."""
        t = cls(symbol=data.get("symbol", ""), price=data.get("price", 0.0))
        t.previous_price = data.get("previous_price", 0.0)
        t.timestamp = data.get("timestamp", time.time())
        return t
