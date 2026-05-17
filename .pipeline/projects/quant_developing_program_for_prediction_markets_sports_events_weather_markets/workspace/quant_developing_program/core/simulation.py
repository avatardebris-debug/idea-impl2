"""Sharpe ratio simulation and Monte Carlo engine.

Provides:
    - SharpeRatioSimulator: Simulates Sharpe ratio distributions.
    - MonteCarloEngine: General Monte Carlo simulation engine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class SharpeResult:
    """Result of Sharpe ratio simulation.

    Attributes:
        mean_sharpe: Mean of simulated Sharpe ratios.
        std_sharpe: Standard deviation of simulated Sharpe ratios.
        median_sharpe: Median of simulated Sharpe ratios.
        percentile_5: 5th percentile of simulated Sharpe ratios.
        percentile_95: 95th percentile of simulated Sharpe ratios.
        num_simulations: Number of simulations performed.
    """
    mean_sharpe: float
    std_sharpe: float
    median_sharpe: float
    percentile_5: float
    percentile_95: float
    num_simulations: int


class SharpeRatioSimulator:
    """Simulates Sharpe ratio distributions for strategy evaluation.

    Uses Monte Carlo simulation to estimate the distribution of
    Sharpe ratios given strategy parameters.
    """

    @staticmethod
    def calculate_sharpe(returns: list[float], risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio from returns.

        Args:
            returns: List of periodic returns.
            risk_free_rate: Risk-free rate (default 0).

        Returns:
            Sharpe ratio.
        """
        if len(returns) < 2:
            return 0.0

        returns_arr = np.array(returns)
        excess_returns = returns_arr - risk_free_rate

        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns, ddof=1)

        if std_excess == 0:
            return 0.0

        return float(mean_excess / std_excess)

    def simulate(
        self,
        num_simulations: int = 10000,
        num_periods: int = 252,
        mean_return: float = 0.001,
        std_return: float = 0.02,
        risk_free_rate: float = 0.0,
        correlation: float = 0.0,
        seed: Optional[int] = None,
    ) -> SharpeResult:
        """Simulate Sharpe ratio distribution.

        Args:
            num_simulations: Number of Monte Carlo simulations.
            num_periods: Number of periods per simulation (e.g., 252 for daily).
            mean_return: Mean periodic return.
            std_return: Standard deviation of periodic returns.
            risk_free_rate: Risk-free rate per period.
            correlation: Correlation between assets (for multi-asset).
            seed: Random seed for reproducibility.

        Returns:
            SharpeResult with distribution statistics.
        """
        rng = np.random.default_rng(seed)

        sharpe_ratios = []

        for _ in range(num_simulations):
            # Generate correlated returns
            if correlation != 0:
                # Simple bivariate simulation
                z1 = rng.standard_normal(num_periods)
                z2 = rng.standard_normal(num_periods)
                # Correlate z2 with z1
                z2_corr = correlation * z1 + math.sqrt(1 - correlation**2) * z2
                returns = mean_return + std_return * z2_corr
            else:
                returns = mean_return + std_return * rng.standard_normal(num_periods)

            sharpe = self.calculate_sharpe(returns.tolist(), risk_free_rate)
            sharpe_ratios.append(sharpe)

        sharpe_arr = np.array(sharpe_ratios)

        return SharpeResult(
            mean_sharpe=float(np.mean(sharpe_arr)),
            std_sharpe=float(np.std(sharpe_arr, ddof=1)),
            median_sharpe=float(np.median(sharpe_arr)),
            percentile_5=float(np.percentile(sharpe_arr, 5)),
            percentile_95=float(np.percentile(sharpe_arr, 95)),
            num_simulations=num_simulations,
        )


@dataclass
class MonteCarloResult:
    """Result of a Monte Carlo simulation.

    Attributes:
        outcomes: List of simulated outcomes.
        mean: Mean of outcomes.
        std: Standard deviation of outcomes.
        min_val: Minimum outcome.
        max_val: Maximum outcome.
        percentile_5: 5th percentile.
        percentile_95: 95th percentile.
        num_simulations: Number of simulations performed.
    """
    outcomes: list[float]
    mean: float
    std: float
    min_val: float
    max_val: float
    percentile_5: float
    percentile_95: float
    num_simulations: int


class MonteCarloEngine:
    """General Monte Carlo simulation engine.

    Supports custom simulation functions and provides
    statistical summaries of results.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize the Monte Carlo engine.

        Args:
            seed: Random seed for reproducibility.
        """
        self.rng = np.random.default_rng(seed)

    def run(
        self,
        num_simulations: int,
        simulation_func,
        **kwargs,
    ) -> MonteCarloResult:
        """Run Monte Carlo simulation.

        Args:
            num_simulations: Number of simulations to run.
            simulation_func: Function that takes **kwargs and returns a float outcome.
            **kwargs: Additional arguments passed to simulation_func.

        Returns:
            MonteCarloResult with statistical summaries.
        """
        outcomes = []

        for _ in range(num_simulations):
            try:
                outcome = simulation_func(rng=self.rng, **kwargs)
                outcomes.append(outcome)
            except Exception as e:
                # Skip failed simulations
                continue

        if not outcomes:
            raise ValueError("No successful simulations completed")

        outcomes_arr = np.array(outcomes)

        return MonteCarloResult(
            outcomes=list(outcomes),
            mean=float(np.mean(outcomes_arr)),
            std=float(np.std(outcomes_arr, ddof=1)),
            min_val=float(np.min(outcomes_arr)),
            max_val=float(np.max(outcomes_arr)),
            percentile_5=float(np.percentile(outcomes_arr, 5)),
            percentile_95=float(np.percentile(outcomes_arr, 95)),
            num_simulations=len(outcomes),
        )

    def run_with_callback(
        self,
        num_simulations: int,
        simulation_func,
        callback_func,
        **kwargs,
    ) -> list:
        """Run Monte Carlo simulation with a callback for each simulation.

        Args:
            num_simulations: Number of simulations to run.
            simulation_func: Function that takes **kwargs and returns a float outcome.
            callback_func: Function called with each outcome (outcome, simulation_index).
            **kwargs: Additional arguments passed to simulation_func.

        Returns:
            List of callback results.
        """
        results = []

        for i in range(num_simulations):
            try:
                outcome = simulation_func(rng=self.rng, **kwargs)
                callback_result = callback_func(outcome, i)
                results.append(callback_result)
            except Exception as e:
                # Skip failed simulations
                continue

        return results
