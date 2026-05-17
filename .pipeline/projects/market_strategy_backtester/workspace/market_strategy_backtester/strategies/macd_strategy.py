"""MACD Crossover strategy.

Generates signals based on MACD (Moving Average Convergence Divergence) line
crossing the signal line.
No look-ahead bias: uses .shift() to ensure signals are based on past data only.
"""

import pandas as pd

from market_strategy_backtester.strategies.base import Strategy


class MACDStrategy(Strategy):
    """MACD crossover strategy.

    Generates a buy signal (1) when the MACD line crosses above the signal line,
    and a sell signal (0) when the MACD line crosses below the signal line.

    Attributes:
        fast_period: Fast EMA period (default: 12).
        slow_period: Slow EMA period (default: 26).
        signal_period: Signal line EMA period (default: 9).
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")
        if signal_period >= fast_period:
            raise ValueError("signal_period must be less than fast_period")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def _compute_macd(self, prices: pd.Series):
        """Compute MACD line and signal line.

        Args:
            prices: Series of close prices.

        Returns:
            Tuple of (macd_line, signal_line) Series.
        """
        ema_fast = prices.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow_period, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        return macd_line, signal_line

    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on MACD crossover.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            DataFrame with columns [date, signal] where:
                - signal == 1 means buy (MACD crosses above signal)
                - signal == 0 means sell/hold (MACD crosses below signal)
        """
        macd_line, signal_line = self._compute_macd(price_data["close"])

        # Initialize signals: 0 = hold/sell
        signals = pd.DataFrame({
            "date": price_data["date"],
            "signal": 0,
        })

        # Buy signal: MACD crosses above signal line
        macd_above = macd_line > signal_line
        macd_prev_below = macd_line.shift(1) <= signal_line
        buy_mask = macd_above & macd_prev_below

        # Sell signal: MACD crosses below signal line
        macd_below = macd_line < signal_line
        macd_prev_above = macd_line.shift(1) >= signal_line
        sell_mask = macd_below & macd_prev_above

        # Set signals: 1 for buy, 0 for sell/hold
        signals.loc[buy_mask, "signal"] = 1
        signals.loc[sell_mask, "signal"] = 0

        return signals
