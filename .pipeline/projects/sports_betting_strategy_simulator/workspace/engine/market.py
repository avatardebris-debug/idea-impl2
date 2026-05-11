"""Market model with odds conversion and probability representation.

Supports moneyline, point spread, and over/under bet types.
Includes decimal, American, and fractional odds formats with bidirectional conversion.
Represents implied probability and allows configurable "true probability" for edge calculation.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional


class BetType(Enum):
    """Supported bet types."""
    MONEYLINE = "moneyline"
    POINT_SPREAD = "point_spread"
    OVER_UNDER = "over_under"


class OddsFormat(Enum):
    """Odds format types."""
    DECIMAL = "decimal"
    AMERICAN = "american"
    FRACTIONAL = "fractional"


class Market:
    """Represents a sports betting market with configurable odds and probabilities.

    Attributes:
        bet_type: Type of bet (moneyline, point spread, over/under).
        odds_decimal: Decimal odds (e.g., 2.50).
        odds_american: American odds (e.g., +150).
        odds_fractional: Fractional odds (e.g., 3/2).
        implied_probability: Probability implied by the odds.
        true_probability: Configurable true probability for edge calculation.
        payout_multiplier: Decimal odds minus 1 (net payout per unit staked).
    """

    def __init__(
        self,
        bet_type: BetType = BetType.MONEYLINE,
        odds_decimal: Optional[float] = None,
        odds_american: Optional[int] = None,
        odds_fractional: Optional[tuple[int, int]] = None,
        true_probability: Optional[float] = None,
    ):
        """Initialize a Market.

        Args:
            bet_type: Type of bet.
            odds_decimal: Decimal odds (e.g., 2.50).
            odds_american: American odds (e.g., +150 for positive, -110 for negative).
            odds_fractional: Fractional odds as (numerator, denominator) tuple.
            true_probability: True probability of the outcome (optional).

        One of odds_decimal, odds_american, or odds_fractional must be provided.
        """
        self.bet_type = bet_type
        self._odds_decimal: float = 0.0
        self._odds_american: int = 0
        self._odds_fractional: tuple[int, int] = (0, 1)

        # Provide exactly one odds format
        if odds_decimal is not None:
            self._odds_decimal = odds_decimal
            self._odds_american = self._decimal_to_american(odds_decimal)
            self._odds_fractional = self._decimal_to_fractional(odds_decimal)
        elif odds_american is not None:
            self._odds_american = odds_american
            self._odds_decimal = self._american_to_decimal(odds_american)
            self._odds_fractional = self._decimal_to_fractional(self._odds_decimal)
        elif odds_fractional is not None:
            self._odds_fractional = odds_fractional
            self._odds_decimal = self._fractional_to_decimal(odds_fractional[0], odds_fractional[1])
            self._odds_american = self._decimal_to_american(self._odds_decimal)
        else:
            raise ValueError("One of odds_decimal, odds_american, or odds_fractional must be provided.")

        # Compute derived values
        self.implied_probability = self._compute_implied_probability(self._odds_decimal)
        self.payout_multiplier = self._odds_decimal - 1.0  # Net payout per unit staked

        # True probability (for edge calculation)
        self.true_probability = true_probability if true_probability is not None else self.implied_probability

    @property
    def odds_decimal(self) -> float:
        return self._odds_decimal

    @property
    def odds_american(self) -> int:
        return self._odds_american

    @property
    def odds_fractional(self) -> tuple[int, int]:
        return self._odds_fractional

    @property
    def edge(self) -> float:
        """Calculate the edge (expected value per unit staked).

        Edge = true_probability * payout_multiplier - (1 - true_probability)
        """
        if self.true_probability is None:
            return 0.0
        return self.true_probability * self.payout_multiplier - (1 - self.true_probability)

    @property
    def expected_value(self) -> float:
        """Expected value per unit staked."""
        return self.edge

    @staticmethod
    def _decimal_to_american(decimal_odds: float) -> int:
        """Convert decimal odds to American odds.

        Args:
            decimal_odds: Decimal odds (e.g., 2.50).

        Returns:
            American odds as integer (e.g., +150 or -200).
        """
        if decimal_odds >= 2.0:
            return int((decimal_odds - 1.0) * 100)
        else:
            return int(-100.0 / (decimal_odds - 1.0))

    @staticmethod
    def _american_to_decimal(american_odds: int) -> float:
        """Convert American odds to decimal odds.

        Args:
            american_odds: American odds (e.g., +150 or -110).

        Returns:
            Decimal odds (e.g., 2.50 or 1.909).
        """
        if american_odds > 0:
            return 1.0 + american_odds / 100.0
        else:
            return 1.0 + 100.0 / abs(american_odds)

    @staticmethod
    def _decimal_to_fractional(decimal_odds: float) -> tuple[int, int]:
        """Convert decimal odds to fractional odds.

        Args:
            decimal_odds: Decimal odds (e.g., 2.50).

        Returns:
            Fractional odds as (numerator, denominator) tuple.
        """
        net_odds = decimal_odds - 1.0
        # Use a tolerance for floating point
        numerator = round(net_odds * 10000)
        denominator = 10000
        # Simplify by GCD
        g = _gcd(numerator, denominator)
        return (numerator // g, denominator // g)

    @staticmethod
    def _fractional_to_decimal(numerator: int, denominator: int) -> float:
        """Convert fractional odds to decimal odds.

        Args:
            numerator: Numerator of fractional odds.
            denominator: Denominator of fractional odds.

        Returns:
            Decimal odds.
        """
        if denominator == 0:
            raise ValueError("Denominator cannot be zero.")
        return 1.0 + numerator / denominator

    @staticmethod
    def _compute_implied_probability(decimal_odds: float) -> float:
        """Compute implied probability from decimal odds.

        Args:
            decimal_odds: Decimal odds (e.g., 2.50).

        Returns:
            Implied probability (e.g., 0.40 for decimal odds of 2.50).
        """
        if decimal_odds <= 1.0:
            raise ValueError("Decimal odds must be greater than 1.0.")
        return 1.0 / decimal_odds

    def __repr__(self) -> str:
        return (
            f"Market(bet_type={self.bet_type.value}, "
            f"odds_decimal={self.odds_decimal:.2f}, "
            f"odds_american={self.odds_american:+d}, "
            f"odds_fractional={self.odds_fractional[0]}/{self.odds_fractional[1]}, "
            f"implied_prob={self.implied_probability:.4f}, "
            f"true_prob={self.true_probability:.4f})"
        )


def _gcd(a: int, b: int) -> int:
    """Compute greatest common divisor."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a
