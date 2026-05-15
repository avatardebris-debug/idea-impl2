"""Kelly criterion strategy implementations.

Supports full Kelly and fractional Kelly variants.
Given true probability and odds, calculates the optimal fraction of bankroll to bet.
"""

from __future__ import annotations
from .base import Strategy
from engine.market import Market


class KellyStrategy(Strategy):
    """Kelly criterion strategy (full or fractional).

    Full Kelly fraction: f* = (p*b - q) / b
    where p = true probability, b = decimal_odds - 1, q = 1 - p.

    Fractional Kelly scales this by a configurable factor (e.g., 0.5 for half-Kelly).
    """

    def __init__(self, fractional_factor: float = 1.0):
        """Initialize Kelly strategy.

        Args:
            fractional_factor: Fraction of full Kelly to bet (1.0 = full Kelly, 0.5 = half-Kelly).
        """
        if fractional_factor < 0 or fractional_factor > 1:
            raise ValueError("fractional_factor must be between 0 and 1.")
        self.fractional_factor = fractional_factor

    def _compute_kelly_fraction(self, market: Market) -> float:
        """Compute the full Kelly fraction for a given market.

        Args:
            market: The Market object with true_probability and payout_multiplier.

        Returns:
            Kelly fraction (fraction of bankroll to bet).
        """
        p = market.true_probability
        b = market.payout_multiplier  # decimal_odds - 1
        q = 1.0 - p

        if b <= 0:
            return 0.0

        kelly_fraction = (p * b - q) / b

        # Kelly fraction is only positive when there's an edge
        if kelly_fraction < 0:
            return 0.0

        return kelly_fraction

    def stake_fraction(self, bankroll: float, market: Market) -> float:
        """Compute the stake fraction using Kelly criterion.

        Args:
            bankroll: Current bankroll amount.
            market: The Market object with odds and probability information.

        Returns:
            Stake fraction (fraction of bankroll to bet).
        """
        full_kelly = self._compute_kelly_fraction(market)
        return self.fractional_factor * full_kelly

    def stake(self, bankroll: float, market: Market) -> float:
        """Compute the absolute stake amount using Kelly criterion.

        Args:
            bankroll: Current bankroll amount.
            market: The Market object with odds and probability information.

        Returns:
            Absolute stake amount.
        """
        fraction = self.stake_fraction(bankroll, market)
        return fraction * bankroll

    def __repr__(self) -> str:
        return f"KellyStrategy(fractional_factor={self.fractional_factor})"


class FixedStakeStrategy(Strategy):
    """Fixed stake strategy that bets a constant fraction of bankroll.

    Unlike Kelly, this always bets the same fraction regardless of edge.
    """

    def __init__(self, stake_fraction: float):
        """Initialize fixed stake strategy.

        Args:
            stake_fraction: Fraction of bankroll to bet each time (e.g., 0.02 for 2%).
        """
        if stake_fraction < 0 or stake_fraction > 1:
            raise ValueError("stake_fraction must be between 0 and 1.")
        self._stake_fraction = stake_fraction

    def stake_fraction(self, bankroll: float, market: Market) -> float:
        """Return the fixed stake fraction.

        Args:
            bankroll: Current bankroll amount (ignored).
            market: The Market object (ignored).

        Returns:
            Fixed stake fraction.
        """
        return self._stake_fraction

    def stake(self, bankroll: float, market: Market) -> float:
        """Return the fixed stake amount.

        Args:
            bankroll: Current bankroll amount.
            market: The Market object (ignored).

        Returns:
            Absolute stake amount.
        """
        return self._stake_fraction * bankroll

    def __repr__(self) -> str:
        return f"FixedStakeStrategy(stake_fraction={self._stake_fraction})"
