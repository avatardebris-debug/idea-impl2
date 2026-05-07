"""Base class for trading strategies."""

from abc import ABC, abstractmethod
import pandas as pd


class Strategy(ABC):
    """Abstract base class for trading strategies.

    Strategies generate buy/sell signals from price data.
    All implementations must override `generate_signals`.
    """

    @abstractmethod
    def generate_signals(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from price data.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.

        Returns:
            DataFrame with columns [date, signal] where:
                - signal == 1 means buy
                - signal == 0 means sell/hold
        """
        pass
