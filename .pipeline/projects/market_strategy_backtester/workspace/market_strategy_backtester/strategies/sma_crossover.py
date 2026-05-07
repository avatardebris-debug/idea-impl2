"""SMA Crossover strategy.

Generates signals based on fast and slow Simple Moving Average crossovers.
No look-ahead bias: uses .shift() to ensure signals are based on past data only.
"""

import pandas as pd

from market_strategy_backtester.strategies.base import Strategy


class SMACrossoverStrategy(Strategy):
    """Simple Moving Average crossover strategy.

    Generates a buy signal (1) when the fast SMA crosses above the slow SMA,
    and a sell signal (0) when the fast SMA crosses below the slow SMA.

    Attributes:
        fast_window: Period for the fast SMA (default: 10).
        slow_window: Period for the slow SMA (default: 30).
    """

    def __init__(self, fast_window: int = 10, slow_window: int = 30):
        if fast_window >= slow_window:
            raise ValueError("fast_window must be less than slow_window")
        self.fast_window = fast_window
        self.slow_window = slow_window

    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from price data.

        Uses only shifted data to avoid look-ahead bias.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            DataFrame with columns [date, signal] where signal is 1 (buy) or 0 (sell).
        """
        df = price_data[["date", "close"]].copy()

        # Compute SMAs (no shift on SMA computation — they use past data)
        df["fast_sma"] = df["close"].rolling(window=self.fast_window).mean()
        df["slow_sma"] = df["close"].rolling(window=self.slow_window).mean()

        # Shift by 1 to avoid look-ahead bias: signal is based on previous day's data
        df["fast_sma"] = df["fast_sma"].shift(1)
        df["slow_sma"] = df["slow_sma"].shift(1)

        # Generate signals
        df["signal"] = 0
        df.loc[df["fast_sma"] > df["slow_sma"], "signal"] = 1

        # Drop intermediate columns
        result = df[["date", "signal"]].copy()

        return result
