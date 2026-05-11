"""Performance metrics computation for betting backtests.

Computes total return, ROI, win rate, max drawdown, Sharpe ratio, and final bankroll.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .runner import BetRecord


class MetricsCalculator:
    """Computes performance metrics from a sequence of bet results.

    Metrics computed:
        - total_return: (final_bankroll / initial_bankroll) - 1
        - roi: net_profit / total_wagered
        - win_rate: wins / total_bets
        - max_drawdown: maximum peak-to-trough decline
        - sharpe_ratio: annualized Sharpe ratio (assuming 1 bet per day)
        - final_bankroll: final bankroll amount
    """

    def __init__(self, records: list["BetRecord"], initial_bankroll: float):
        """Initialize the metrics calculator.

        Args:
            records: List of BetRecord objects from the backtest.
            initial_bankroll: Starting bankroll amount.
        """
        self.records = records
        self.initial_bankroll = initial_bankroll

    def compute(self) -> dict[str, float]:
        """Compute all performance metrics.

        Returns:
            Dictionary of metric names to values.
        """
        if not self.records:
            return {
                "total_return": 0.0,
                "roi": 0.0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "final_bankroll": self.initial_bankroll,
            }

        # Extract bankroll history
        bankroll_history = np.array([r.bankroll_after for r in self.records])
        final_bankroll = bankroll_history[-1]

        # Total return
        total_return = (final_bankroll / self.initial_bankroll) - 1.0

        # Net profit and total wagered
        net_profit = final_bankroll - self.initial_bankroll
        total_wagered = sum(r.stake for r in self.records)
        roi = net_profit / total_wagered if total_wagered > 0 else 0.0

        # Win rate
        wins = sum(1 for r in self.records if r.won)
        win_rate = wins / len(self.records)

        # Max drawdown
        max_drawdown = self._compute_max_drawdown(bankroll_history)

        # Sharpe ratio (annualized, assuming 1 bet per day)
        sharpe_ratio = self._compute_sharpe_ratio(bankroll_history)

        return {
            "total_return": total_return,
            "roi": roi,
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "final_bankroll": final_bankroll,
        }

    @staticmethod
    def _compute_max_drawdown(bankroll_history: np.ndarray) -> float:
        """Compute maximum drawdown from bankroll history.

        Args:
            bankroll_history: Array of bankroll values.

        Returns:
            Maximum drawdown as a positive fraction (e.g., 0.15 for 15% drawdown).
        """
        if len(bankroll_history) == 0:
            return 0.0

        peak = np.maximum.accumulate(bankroll_history)
        drawdown = (peak - bankroll_history) / peak
        return float(np.max(drawdown))

    @staticmethod
    def _compute_sharpe_ratio(bankroll_history: np.ndarray, risk_free_rate: float = 0.0) -> float:
        """Compute annualized Sharpe ratio from bankroll history.

        Assumes 1 bet per day, so 252 trading days per year.

        Args:
            bankroll_history: Array of bankroll values.
            risk_free_rate: Annualized risk-free rate (default 0).

        Returns:
            Annualized Sharpe ratio.
        """
        if len(bankroll_history) < 2:
            return 0.0

        # Compute daily returns
        daily_returns = np.diff(bankroll_history) / bankroll_history[:-1]

        # Annualize
        mean_daily_return = np.mean(daily_returns)
        std_daily_return = np.std(daily_returns, ddof=1)

        if std_daily_return == 0:
            return 0.0

        # Annualize: multiply by sqrt(252)
        sharpe = (mean_daily_return - risk_free_rate / 252) / std_daily_return * np.sqrt(252)
        return float(sharpe)
