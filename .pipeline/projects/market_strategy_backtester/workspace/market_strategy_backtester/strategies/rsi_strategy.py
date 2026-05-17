"""RSI (Relative Strength Index) strategy.

Generates signals based on RSI overbought/oversold levels.
No look-ahead bias: uses .shift() to ensure signals are based on past data only.
"""

import numpy as np
import pandas as pd

from market_strategy_backtester.strategies.base import Strategy


class RSIStrategy(Strategy):
    """RSI-based mean-reversion strategy.

    Generates a buy signal (1) when RSI crosses below the oversold threshold,
    and a sell signal (0) when RSI crosses above the overbought threshold.

    Attributes:
        rsi_window: Period for RSI calculation (default: 14).
        oversold_threshold: RSI level below which we consider oversold (default: 30).
        overbought_threshold: RSI level above which we consider overbought (default: 70).
    """

    def __init__(
        self,
        rsi_window: int = 14,
        oversold_threshold: float = 30.0,
        overbought_threshold: float = 70.0,
    ):
        if oversold_threshold >= overbought_threshold:
            raise ValueError("oversold_threshold must be less than overbought_threshold")
        if rsi_window < 2:
            raise ValueError("rsi_window must be at least 2")
        self.rsi_window = rsi_window
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

    def _compute_rsi(self, prices: pd.Series) -> pd.Series:
        """Compute RSI from price series."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        # Wilder's smoothing (smoothed moving average)
        avg_gain = gain.ewm(alpha=1 / self.rsi_window, min_periods=self.rsi_window).mean()
        avg_loss = loss.ewm(alpha=1 / self.rsi_window, min_periods=self.rsi_window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        # Ensure first rsi_window rows are NaN (Wilders smoothing needs min_periods)
        rsi.iloc[:self.rsi_window] = np.nan
        return rsi

    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on RSI.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            DataFrame with columns [date, signal] where:
                - signal == 1 means buy
                - signal == 0 means sell/hold
        """
        rsi = self._compute_rsi(price_data["close"])

        # Initialize signals: 0 = hold/sell
        signals = pd.DataFrame({"date": price_data["date"], "signal": 0})

        # Buy signal: RSI crosses below oversold threshold
        # We use shift(1) to ensure no look-ahead bias
        rsi_below = rsi < self.oversold_threshold
        rsi_prev_above = rsi.shift(1) >= self.oversold_threshold
        buy_mask = rsi_below & rsi_prev_above

        # Sell signal: RSI crosses above overbought threshold
        rsi_above = rsi > self.overbought_threshold
        rsi_prev_below = rsi.shift(1) <= self.overbought_threshold
        sell_mask = rsi_above & rsi_prev_below

        signals.loc[buy_mask, "signal"] = 1
        signals.loc[sell_mask, "signal"] = 0

        # Drop rows where RSI is not yet computed (first rsi_window rows)
        signals = signals.iloc[self.rsi_window:]

        return signals.reset_index(drop=True)
