"""Ticker data model for stock tickers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Ticker:
    """Represents a stock ticker with price information."""

    symbol: str
    name: str = ""
    price: float = 0.0
    open_price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    high: float = 0.0
    low: float = 0.0
    previous_close: float = 0.0

    def __post_init__(self):
        """Calculate derived values after initialization."""
        if self.open_price == 0.0 and self.price > 0.0 and self.change != 0.0:
            self.open_price = self.price - self.change
        if self.previous_close == 0.0 and self.open_price > 0.0:
            self.previous_close = self.open_price

    @property
    def is_up(self) -> bool:
        """Check if the ticker is up (positive change)."""
        return self.change > 0

    @property
    def is_down(self) -> bool:
        """Check if the ticker is down (negative change)."""
        return self.change < 0

    @property
    def is_positive_change(self) -> bool:
        """Check if change is positive."""
        return self.change > 0

    @property
    def is_negative_change(self) -> bool:
        """Check if change is negative."""
        return self.change < 0

    @property
    def price_color(self) -> tuple:
        """Get the color for the price display."""
        if self.change > 0:
            return (0.0, 1.0, 0.0)  # Green
        elif self.change < 0:
            return (1.0, 0.0, 0.0)  # Red
        else:
            return (1.0, 1.0, 1.0)  # White

    @property
    def background_color(self) -> tuple:
        """Get the background color for the ticker display."""
        if self.change > 0:
            return (0.0, 0.5, 0.0)  # Dark green
        elif self.change < 0:
            return (0.5, 0.0, 0.0)  # Dark red
        else:
            return (0.2, 0.2, 0.2)  # Gray

    def update_price(self, new_price: float, change: Optional[float] = None, change_percent: Optional[float] = None) -> None:
        """Update the ticker price and optionally change/change_percent."""
        old_price = self.price
        self.price = new_price
        if change is not None:
            self.change = change
        else:
            self.change = new_price - old_price
        if change_percent is not None:
            self.change_percent = change_percent
        elif old_price > 0:
            self.change_percent = (self.change / old_price) * 100

    def to_dict(self) -> Dict:
        """Convert ticker to dictionary."""
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "change": self.change,
            "change_percent": self.change_percent,
            "volume": self.volume,
            "high": self.high,
            "low": self.low,
            "open_price": self.open_price,
            "previous_close": self.previous_close,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> Ticker:
        """Create a ticker from dictionary."""
        return cls(
            symbol=data.get("symbol", ""),
            name=data.get("name", ""),
            price=data.get("price", 0.0),
            change=data.get("change", 0.0),
            change_percent=data.get("change_percent", 0.0),
            volume=data.get("volume", 0),
            high=data.get("high", 0.0),
            low=data.get("low", 0.0),
            open_price=data.get("open_price", 0.0),
            previous_close=data.get("previous_close", 0.0),
        )

    def __eq__(self, other: object) -> bool:
        """Check equality between two tickers."""
        if not isinstance(other, Ticker):
            return NotImplemented
        return (
            self.symbol == other.symbol
            and self.price == other.price
            and self.change == other.change
            and self.change_percent == other.change_percent
        )
