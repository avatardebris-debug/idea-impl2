"""Monte Carlo portfolio simulator — runs N iterations and computes risk metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from numpy import ndarray

from financial_portfolio_simulator.exceptions import SimulationError
from financial_portfolio_simulator.models.portfolio import Portfolio
from financial_portfolio_simulator.simulators.gbm import GBM
from financial_portfolio_simulator.simulators.market_simulator import MarketSimulator

if TYPE_CHECKING:
    from financial_portfolio_simulator.strategies.base import Strategy


@dataclass
class SimulationResult:
    """Results from a Monte Carlo portfolio simulation."""

    final_values: ndarray  # shape (n_iterations,)
    mean_final_value: float = 0.0
    median_final_value: float = 0.0
    std_final_value: float = 0.0
    var_95: float = 0.0  # Value at Risk at 95% confidence
    var_99: float = 0.0  # Value at Risk at 99% confidence
    expected_return: float = 0.0  # Expected percentage return
    confidence_intervals: dict = field(default_factory=dict)
    price_paths: dict[str, ndarray] | None = None  # ticker -> (n_paths, time_steps+1)
    initial_value: float = 0.0
    n_iterations: int = 0
    time_horizon: int = 0

    @property
    def worst_case_95(self) -> float:
        """5th percentile of final portfolio values."""
        return float(np.percentile(self.final_values, 5))

    @property
    def worst_case_99(self) -> float:
        """1st percentile of final portfolio values."""
        return float(np.percentile(self.final_values, 1))

    @property
    def best_case_95(self) -> float:
        """95th percentile of final portfolio values."""
        return float(np.percentile(self.final_values, 95))

    @property
    def best_case_99(self) -> float:
        """99th percentile of final portfolio values."""
        return float(np.percentile(self.final_values, 99))

    def summary(self) -> dict:
        """Return a human-readable summary dict."""
        return {
            "initial_value": self.initial_value,
            "mean_final_value": self.mean_final_value,
            "median_final_value": self.median_final_value,
            "std_final_value": self.std_final_value,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "worst_case_95": self.worst_case_95,
            "worst_case_99": self.worst_case_99,
            "best_case_95": self.best_case_95,
            "best_case_99": self.best_case_99,
            "expected_return": self.expected_return,
            "expected_return_pct": self.expected_return * 100,
            "confidence_intervals": self.confidence_intervals,
            "n_iterations": self.n_iterations,
            "time_horizon": self.time_horizon,
        }


class PortfolioSimulator:
    """Runs Monte Carlo simulations on a Portfolio.

    For each iteration:
    1. Simulate price paths for all assets using GBM or correlated MarketSimulator.
    2. Apply the strategy to update allocations over time.
    3. Compute the final portfolio value.

    After N iterations, computes distribution statistics and risk metrics.
    """

    def __init__(
        self,
        seed: int | None = None,
        use_correlated: bool = False,
    ):
        """Initialize PortfolioSimulator.

        Args:
            seed: Random seed for reproducibility.
            use_correlated: Whether to use correlated asset simulation.
        """
        self.seed = seed
        self.use_correlated = use_correlated
        self.rng = np.random.default_rng(seed)
        self.market_sim = MarketSimulator(seed=seed)

    def simulate(
        self,
        portfolio: Portfolio,
        time_steps: int,
        n_iterations: int = 1000,
        dt: float = 1.0 / 252.0,
        strategy: Strategy | None = None,
        correlation_matrix: ndarray | None = None,
    ) -> SimulationResult:
        """Run Monte Carlo simulation on the portfolio.

        Args:
            portfolio: The Portfolio to simulate.
            time_steps: Number of time steps per path.
            n_iterations: Number of Monte Carlo iterations.
            dt: Time step size.
            strategy: Optional Strategy to apply at each period.
            correlation_matrix: Optional NxN correlation matrix for multi-asset.

        Returns:
            SimulationResult with distribution stats and risk metrics.

        Raises:
            SimulationError: If parameters are invalid.
        """
        if not isinstance(portfolio, Portfolio):
            raise SimulationError(
                f"portfolio must be a Portfolio instance, got {type(portfolio).__name__}.",
                details={"portfolio_type": type(portfolio).__name__},
            )

        if not isinstance(time_steps, int) or time_steps <= 0:
            raise SimulationError(
                f"time_steps must be a positive integer, got {time_steps}.",
                details={"time_steps": time_steps},
            )

        if not isinstance(n_iterations, int) or n_iterations <= 0:
            raise SimulationError(
                f"n_iterations must be a positive integer, got {n_iterations}.",
                details={"n_iterations": n_iterations},
            )

        if not isinstance(dt, (int, float)) or dt <= 0:
            raise SimulationError(
                f"dt must be a positive number, got {dt}.",
                details={"dt": dt},
            )

        initial_value = portfolio.total_value
        n_assets = len(portfolio.assets)
        final_values = np.zeros(n_iterations)

        if n_assets == 0:
            return SimulationResult(
                final_values=final_values,
                initial_value=initial_value,
                n_iterations=n_iterations,
                time_horizon=time_steps,
            )

        # Build asset specs for MarketSimulator
        asset_specs = []
        for asset in portfolio.assets:
            asset_specs.append({
                "ticker": asset.ticker,
                "initial_price": asset.price,
                "drift": asset.metadata.get("drift", 0.08),
                "volatility": asset.metadata.get("volatility", 0.2),
            })

        # Build pairwise correlation matrix if requested
        corr_matrix: ndarray | None = None
        if self.use_correlated and n_assets > 1:
            corr_matrix = self._build_correlation_matrix(asset_specs, correlation_matrix)

        # Save original prices to restore between iterations
        original_prices = {a.ticker: a.price for a in portfolio.assets}

        # Accumulate price paths across all iterations for the result
        all_price_paths: dict[str, list[ndarray]] = {spec["ticker"]: [] for spec in asset_specs}

        for i in range(n_iterations):
            # Simulate price paths — each iteration must produce independent random results
            if self.use_correlated and n_assets > 1:
                # For correlated simulation, create a fresh MarketSimulator with a per-iteration seed
                iter_sim = MarketSimulator(seed=self.rng.integers(0, 2**31))
                paths = iter_sim.simulate_correlated(
                    assets=asset_specs,
                    time_steps=time_steps,
                    dt=dt,
                    correlation_matrix=corr_matrix,
                )
            else:
                # Independent GBM per asset — create fresh GBMs each iteration for true Monte Carlo
                paths = {}
                for spec in asset_specs:
                    gbm = GBM(
                        drift=spec["drift"],
                        volatility=spec["volatility"],
                        seed=self.rng.integers(0, 2**31),
                    )
                    paths[spec["ticker"]] = gbm.simulate_single(
                        spec["initial_price"], time_steps, dt
                    )

            # Accumulate price paths for the result
            for ticker, path in paths.items():
                all_price_paths[ticker].append(path)

            # Apply strategy if provided
            if strategy is not None:
                strategy.apply(portfolio, paths, dt)

            # Compute final portfolio value
            final_value = 0.0
            for asset in portfolio.assets:
                final_price = paths[asset.ticker][-1]
                asset.update_price(final_price)
                final_value += asset.value

            final_values[i] = final_value

            # Restore original prices for next iteration
            for asset in portfolio.assets:
                asset.update_price(original_prices[asset.ticker])

        # Stack accumulated price paths into (n_iterations, time_steps+1) arrays
        stacked_paths: dict[str, ndarray] = {}
        for ticker, path_list in all_price_paths.items():
            stacked_paths[ticker] = np.array(path_list)

        # Compute statistics
        result = SimulationResult(
            final_values=final_values,
            mean_final_value=float(np.mean(final_values)),
            median_final_value=float(np.median(final_values)),
            std_final_value=float(np.std(final_values)),
            var_95=float(np.percentile(final_values, 5)),
            var_99=float(np.percentile(final_values, 1)),
            expected_return=(np.mean(final_values) - initial_value) / initial_value if initial_value > 0 else 0.0,
            confidence_intervals={
                (5, 95): (float(np.percentile(final_values, 5)), float(np.percentile(final_values, 95))),
                (1, 99): (float(np.percentile(final_values, 1)), float(np.percentile(final_values, 99))),
            },
            price_paths=stacked_paths if n_iterations > 0 else None,
            initial_value=initial_value,
            n_iterations=n_iterations,
            time_horizon=time_steps,
        )
        return result

    def _build_correlation_matrix(
        self,
        asset_specs: list[dict],
        provided_matrix: ndarray | None,
    ) -> ndarray:
        """Build a pairwise correlation matrix from asset specs or use provided matrix.

        Args:
            asset_specs: List of asset specification dicts.
            provided_matrix: Optional NxN correlation matrix.

        Returns:
            NxN correlation matrix.

        Raises:
            SimulationError: If matrix dimensions don't match number of assets.
        """
        n = len(asset_specs)
        if n == 1:
            return np.array([[1.0]])

        if provided_matrix is not None:
            if provided_matrix.shape != (n, n):
                raise SimulationError(
                    f"Correlation matrix shape {provided_matrix.shape} does not match "
                    f"number of assets ({n}).",
                    details={"matrix_shape": provided_matrix.shape, "n_assets": n},
                )
            # Validate correlation values are in [-1, 1]
            if np.any(provided_matrix < -1.0) or np.any(provided_matrix > 1.0):
                raise SimulationError(
                    "Correlation matrix contains values outside [-1, 1].",
                    details={"min_value": float(np.min(provided_matrix)), "max_value": float(np.max(provided_matrix))},
                )
            # Validate diagonal is 1.0
            if not np.allclose(np.diag(provided_matrix), 1.0):
                raise SimulationError(
                    "Correlation matrix diagonal must be 1.0.",
                )
            # Validate symmetry
            if not np.allclose(provided_matrix, provided_matrix.T):
                raise SimulationError(
                    "Correlation matrix must be symmetric.",
                )
            return provided_matrix

        # Build from asset specs — use metadata correlation if available, else 0
        corr = np.zeros((n, n))
        for i in range(n):
            corr[i, i] = 1.0
            for j in range(i + 1, n):
                # Try to get correlation from asset metadata
                corr_val = asset_specs[i].get("correlation", 0.0)
                corr[i, j] = corr_val
                corr[j, i] = corr_val

        # Validate built matrix
        if np.any(corr < -1.0) or np.any(corr > 1.0):
            raise SimulationError(
                "Correlation values from asset specs must be in [-1, 1].",
            )
        return corr
