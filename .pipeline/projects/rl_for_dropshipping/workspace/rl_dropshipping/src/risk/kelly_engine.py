"""Kelly Criterion budget allocation engine.

Implements the Kelly criterion for optimal bet sizing with a hard cap
at 10% of total budget. Uses fractional (half) Kelly by default for safety.

Core formula: f* = (b*p - q) / b
    where b = odds, p = win probability, q = 1 - p

The engine is callable from the RL agent's action pipeline and returns
a capped budget allocation per channel.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Maximum fraction of total budget allowed (10% cap)
MAX_BUDGET_FRACTION = 0.10

# Fractional Kelly multiplier (half-Kelly for safety)
FRACTIONAL_KELLY = 0.5


class KellyEngine:
    """Kelly criterion budget allocation engine.

    Attributes:
        fractional_multiplier: Fraction of full Kelly to use (default 0.5 = half-Kelly).
        max_budget_fraction: Hard cap on allocation as fraction of total budget (default 0.10).
        win_rate: Historical win rate, dynamically updated.
        confidence: Agent confidence in current predictions.
        n_wins: Number of winning decisions.
        n_losses: Number of losing decisions.
        n_total: Total number of decisions.
    """

    def __init__(
        self,
        fractional_multiplier: float = FRACTIONAL_KELLY,
        max_budget_fraction: float = MAX_BUDGET_FRACTION,
    ):
        self.fractional_multiplier = fractional_multiplier
        self.max_budget_fraction = max_budget_fraction
        self.win_rate: float = 0.5  # Default prior
        self.confidence: float = 0.5
        self.n_wins: int = 0
        self.n_losses: int = 0
        self.n_total: int = 0

    def update_win_rate(self, is_win: bool) -> float:
        """Update the win rate with a new outcome.

        Args:
            is_win: True if the last decision was a win, False otherwise.

        Returns:
            Updated win rate.
        """
        self.n_total += 1
        if is_win:
            self.n_wins += 1
        else:
            self.n_losses += 1
        # Use empirical win rate with a minimum prior to avoid division issues
        self.win_rate = self.n_wins / max(self.n_total, 1)
        return self.win_rate

    def set_confidence(self, confidence: float) -> None:
        """Set the agent's confidence in current predictions.

        Args:
            confidence: Confidence value in [0, 1].
        """
        self.confidence = max(0.0, min(1.0, confidence))

    def compute_kelly_fraction(self, odds: float) -> float:
        """Compute the Kelly fraction for given odds.

        Args:
            odds: Decimal odds (e.g., 2.5 means you get 2.5x your bet back).

        Returns:
            Fractional Kelly fraction capped at max_budget_fraction.
        """
        if odds <= 0:
            return 0.0

        # p = win probability, q = lose probability
        p = self.win_rate * self.confidence
        q = 1.0 - p

        # b = net odds (odds - 1)
        b = odds - 1.0

        # Full Kelly: f* = (b*p - q) / b
        if b <= 0:
            return 0.0

        full_kelly = (b * p - q) / b

        # Apply fractional multiplier
        fractional_kelly = full_kelly * self.fractional_multiplier

        # Cap at max budget fraction
        capped = min(fractional_kelly, self.max_budget_fraction)

        # Ensure non-negative
        return max(capped, 0.0)

    def allocate_budget(self, total_budget: float, odds: float) -> float:
        """Allocate budget using Kelly criterion.

        Args:
            total_budget: Total available budget.
            odds: Decimal odds for the current opportunity.

        Returns:
            Allocated budget amount.
        """
        fraction = self.compute_kelly_fraction(odds)
        allocated = total_budget * fraction
        return max(allocated, 0.0)

    def get_state(self) -> dict:
        """Get the current state of the Kelly engine.

        Returns:
            Dictionary with engine state.
        """
        return {
            "win_rate": self.win_rate,
            "confidence": self.confidence,
            "n_wins": self.n_wins,
            "n_losses": self.n_losses,
            "n_total": self.n_total,
            "fractional_multiplier": self.fractional_multiplier,
            "max_budget_fraction": self.max_budget_fraction,
        }

    def __repr__(self) -> str:
        return (
            f"KellyEngine(win_rate={self.win_rate:.3f}, "
            f"confidence={self.confidence:.3f}, "
            f"n_total={self.n_total})"
        )
