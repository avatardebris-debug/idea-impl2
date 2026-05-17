"""Market data models and LMSR (Logarithmic Market Scoring Rule) market maker.

Provides:
    - MarketOrder: Represents a buy/sell order.
    - MarketState: Tracks current market state (shares, prices).
    - LMSRMarketMaker: Implements the LMSR market maker with configurable spread costs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OrderSide(Enum):
    """Direction of a market order."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class MarketOrder:
    """Represents a buy or sell order.

    Attributes:
        side: Buy or sell.
        shares: Number of shares to trade.
        price: Limit price (optional).
    """
    side: OrderSide
    shares: float
    price: Optional[float] = None

    def __post_init__(self):
        if self.shares <= 0:
            raise ValueError("shares must be positive")


@dataclass
class MarketState:
    """Current state of a prediction market.

    Attributes:
        name: Market name/identifier.
        outcome_a_shares: Shares held for outcome A.
        outcome_b_shares: Shares held for outcome B.
        initial_price_a: Initial price for outcome A.
        initial_price_b: Initial price for outcome B.
    """
    name: str
    outcome_a_shares: float = 0.0
    outcome_b_shares: float = 0.0
    initial_price_a: float = 0.5
    initial_price_b: float = 0.5

    @property
    def total_shares(self) -> float:
        """Total shares outstanding."""
        return self.outcome_a_shares + self.outcome_b_shares

    @property
    def implied_probability_a(self) -> float:
        """Implied probability of outcome A from current shares."""
        total = self.total_shares
        if total == 0:
            return self.initial_price_a
        return self.outcome_a_shares / total

    @property
    def implied_probability_b(self) -> float:
        """Implied probability of outcome B from current shares."""
        total = self.total_shares
        if total == 0:
            return self.initial_price_b
        return self.outcome_b_shares / total


class LMSRMarketMaker:
    """Logarithmic Market Scoring Rule (LMSR) market maker.

    The LMSR market maker provides continuous liquidity by quoting prices
    based on the number of shares held. The cost function is:

        C(q) = b * m * ln(sum(exp(q_i / b)))

    where:
        b: liquidity parameter (larger b = tighter spreads)
        m: number of outcomes
        q: vector of shares held for each outcome

    Attributes:
        liquidity: Liquidity parameter b (controls spread width).
        spread_cost: Additional spread cost multiplier.
        state: Current market state.
    """

    def __init__(
        self,
        state: MarketState,
        liquidity: float = 1000.0,
        spread_cost: float = 0.0,
    ):
        """Initialize the LMSR market maker.

        Args:
            state: Initial market state.
            liquidity: Liquidity parameter b. Larger values mean tighter spreads.
            spread_cost: Additional spread cost multiplier (0.0 to 1.0).
        """
        if liquidity <= 0:
            raise ValueError("liquidity must be positive")
        if spread_cost < 0 or spread_cost >= 1:
            raise ValueError("spread_cost must be in [0, 1)")

        self.liquidity = liquidity
        self.spread_cost = spread_cost
        self.state = state
        self._trade_log: list[dict] = []

    def _cost_function(self, shares_a: float, shares_b: float) -> float:
        """Compute the LMSR cost function for a given share configuration.

        Args:
            shares_a: Shares for outcome A.
            shares_b: Shares for outcome B.

        Returns:
            Cost to acquire the given shares.
        """
        m = 2  # two outcomes
        b = self.liquidity
        term_a = math.exp(shares_a / b)
        term_b = math.exp(shares_b / b)
        return b * m * math.log(term_a + term_b)

    def _marginal_price_a(self) -> float:
        """Compute the marginal price for outcome A."""
        b = self.liquidity
        q_a = self.state.outcome_a_shares
        q_b = self.state.outcome_b_shares
        term_a = math.exp(q_a / b)
        term_b = math.exp(q_b / b)
        price_a = term_a / (term_a + term_b)
        return price_a

    def _marginal_price_b(self) -> float:
        """Compute the marginal price for outcome B."""
        b = self.liquidity
        q_a = self.state.outcome_a_shares
        q_b = self.state.outcome_b_shares
        term_a = math.exp(q_a / b)
        term_b = math.exp(q_b / b)
        price_b = term_b / (term_a + term_b)
        return price_b

    def get_bid_ask_spread(self) -> tuple[float, float]:
        """Get the current bid-ask spread for outcome A.

        Returns:
            Tuple of (bid_price, ask_price) for outcome A.
        """
        base_price = self._marginal_price_a()
        half_spread = self.spread_cost * base_price
        bid = max(0.0, base_price - half_spread)
        ask = min(1.0, base_price + half_spread)
        return (bid, ask)

    def get_price(self, side: OrderSide) -> float:
        """Get the current price for a given order side.

        Args:
            side: BUY or SELL.

        Returns:
            Price for the given side.
        """
        if side == OrderSide.BUY:
            return self._marginal_price_a()
        else:
            return self._marginal_price_b()

    def submit_order(self, order: MarketOrder) -> dict:
        """Submit an order and update the market state.

        Args:
            order: The order to submit.

        Returns:
            Dict with trade details: price, cost, new state.
        """
        if order.side == OrderSide.BUY:
            # Buying outcome A: increase outcome_a_shares
            old_cost = self._cost_function(
                self.state.outcome_a_shares,
                self.state.outcome_b_shares,
            )
            new_cost = self._cost_function(
                self.state.outcome_a_shares + order.shares,
                self.state.outcome_b_shares,
            )
            cost = new_cost - old_cost
            self.state.outcome_a_shares += order.shares
            execution_price = cost / order.shares if order.shares > 0 else 0.0
        else:
            # Selling outcome A: decrease outcome_a_shares
            old_cost = self._cost_function(
                self.state.outcome_a_shares,
                self.state.outcome_b_shares,
            )
            new_cost = self._cost_function(
                self.state.outcome_a_shares - order.shares,
                self.state.outcome_b_shares,
            )
            cost = new_cost - old_cost
            self.state.outcome_a_shares -= order.shares
            execution_price = cost / order.shares if order.shares > 0 else 0.0

        # Apply spread cost
        if self.spread_cost > 0:
            spread_adjustment = execution_price * self.spread_cost
            if order.side == OrderSide.BUY:
                execution_price += spread_adjustment
            else:
                execution_price -= spread_adjustment
            execution_price = max(0.0, min(1.0, execution_price))

        trade = {
            "side": order.side.value,
            "shares": order.shares,
            "price": execution_price,
            "cost": cost,
            "state": MarketState(
                name=self.state.name,
                outcome_a_shares=self.state.outcome_a_shares,
                outcome_b_shares=self.state.outcome_b_shares,
                initial_price_a=self.state.initial_price_a,
                initial_price_b=self.state.initial_price_b,
            ),
        }
        self._trade_log.append(trade)
        return trade

    def get_current_prices(self) -> dict:
        """Get current implied probabilities for both outcomes.

        Returns:
            Dict with 'price_a' and 'price_b'.
        """
        return {
            "price_a": self._marginal_price_a(),
            "price_b": self._marginal_price_b(),
        }

    def get_trade_log(self) -> list[dict]:
        """Return the trade log."""
        return list(self._trade_log)
