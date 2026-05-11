"""Portfolio — a collection of Asset holdings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from financial_portfolio_simulator.exceptions import ModelError
from financial_portfolio_simulator.models.asset import Asset
from financial_portfolio_simulator.models.position import Position


@dataclass
class Portfolio:
    """A portfolio of assets with value and weighting calculations."""

    name: str = "Portfolio"
    assets: List[Asset] = field(default_factory=list)
    positions: List[Position] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate fields after initialization."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ModelError(
                "name must be a non-empty string.",
                details={"name": self.name},
            )

    # ---- construction helpers ----

    @classmethod
    def from_assets(cls, name: str = "Portfolio", assets: list[Asset] | None = None) -> Portfolio:
        """Create a Portfolio from a list of Asset objects.

        Args:
            name: Portfolio name.
            assets: Optional list of Asset objects.

        Returns:
            A new Portfolio instance.

        Raises:
            ModelError: If name is invalid.
        """
        if not isinstance(name, str) or not name.strip():
            raise ModelError(
                "name must be a non-empty string.",
                details={"name": name},
            )
        portfolio = cls(name=name)
        if assets:
            for asset in assets:
                portfolio.add_asset(asset)
        return portfolio

    def add_asset(self, asset: Asset) -> None:
        """Add an asset to the portfolio and create a corresponding position.

        Args:
            asset: The Asset to add.

        Raises:
            ModelError: If asset is not an Asset instance.
        """
        if not isinstance(asset, Asset):
            raise ModelError(
                f"asset must be an Asset instance, got {type(asset).__name__}.",
                details={"asset_type": type(asset).__name__},
            )
        self.assets.append(asset)
        self.positions.append(
            Position(
                ticker=asset.ticker,
                quantity=asset.quantity,
                avg_cost=asset.price,
                current_price=asset.price,
            )
        )

    # ---- portfolio metrics ----

    @property
    def total_value(self) -> float:
        """Total market value of all holdings."""
        return sum(a.value for a in self.assets)

    @property
    def weights(self) -> dict[str, float]:
        """Per-asset weightings (fraction of total portfolio value)."""
        total = self.total_value
        if total == 0:
            return {a.ticker: 0.0 for a in self.assets}
        return {a.ticker: a.value / total for a in self.assets}

    def remove_asset(self, ticker: str) -> None:
        """Remove an asset from the portfolio by ticker.

        Args:
            ticker: The ticker of the asset to remove.

        Raises:
            ModelError: If ticker is not a string.
        """
        if not isinstance(ticker, str):
            raise ModelError(
                f"ticker must be a string, got {type(ticker).__name__}.",
                details={"ticker_type": type(ticker).__name__},
            )
        self.assets = [a for a in self.assets if a.ticker != ticker]
        self.positions = [p for p in self.positions if p.ticker != ticker]

    def get_asset(self, ticker: str) -> Asset | None:
        """Get an asset by ticker, or None if not found.

        Args:
            ticker: The ticker to search for.

        Returns:
            The Asset if found, None otherwise.
        """
        for a in self.assets:
            if a.ticker == ticker:
                return a
        return None

    @property
    def allocation(self) -> dict[str, float]:
        """Per-asset allocation as fractions of total portfolio value."""
        total = self.total_value
        if total == 0:
            return {a.ticker: 0.0 for a in self.assets}
        return {a.ticker: a.value / total for a in self.assets}

    @property
    def weight_list(self) -> List[float]:
        """Weights as a list matching the order of self.assets."""
        total = self.total_value
        if total == 0:
            return [0.0] * len(self.assets)
        return [a.value / total for a in self.assets]

    def update_prices(self, price_map: dict[str, float]) -> None:
        """Update asset prices from a ticker -> price mapping.

        Args:
            price_map: Dictionary mapping ticker to new price.

        Raises:
            ModelError: If price_map is not a dict.
        """
        if not isinstance(price_map, dict):
            raise ModelError(
                f"price_map must be a dict, got {type(price_map).__name__}.",
                details={"price_map_type": type(price_map).__name__},
            )
        for asset in self.assets:
            if asset.ticker in price_map:
                asset.update_price(price_map[asset.ticker])
        # Also update positions
        for pos in self.positions:
            if pos.ticker in price_map:
                pos.update_market_value(price_map[pos.ticker])

    def __repr__(self) -> str:
        return (
            f"Portfolio(name={self.name!r}, value={self.total_value:.2f}, "
            f"assets={len(self.assets)})"
        )
