"""Market simulator — handles correlated multi-asset price simulation."""

from __future__ import annotations

import numpy as np
from numpy import ndarray

from financial_portfolio_simulator.exceptions import SimulationError
from financial_portfolio_simulator.simulators.gbm import GBM


class MarketSimulator:
    """Simulates correlated multi-asset market movements.

    Uses Cholesky decomposition to generate correlated Brownian motions
    from a correlation matrix, then applies GBM to each asset.
    """

    def __init__(self, seed: int | None = None):
        """Initialize MarketSimulator.

        Args:
            seed: Random seed for reproducibility.
        """
        self.rng = np.random.default_rng(seed)

    def simulate_correlated(
        self,
        assets: list[dict],
        time_steps: int,
        dt: float = 1.0 / 252.0,
        correlation_matrix: ndarray | None = None,
    ) -> dict[str, ndarray]:
        """Simulate correlated price paths for multiple assets.

        Args:
            assets: List of dicts with keys:
                - ticker (str): asset identifier
                - initial_price (float)
                - drift (float): expected annual return
                - volatility (float): annual volatility
                - correlation (float, optional): correlation with other assets
            time_steps: Number of time steps.
            dt: Time step size.
            correlation_matrix: Optional NxN correlation matrix. If None,
                uses pairwise correlations from asset dicts.

        Returns:
            Dict mapping ticker -> ndarray of shape (time_steps + 1,) with price paths.

        Raises:
            SimulationError: If parameters are invalid.
        """
        if not assets:
            return {}

        if not isinstance(time_steps, int) or time_steps <= 0:
            raise SimulationError(
                f"time_steps must be a positive integer, got {time_steps}.",
                details={"time_steps": time_steps},
            )

        if not isinstance(dt, (int, float)) or dt <= 0:
            raise SimulationError(
                f"dt must be a positive number, got {dt}.",
                details={"dt": dt},
            )

        n = len(assets)

        # Build correlation matrix
        if correlation_matrix is not None:
            corr = np.array(correlation_matrix, dtype=float)
            if corr.shape != (n, n):
                raise SimulationError(
                    f"Correlation matrix shape {corr.shape} does not match "
                    f"number of assets ({n}).",
                    details={"matrix_shape": corr.shape, "n_assets": n},
                )
            # Check symmetry
            if not np.allclose(corr, corr.T):
                raise SimulationError(
                    "Correlation matrix must be symmetric.",
                    details={"matrix_shape": corr.shape},
                )
            # Check positive semi-definite
            try:
                np.linalg.cholesky(corr)
            except np.linalg.LinAlgError:
                raise SimulationError(
                    "Correlation matrix must be positive semi-definite.",
                    details={"matrix_shape": corr.shape},
                )
        else:
            corr = np.eye(n)
            for i in range(n):
                for j in range(i + 1, n):
                    c = assets[i].get("correlation", 0.0)
                    if not (-1.0 <= c <= 1.0):
                        raise SimulationError(
                            f"Correlation value for asset '{assets[i]['ticker']}' must be in [-1, 1], got {c}.",
                            details={"ticker": assets[i]["ticker"], "correlation": c},
                        )
                    corr[i, j] = c
                    corr[j, i] = c

        # Cholesky decomposition for correlated normals
        try:
            L = np.linalg.cholesky(corr)
        except np.linalg.LinAlgError:
            raise SimulationError(
                "Failed to compute Cholesky decomposition of correlation matrix. "
                "Ensure the matrix is positive semi-definite.",
                details={"matrix_shape": corr.shape},
            )

        # Generate independent standard normals
        Z_independent = self.rng.standard_normal((n, time_steps))

        # Apply correlation: Z_correlated = L @ Z_independent
        Z_correlated = L @ Z_independent

        results: dict[str, ndarray] = {}
        for i, asset in enumerate(assets):
            gbm = GBM(
                drift=asset["drift"],
                volatility=asset["volatility"],
                seed=None,  # already seeded via MarketSimulator
            )
            # Use correlated increments
            Z = Z_correlated[i]
            initial_price = asset["initial_price"]
            drift_term = (asset["drift"] - 0.5 * asset["volatility"]**2) * dt
            diffusion_term = asset["volatility"] * np.sqrt(dt)

            log_returns = drift_term + diffusion_term * Z
            log_prices = np.cumsum(log_returns)
            prices = initial_price * np.exp(log_prices)

            # Prepend initial price
            path = np.concatenate([[initial_price], prices])
            results[asset["ticker"]] = path

        return results
