"""Abstract base class for portfolio strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from financial_portfolio_simulator.exceptions import StrategyError

if TYPE_CHECKING:
    from financial_portfolio_simulator.models.portfolio import Portfolio
    import numpy as np


class Strategy(ABC):
    """Base class for portfolio strategies.

    Strategies can modify portfolio allocations over simulation periods.
    Subclasses implement the `apply` method to define rebalancing logic.
    """

    name: str = "base_strategy"

    def __init__(self, name: str | None = None) -> None:
        """Initialize the strategy.

        Args:
            name: Optional custom name for the strategy.
        """
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise StrategyError(
                    "name must be a non-empty string.",
                    details={"name": name},
                )
            self.name = name

    @abstractmethod
    def apply(
        self,
        portfolio: "Portfolio",
        price_paths: dict[str, np.ndarray],
        dt: float,
    ) -> None:
        """Apply the strategy to the portfolio at the current simulation step.

        Args:
            portfolio: The portfolio to modify.
            price_paths: Dict of ticker -> price path array.
            dt: Time step size.

        Raises:
            StrategyError: If parameters are invalid.
        """
        pass

    def __repr__(self) -> str:
        return f"Strategy(name={self.name!r})"
