"""Bollinger Bands strategy.

Generates signals based on price position relative to Bollinger Bands.
No look-ahead bias: uses .shift() to ensure signals are based on past data only.
"""

import pandas as pd

from market_strategy_backtester.strategies.base import Strategy


class BollingerBandsStrategy(Strategy):
    """Bollinger Bands mean-reversion strategy.

    Generates a buy signal (1) when price touches or crosses below the lower band,
    and a sell signal (0) when price touches or crosses above the upper band.

    Attributes:
        window: Period for the moving average (default: 20).
        num_std: Number of standard deviations for the bands (default: 2.0).
    """

    def __init__(
        self,
        window: int = 20,
        std_dev: float = 2.0,
    ):
        if window < 2:
            raise ValueError("window must be at least 2")
        if std_dev <= 0:
            raise ValueError("std_dev must be positive")
        self.window = window
        self.std_dev = std_dev

    def _compute_bollinger_bands(self, prices: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Compute Bollinger Bands from price series.

        Returns:
            Tuple of (upper_band, middle_band, lower_band) Series.
        """
        middle_band = prices.rolling(window=self.window).mean()
        std = prices.rolling(window=self.window).std()
        upper_band = middle_band + self.std_dev * std
        lower_band = middle_band - self.std_dev * std
        return upper_band, middle_band, lower_band

    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals based on Bollinger Bands.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            DataFrame with columns [date, signal] where:
                - signal == 1 means buy
                - signal == 0 means sell/hold
        """
        upper_band, middle_band, lower_band = self._compute_bollinger_bands(price_data["close"])

        # Initialize signals: 0 = hold/sell
        signals = pd.DataFrame({"date": price_data["date"], "signal": 0})

        # Buy signal: price crosses below lower band
        price_below_lower = price_data["close"] < lower_band
        price_prev_above_lower = price_data["close"].shift(1) >= lower_band.shift(1)
        buy_mask = price_below_lower & price_prev_above_lower

        # Sell signal: price crosses above upper band
        price_above_upper = price_data["close"] > upper_band
        price_prev_below_upper = price_data["close"].shift(1) <= upper_band.shift(1)
        sell_mask = price_above_upper & price_prev_below_upper

        signals.loc[buy_mask, "signal"] = 1
        signals.loc[sell_mask, "signal"] = 0

        # Drop rows where bands are not yet computed
        signals = signals.iloc[self.window:]

        return signals.reset_index(drop=True)
