"""Asset representation for the portfolio simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from financial_portfolio_simulator.exceptions import ModelError


@dataclass
class Asset:
    """Represents a single holding (stock or crypto)."""

    ticker: str
    asset_type: Literal["stock", "crypto"]
    quantity: float = 0.0
    price: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not isinstance(self.ticker, str) or not self.ticker.strip():
            raise ModelError(
                "ticker must be a non-empty string.",
                details={"ticker": self.ticker},
            )

        if self.asset_type not in ("stock", "crypto"):
            raise ModelError(
                f"asset_type must be 'stock' or 'crypto', got '{self.asset_type}'.",
                details={"asset_type": self.asset_type},
            )

        if not isinstance(self.quantity, (int, float)) or self.quantity < 0:
            raise ModelError(
                f"quantity must be a non-negative number, got {self.quantity}.",
                details={"quantity": self.quantity},
            )

        if not isinstance(self.price, (int, float)) or self.price < 0:
            raise ModelError(
                f"price must be a non-negative number, got {self.price}.",
                details={"price": self.price},
            )

    @property
    def value(self) -> float:
        """Current market value of this asset holding."""
        return self.quantity * self.price

    def update_price(self, new_price: float) -> None:
        """Update the asset's price.

        Args:
            new_price: The new price value.

        Raises:
            ModelError: If new_price is invalid.
        """
        if not isinstance(new_price, (int, float)) or new_price < 0:
            raise ModelError(
                f"new_price must be a non-negative number, got {new_price}.",
                details={"new_price": new_price},
            )
        self.price = new_price

    def __repr__(self) -> str:
        return (
            f"Asset(ticker={self.ticker!r}, type={self.asset_type!r}, "
            f"qty={self.quantity}, price={self.price})"
        )
