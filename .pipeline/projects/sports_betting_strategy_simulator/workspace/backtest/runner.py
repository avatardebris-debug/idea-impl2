"""Backtest runner that iterates through simulated bets and applies strategies."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from ..engine.market import Market
from ..engine.monte_carlo import MonteCarloEngine
from ..strategies.base import Strategy
from .bankroll import Bankroll


@dataclass
class BetRecord:
    """Record of a single bet in the backtest."""
    bet_index: int
    stake: float
    won: bool
    pnl: float
    bankroll_after: float
    market_odds_decimal: float
    true_probability: float


class BacktestRunner:
    """Runs a backtest by iterating through simulated bets.

    Applies a strategy to determine stake, resolves the outcome,
    and updates the bankroll. Records per-bet state.
    """

    def __init__(
        self,
        strategy: Strategy,
        market: Market,
        bankroll: Bankroll,
        n_bets: int = 1000,
        seed: int = 42,
    ):
        """Initialize the backtest runner.

        Args:
            strategy: Betting strategy to use.
            market: Market object defining the bet parameters.
            bankroll: Bankroll object to track.
            n_bets: Number of bets to simulate.
            seed: Random seed for reproducibility.
        """
        self.strategy = strategy
        self.market = market
        self.bankroll = bankroll
        self.n_bets = n_bets
        self.seed = seed
        self.records: list[BetRecord] = []

    def run(self) -> list[BetRecord]:
        """Run the backtest simulation.

        Returns:
            List of BetRecord objects with per-bet details.
        """
        engine = MonteCarloEngine(seed=self.seed)
        self.bankroll.reset()

        # Generate all outcomes at once using vectorized simulation
        # We'll use unit stakes for outcome generation, then scale by actual stakes
        stakes = np.zeros(self.n_bets)
        for i in range(self.n_bets):
            stake_fraction = self.strategy.stake_fraction(self.bankroll.current_bankroll, self.market)
            stake = stake_fraction * self.bankroll.current_bankroll
            stakes[i] = stake

        # Simulate outcomes
        wins, base_pnl = engine.simulate_with_custom_stakes(self.market, stakes)

        # Record each bet
        self.records = []
        for i in range(self.n_bets):
            won = bool(wins[i])
            pnl = float(base_pnl[i])
            self.bankroll.bet(stakes[i], won, self.market.payout_multiplier)

            record = BetRecord(
                bet_index=i,
                stake=float(stakes[i]),
                won=won,
                pnl=pnl,
                bankroll_after=self.bankroll.current_bankroll,
                market_odds_decimal=self.market.odds_decimal,
                true_probability=self.market.true_probability,
            )
            self.records.append(record)

        return self.records

    @property
    def final_bankroll(self) -> float:
        """Get the final bankroll after all bets."""
        return self.bankroll.current_bankroll

    @property
    def net_profit(self) -> float:
        """Get the net profit after all bets."""
        return self.bankroll.net_profit

    @property
    def total_return(self) -> float:
        """Get the total return ratio."""
        return self.bankroll.total_return
