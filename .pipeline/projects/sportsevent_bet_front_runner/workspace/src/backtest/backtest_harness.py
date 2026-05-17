"""
Backtest harness for the Sports/Event Bet Front Runner Pipeline.

Simulates bet placement during latency gaps and calculates performance metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.pipeline.config import BacktestConfig
from src.pipeline.models import ProcessedSignal, SignalStats

logger = logging.getLogger(__name__)


@dataclass
class BetResult:
    """Represents the result of a simulated bet."""
    signal_id: str
    bet_amount: float
    odds: float
    commission: float
    is_win: bool
    net_profit: float
    timestamp: float


@dataclass
class BacktestResult:
    """Results of a backtest run."""
    total_bets: int = 0
    wins: int = 0
    losses: int = 0
    initial_bankroll: float = 0.0
    final_bankroll: float = 0.0
    roi: float = 0.0
    win_rate: float = 0.0
    avg_odds: float = 0.0
    total_commission_paid: float = 0.0
    bet_results: list[BetResult] = field(default_factory=list)
    stats: SignalStats = field(default_factory=SignalStats)

    @property
    def profit(self) -> float:
        """Calculate total profit."""
        return self.final_bankroll - self.initial_bankroll

    def summary(self) -> dict[str, Any]:
        """Generate a summary of the backtest results."""
        return {
            "total_bets": self.total_bets,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.win_rate,
            "roi": self.roi,
            "profit": self.profit,
            "initial_bankroll": self.initial_bankroll,
            "final_bankroll": self.final_bankroll,
            "avg_odds": self.avg_odds,
            "total_commission_paid": self.total_commission_paid,
        }


class BacktestHarness:
    """Harness for backtesting the pipeline's betting strategy."""

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.bankroll = self.config.initial_bankroll
        self.results = BacktestResult(
            initial_bankroll=self.config.initial_bankroll,
            stats=SignalStats(),
        )

    def process_signal(self, processed: ProcessedSignal) -> BetResult | None:
        """Process a signal and simulate a bet if appropriate."""
        if processed.action != "bet":
            self.results.stats.update(processed)
            return None

        # Check if we have enough bankroll
        if self.bankroll < self.config.bet_amount:
            logger.warning("Insufficient bankroll for bet")
            return None

        # Simulate bet outcome (50/50 for simplicity)
        import random
        is_win = random.random() > 0.5

        commission = self.config.bet_amount * self.config.commission_rate
        if is_win:
            net_profit = (self.config.bet_amount * self.config.odds) - self.config.bet_amount - commission
        else:
            net_profit = -self.config.bet_amount - commission

        self.bankroll += net_profit

        bet_result = BetResult(
            signal_id=processed.signal.signal_id,
            bet_amount=self.config.bet_amount,
            odds=self.config.odds,
            commission=commission,
            is_win=is_win,
            net_profit=net_profit,
            timestamp=processed.processed_at,
        )

        self.results.bet_results.append(bet_result)
        self.results.total_bets += 1
        if is_win:
            self.results.wins += 1
        else:
            self.results.losses += 1
        self.results.total_commission_paid += commission
        self.results.avg_odds = (
            self.results.avg_odds * (self.results.total_bets - 1) + self.config.odds
        ) / self.results.total_bets

        self.results.roi = (self.bankroll - self.config.initial_bankroll) / self.config.initial_bankroll
        self.results.win_rate = self.results.wins / self.results.total_bets if self.results.total_bets > 0 else 0.0
        self.results.final_bankroll = self.bankroll

        self.results.stats.update(processed)

        logger.info(
            f"Bet result: {'WIN' if is_win else 'LOSS'}, "
            f"profit={net_profit:.2f}, bankroll={self.bankroll:.2f}"
        )

        return bet_result

    def run_backtest(self, signals: list[ProcessedSignal]) -> BacktestResult:
        """Run a backtest with a list of processed signals."""
        for signal in signals[: self.config.max_bets]:
            self.process_signal(signal)

        logger.info(f"Backtest complete: {self.results.summary()}")
        return self.results
