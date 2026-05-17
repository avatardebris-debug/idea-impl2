"""RSI Reversal strategy.

Generates signals based on RSI (Relative Strength Index) overbought/oversold levels.
No look-ahead bias: uses .shift() to ensure signals are based on past data only.
"""

import pandas as pd

from market_strategy_backtester.strategies.base import Strategy


class RSIStrategy(Strategy):
    """RSI mean-reversion strategy.

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
        if rsi_window < 2:
            raise ValueError("rsi_window must be at least 2")
        if oversold_threshold >= overbought_threshold:
            raise ValueError("oversold_threshold must be less than overbought_threshold")
        self.rsi_window = rsi_window
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

    def _compute_rsi(self, prices: pd.Series) -> pd.Series:
        """Compute RSI using Wilder's smoothing (ewm with alpha=1/window).

        Args:
            prices: Series of close prices.

        Returns:
            Series of RSI values (0-100), with NaN for the first rsi_window rows.
        """
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)

        # Wilder's smoothing: exponential moving average with alpha = 1/window
        avg_gain = gain.ewm(alpha=1 / self.rsi_window, min_periods=self.rsi_window).mean()
        avg_loss = loss.ewm(alpha=1 / self.rsi_window, min_periods=self.rsi_window).mean()

        # RS = average gain / average loss
        rs = avg_gain / avg_loss

        # RSI = 100 - (100 / (1 + RS))
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on RSI.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            DataFrame with columns [date, signal] where:
                - signal == 1 means buy (oversold)
                - signal == 0 means sell/hold (overbought or neutral)
        """
        rsi = self._compute_rsi(price_data["close"])

        # Initialize signals: 0 = hold/sell
        signals = pd.DataFrame({
            "date": price_data["date"],
            "signal": 0,
        })

        # Buy signal: RSI crosses below oversold threshold
        rsi_below_oversold = rsi < self.oversold_threshold
        rsi_prev_above_oversold = rsi.shift(1) >= self.oversold_threshold
        buy_mask = rsi_below_oversold & rsi_prev_above_oversold

        # Sell signal: RSI crosses above overbought threshold
        rsi_above_overbought = rsi > self.overbought_threshold
        rsi_prev_below_overbought = rsi.shift(1) <= self.overbought_threshold
        sell_mask = rsi_above_overbought & rsi_prev_below_overbought

        # Set signals: 1 for buy, 0 for sell/hold
        signals.loc[buy_mask, "signal"] = 1
        signals.loc[sell_mask, "signal"] = 0

        return signals
