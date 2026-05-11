"""Buy and Hold strategy — the baseline strategy.

Does nothing: the portfolio is held without rebalancing throughout the simulation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from financial_portfolio_simulator.strategies.base import Strategy

if TYPE_CHECKING:
    from financial_portfolio_simulator.models.portfolio import Portfolio
    import numpy as np


class BuyAndHold(Strategy):
    """Buy and Hold strategy.

    Maintains the original asset allocation without any rebalancing.
    This is the simplest baseline strategy for comparison.
    """

    name = "buy_and_hold"

    def apply(
        self,
        portfolio: "Portfolio",
        price_paths: dict[str, "np.ndarray"],
        dt: float,
    ) -> None:
        """No-op: buy and hold means no rebalancing.

        The portfolio value naturally changes as asset prices evolve
        through the simulation, but no trades are executed.

        Args:
            portfolio: The portfolio (unchanged).
            price_paths: Dict of ticker -> price path array.
            dt: Time step size.
        """
        pass
