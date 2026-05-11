"""Bankroll management for tracking bankroll evolution across bets."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Bankroll:
    """Tracks bankroll evolution across a sequence of bets.

    Attributes:
        initial_bankroll: Starting bankroll amount.
        current_bankroll: Current bankroll after all bets.
        history: List of bankroll values after each bet.
    """

    initial_bankroll: float
    current_bankroll: float = 0.0
    history: list[float] = field(default_factory=list)

    def __post_init__(self):
        """Initialize bankroll state."""
        self.current_bankroll = self.initial_bankroll
        self.history = [self.initial_bankroll]

    def bet(self, stake: float, won: bool, payout_multiplier: float) -> float:
        """Process a bet and update the bankroll.

        Args:
            stake: Amount wagered.
            won: Whether the bet was won.
            payout_multiplier: Net payout per unit staked (decimal_odds - 1).

        Returns:
            Net profit/loss from this bet.
        """
        if won:
            profit = stake * payout_multiplier
        else:
            profit = -stake

        self.current_bankroll += profit
        self.history.append(self.current_bankroll)
        return profit

    @property
    def total_wagered(self) -> float:
        """Total amount wagered across all bets."""
        return sum(max(0, h - self.history[i - 1]) for i, h in enumerate(self.history) if i > 0)

    @property
    def net_profit(self) -> float:
        """Net profit from all bets."""
        return self.current_bankroll - self.initial_bankroll

    @property
    def total_return(self) -> float:
        """Total return ratio (final / initial - 1)."""
        if self.initial_bankroll == 0:
            return 0.0
        return (self.current_bankroll / self.initial_bankroll) - 1.0

    def reset(self):
        """Reset bankroll to initial state."""
        self.current_bankroll = self.initial_bankroll
        self.history = [self.initial_bankroll]
