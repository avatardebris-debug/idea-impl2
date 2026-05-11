"""Base Ticker class for price tracking."""

import time


class Ticker:
    """A ticker that tracks a symbol and its price, with color encoding."""

    def __init__(self, symbol: str = "", price: float = 0.0):
        self.symbol = symbol
        self.price = price
        self.previous_price = 0.0
        self._color = "white"
        self.timestamp = time.time()

    def update(self, new_price: float) -> None:
        """Update the price and record the previous price."""
        self.previous_price = self.price
        self.price = new_price
        self.timestamp = time.time()

    @property
    def price_color(self) -> str:
        """Return color based on price change."""
        if self.previous_price == 0.0:
            return "white"
        if self.price > self.previous_price:
            return "green"
        elif self.price < self.previous_price:
            return "red"
        else:
            return "white"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "timestamp": self.timestamp,
            "previous_price": self.previous_price,
            "price_color": self.price_color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ticker":
        """Deserialize from dictionary."""
        t = cls(symbol=data.get("symbol", ""), price=data.get("price", 0.0))
        t.timestamp = data.get("timestamp", time.time())
        t.previous_price = data.get("previous_price", 0.0)
        return t
