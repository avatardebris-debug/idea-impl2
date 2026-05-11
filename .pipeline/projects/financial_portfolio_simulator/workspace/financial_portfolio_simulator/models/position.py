"""Position tracking for a single asset in a portfolio."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from financial_portfolio_simulator.exceptions import ModelError


@dataclass
class Position:
    """Tracks the position of a single asset within a portfolio."""

    ticker: str
    quantity: float
    avg_cost: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    price: float = 0.0

    def __post_init__(self) -> None:
        """Validate fields and sync price with current_price if needed."""
        if not isinstance(self.ticker, str) or not self.ticker.strip():
            raise ModelError(
                "ticker must be a non-empty string.",
                details={"ticker": self.ticker},
            )

        if not isinstance(self.quantity, (int, float)) or self.quantity < 0:
            raise ModelError(
                f"quantity must be a non-negative number, got {self.quantity}.",
                details={"quantity": self.quantity},
            )

        if not isinstance(self.avg_cost, (int, float)) or self.avg_cost < 0:
            raise ModelError(
                f"avg_cost must be a non-negative number, got {self.avg_cost}.",
                details={"avg_cost": self.avg_cost},
            )

        # Sync price with current_price if not explicitly set
        if self.price == 0.0 and self.current_price != 0.0:
            self.price = self.current_price
        elif self.price != 0.0 and self.current_price == 0.0:
            self.current_price = self.price

    def update_market_value(self, current_price: float) -> None:
        """Update the current price and recalculate PnL.

        Args:
            current_price: The new current price.

        Raises:
            ModelError: If current_price is invalid.
        """
        if not isinstance(current_price, (int, float)) or current_price < 0:
            raise ModelError(
                f"current_price must be a non-negative number, got {current_price}.",
                details={"current_price": current_price},
            )
        self.current_price = current_price
        self.price = current_price
        self.unrealized_pnl = (current_price - self.avg_cost) * self.quantity

    def update_price(self, price: float) -> None:
        """Alias for update_market_value.

        Args:
            price: The new price.

        Raises:
            ModelError: If price is invalid.
        """
        self.update_market_value(price)

    @property
    def value(self) -> float:
        """Market value of the position."""
        return self.quantity * self.current_price

    @property
    def market_value(self) -> float:
        """Market value of the position (alias for value)."""
        return self.quantity * self.current_price

    def __repr__(self) -> str:
        return (
            f"Position(ticker={self.ticker!r}, qty={self.quantity}, "
            f"avg_cost={self.avg_cost}, current={self.current_price}, "
            f"pnl={self.unrealized_pnl})"
        )
