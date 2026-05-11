"""Geometric Brownian Motion (GBM) price simulation."""

from __future__ import annotations

import numpy as np
from numpy import ndarray

from financial_portfolio_simulator.exceptions import SimulationError


class GBM:
    """Geometric Brownian Motion simulator.

    Models asset price evolution as:
        dS(t) = mu * S(t) * dt + sigma * S(t) * dW(t)

    Where:
        mu  = drift (expected return per unit time)
        sigma = volatility (standard deviation of returns)
        dW  = Wiener process (Brownian motion increment)
    """

    def __init__(
        self,
        drift: float = 0.05,
        volatility: float = 0.2,
        seed: int | None = None,
    ):
        """Initialize GBM simulator.

        Args:
            drift: Annualized drift rate (expected return).
            volatility: Annualized volatility (standard deviation).
            seed: Random seed for reproducibility.

        Raises:
            SimulationError: If drift or volatility are invalid.
        """
        if not isinstance(drift, (int, float)):
            raise SimulationError(
                f"drift must be a number, got {type(drift).__name__}.",
                details={"drift": drift},
            )

        if not isinstance(volatility, (int, float)) or volatility < 0:
            raise SimulationError(
                f"volatility must be a non-negative number, got {volatility}.",
                details={"volatility": volatility},
            )

        self.drift = float(drift)
        self.volatility = float(volatility)
        self.rng = np.random.default_rng(seed)

    def simulate(
        self,
        initial_price: float,
        time_steps: int,
        dt: float = 1.0 / 252.0,
        n_paths: int = 1,
    ) -> ndarray:
        """Simulate price paths using GBM.

        Args:
            initial_price: Starting price of the asset.
            time_steps: Number of time steps (e.g., trading days).
            dt: Time step size (default = 1/252 for daily).
            n_paths: Number of independent paths to simulate.

        Returns:
            ndarray of shape (n_paths, time_steps + 1) with price paths.
            Column 0 is the initial price for all paths.

        Raises:
            SimulationError: If parameters are invalid.
        """
        if not isinstance(initial_price, (int, float)) or initial_price <= 0:
            raise SimulationError(
                f"initial_price must be a positive number, got {initial_price}.",
                details={"initial_price": initial_price},
            )

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

        if not isinstance(n_paths, int) or n_paths <= 0:
            raise SimulationError(
                f"n_paths must be a positive integer, got {n_paths}.",
                details={"n_paths": n_paths},
            )

        # Log returns: (mu - sigma^2/2) * dt + sigma * sqrt(dt) * Z
        drift_term = (self.drift - 0.5 * self.volatility**2) * dt
        diffusion_term = self.volatility * np.sqrt(dt)

        # Generate standard normal increments
        Z = self.rng.standard_normal((n_paths, time_steps))

        # Compute log returns
        log_returns = drift_term + diffusion_term * Z

        # Cumulative sum to get log prices, then exponentiate
        log_prices = np.cumsum(log_returns, axis=1)
        prices = initial_price * np.exp(log_prices)

        # Prepend initial price column
        paths = np.column_stack([np.full(n_paths, initial_price), prices])
        return paths

    def simulate_single(
        self,
        initial_price: float,
        time_steps: int,
        dt: float = 1.0 / 252.0,
    ) -> ndarray:
        """Simulate a single price path.

        Returns:
            ndarray of shape (time_steps + 1,) with the price path.

        Raises:
            SimulationError: If parameters are invalid.
        """
        paths = self.simulate(initial_price, time_steps, dt, n_paths=1)
        return paths[0]
