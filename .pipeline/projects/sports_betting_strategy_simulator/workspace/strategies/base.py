"""Abstract strategy interface for betting strategies."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from ..engine.market import Market


class Strategy(ABC):
    """Abstract base class for betting strategies.

    All strategies must implement the `stake` method which determines
    the stake size given the current bankroll and market conditions.
    """

    @abstractmethod
    def stake(self, bankroll: float, market: Market) -> float:
        """Determine the stake size for a given bankroll and market.

        Args:
            bankroll: Current bankroll amount.
            market: The Market object with odds and probability information.

        Returns:
            Stake amount (fraction of bankroll or absolute amount).
        """
        pass

    @abstractmethod
    def stake_fraction(self, bankroll: float, market: Market) -> float:
        """Determine the stake as a fraction of bankroll.

        Args:
            bankroll: Current bankroll amount.
            market: The Market object with odds and probability information.

        Returns:
            Stake fraction (e.g., 0.02 means 2% of bankroll).
        """
        pass
