"""High-level API for running Monte Carlo portfolio simulations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from financial_portfolio_simulator.exceptions import (
    InvalidAssetError,
    SimulationError,
    StrategyError,
)
from financial_portfolio_simulator.models.asset import Asset
from financial_portfolio_simulator.models.portfolio import Portfolio
from financial_portfolio_simulator.simulators.portfolio_simulator import PortfolioSimulator, SimulationResult
from financial_portfolio_simulator.strategies.buy_and_hold import BuyAndHold

if TYPE_CHECKING:
    from typing import Literal


def _validate_asset(asset: dict) -> None:
    """Validate a single asset specification dict."""
    required_keys = ["ticker", "asset_type", "quantity", "price"]
    for key in required_keys:
        if key not in asset:
            raise InvalidAssetError(
                f"Asset specification is missing required key '{key}'. "
                f"Required keys: {required_keys}",
                details={"missing_key": key},
            )

    if not isinstance(asset["ticker"], str) or not asset["ticker"].strip():
        raise InvalidAssetError("Asset 'ticker' must be a non-empty string.", details={"ticker": asset.get("ticker")})

    if not isinstance(asset["asset_type"], str) or not asset["asset_type"].strip():
        raise InvalidAssetError("Asset 'asset_type' must be a non-empty string.", details={"asset_type": asset.get("asset_type")})

    if not isinstance(asset["quantity"], (int, float)) or asset["quantity"] < 0:
        raise InvalidAssetError(
            f"Asset 'quantity' must be a non-negative number, got {asset['quantity']}.",
            details={"quantity": asset["quantity"]},
        )

    if not isinstance(asset["price"], (int, float)) or asset["price"] <= 0:
        raise InvalidAssetError(
            f"Asset 'price' must be a positive number, got {asset['price']}.",
            details={"price": asset["price"]},
        )


def _validate_assets(assets: list[dict]) -> None:
    """Validate a list of asset specifications."""
    if not assets:
        raise InvalidAssetError("Asset list cannot be empty.", details={"assets": assets})

    tickers = [a["ticker"] for a in assets]
    if len(tickers) != len(set(tickers)):
        raise InvalidAssetError(
            f"Duplicate tickers found in asset list: {tickers}",
            details={"duplicate_tickers": tickers},
        )

    for asset in assets:
        _validate_asset(asset)


def _validate_strategy(strategy) -> None:
    """Validate that a strategy object is properly configured."""
    if strategy is None:
        return
    if not hasattr(strategy, "apply"):
        raise StrategyError(
            "Strategy must have an 'apply' method.",
            details={"strategy": strategy},
        )


def run_simulation(
    assets: list[dict],
    time_steps: int = 252,
    n_iterations: int = 1000,
    seed: int | None = None,
    strategy: str | None = None,
    use_correlated: bool = False,
    correlation_matrix: np.ndarray | None = None,
) -> SimulationResult:
    """Run a Monte Carlo simulation of a portfolio.

    Args:
        assets: List of asset dicts with keys: ticker, asset_type, quantity, price.
                Optional keys: drift, volatility, correlation.
        time_steps: Number of time steps in the simulation.
        n_iterations: Number of Monte Carlo iterations.
        seed: Random seed for reproducibility.
        strategy: Strategy name (e.g., "buy_and_hold").
        use_correlated: Whether to use correlated asset simulation.
        correlation_matrix: Correlation matrix for correlated simulation.

    Returns:
        SimulationResult with final values and statistics.

    Raises:
        InvalidAssetError: If asset specifications are invalid.
        SimulationError: If simulation parameters are invalid.
        StrategyError: If strategy specification is invalid.
    """
    # Validate inputs
    if assets:
        _validate_assets(assets)

    if time_steps <= 0:
        raise SimulationError(
            f"time_steps must be positive, got {time_steps}.",
            details={"time_steps": time_steps},
        )

    if n_iterations <= 0:
        raise SimulationError(
            f"n_iterations must be positive, got {n_iterations}.",
            details={"n_iterations": n_iterations},
        )

    # Create assets
    asset_objects = []
    for asset_dict in assets:
        asset = Asset(
            ticker=asset_dict["ticker"],
            asset_type=asset_dict["asset_type"],
            quantity=asset_dict["quantity"],
            price=asset_dict["price"],
            metadata={
                k: v for k, v in asset_dict.items()
                if k not in ("ticker", "asset_type", "quantity", "price")
            },
        )
        asset_objects.append(asset)

    # Create portfolio
    portfolio = Portfolio(name="Simulation Portfolio", assets=asset_objects)

    # Create strategy
    strategy_obj = None
    if strategy == "buy_and_hold":
        strategy_obj = BuyAndHold()
    elif strategy is not None:
        raise StrategyError(
            f"Unknown strategy: '{strategy}'. Supported strategies: 'buy_and_hold'.",
            details={"strategy": strategy},
        )

    # Run simulation
    sim = PortfolioSimulator(seed=seed, use_correlated=use_correlated)
    result = sim.simulate(
        portfolio,
        time_steps=time_steps,
        n_iterations=n_iterations,
        correlation_matrix=correlation_matrix,
        strategy=strategy_obj,
    )

    return result
