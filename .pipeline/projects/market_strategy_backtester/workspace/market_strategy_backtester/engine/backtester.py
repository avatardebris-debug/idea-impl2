"""Core backtester engine.

Applies a strategy to price data and produces per-trade returns and an equity curve.
"""

import numpy as np
import pandas as pd

from market_strategy_backtester.strategies.base import Strategy


class Backtester:
    """Backtesting engine that applies a strategy to price data.

    Attributes:
        strategy: A Strategy instance with a `generate_signals` method.
        risk_free_rate: Annual risk-free rate for Sharpe calculation (default: 0.02).
    """

    def __init__(self, strategy: Strategy, risk_free_rate: float = 0.02):
        self.strategy = strategy
        self.risk_free_rate = risk_free_rate

    def run(self, price_data: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """Run the backtest.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            Tuple of (equity_curve, per_trade_returns):
                - equity_curve: Series of cumulative equity values (starting at 1.0).
                - per_trade_returns: Series of per-trade return values.
        """
        # Generate signals
        signals = self.strategy.generate_signals(price_data)

        # Merge signals with price data
        merged = price_data[["date", "close"]].copy()
        merged = merged.merge(signals, on="date", how="left")
        merged["signal"] = merged["signal"].fillna(0)

        # Compute daily returns
        merged["daily_return"] = merged["close"].pct_change()

        # Compute strategy returns (position * daily return)
        # Shift signal by 1 so we trade on the next day after the signal
        merged["strategy_return"] = merged["signal"].shift(1) * merged["daily_return"]

        # Drop NaN rows from shift
        merged.dropna(subset=["strategy_return"], inplace=True)

        # Compute equity curve (starting at 1.0)
        equity_curve = (1 + merged["strategy_return"]).cumprod()

        # Compute per-trade returns (non-zero strategy returns)
        trades = merged[merged["strategy_return"] != 0]
        per_trade_returns = trades["strategy_return"].reset_index(drop=True)

        return equity_curve, per_trade_returns
