"""Core Monte Carlo simulation engine for sports betting.

Generates N simulated outcomes for a single market using NumPy vectorized operations.
Supports configurable seed for reproducibility.
"""

from __future__ import annotations
import numpy as np

from .market import Market


class MonteCarloEngine:
    """Monte Carlo engine that simulates sports betting outcomes.

    Attributes:
        seed: Random seed for reproducibility.
    """

    def __init__(self, seed: int = 42):
        """Initialize the Monte Carlo engine.

        Args:
            seed: Random seed for reproducibility.
        """
        self.seed = seed

    def simulate(
        self,
        market: Market,
        n_outcomes: int = 10000,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Simulate N outcomes for a single market.

        Uses np.random.binomial for vectorized outcome generation.

        Args:
            market: The Market object defining the bet parameters.
            n_outcomes: Number of simulated outcomes.

        Returns:
            Tuple of (wins, pnl) where:
                - wins: boolean array of shape (n_outcomes,) indicating wins.
                - pnl: float array of shape (n_outcomes,) with per-bet profit/loss.
        """
        rng = np.random.default_rng(self.seed)
        true_prob = market.true_probability

        # Vectorized outcome generation using binomial
        # 1 = win, 0 = loss
        wins = rng.binomial(n=1, p=true_prob, size=n_outcomes).astype(bool)

        # P&L: win = stake * (odds_decimal - 1), loss = -stake
        # We assume unit stake (1.0) for the simulation
        stake = 1.0
        pnl = np.where(
            wins,
            stake * market.payout_multiplier,
            -stake,
        )

        return wins, pnl

    def simulate_with_custom_stakes(
        self,
        market: Market,
        stakes: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Simulate outcomes with custom stake sizes.

        Args:
            market: The Market object defining the bet parameters.
            stakes: Array of stake sizes for each bet.

        Returns:
            Tuple of (wins, pnl) where:
                - wins: boolean array of shape (len(stakes),) indicating wins.
                - pnl: float array of shape (len(stakes),) with per-bet profit/loss.
        """
        rng = np.random.default_rng(self.seed)
        true_prob = market.true_probability
        n = len(stakes)

        wins = rng.binomial(n=1, p=true_prob, size=n).astype(bool)
        pnl = np.where(
            wins,
            stakes * market.payout_multiplier,
            -stakes,
        )

        return wins, pnl
