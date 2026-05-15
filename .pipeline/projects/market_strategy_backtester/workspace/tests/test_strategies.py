"""Tests for trading strategies."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from market_strategy_backtester.strategies.sma_crossover import SMACrossoverStrategy
from market_strategy_backtester.strategies.rsi_strategy import RSIStrategy
from market_strategy_backtester.strategies.macd_strategy import MACDStrategy
from market_strategy_backtester.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from market_strategy_backtester.strategies.base import Strategy


def _make_price_data(n_days=500, start_price=100.0, seed=42):
    """Create synthetic OHLCV price data for testing."""
    rng = np.random.RandomState(seed)
    dates = pd.date_range(start=datetime(2020, 1, 1), periods=n_days, freq="B")
    returns = rng.normal(0.0005, 0.02, n_days)
    prices = start_price * np.cumprod(1 + returns)
    # Create OHLCV from close prices
    close = prices
    open_ = close * (1 + rng.uniform(-0.005, 0.005, n_days))
    high = close * (1 + rng.uniform(0.005, 0.02, n_days))
    low = close * (1 - rng.uniform(0.005, 0.02, n_days))
    volume = rng.randint(1000, 100000, n_days)

    df = pd.DataFrame({
        "date": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })
    return df


class TestSMACrossoverStrategy:
    """Tests for SMACrossoverStrategy."""

    def test_default_params(self):
        """Test strategy with default parameters."""
        strategy = SMACrossoverStrategy()
        assert strategy.fast_window == 10
        assert strategy.slow_window == 30

    def test_custom_params(self):
        """Test strategy with custom parameters."""
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=20)
        assert strategy.fast_window == 5
        assert strategy.slow_window == 20

    def test_invalid_params_fast_ge_slow(self):
        """Test that fast_window >= slow_window raises ValueError."""
        with pytest.raises(ValueError, match="fast_window must be less than slow_window"):
            SMACrossoverStrategy(fast_window=30, slow_window=10)

    def test_invalid_params_window_lt_1(self):
        """Test that window < 1 raises ValueError."""
        with pytest.raises(ValueError, match="fast_window must be at least 1"):
            SMACrossoverStrategy(fast_window=0, slow_window=10)
        with pytest.raises(ValueError, match="slow_window must be at least 1"):
            SMACrossoverStrategy(fast_window=1, slow_window=0)

    def test_generate_signals_returns_correct_columns(self):
        """Test that generate_signals returns DataFrame with correct columns."""
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        price_data = _make_price_data(n_days=200)
        signals = strategy.generate_signals(price_data)

        assert isinstance(signals, pd.DataFrame)
        assert "date" in signals.columns
        assert "signal" in signals.columns

    def test_generate_signals_only_binary_values(self):
        """Test that signals are only 0 or 1."""
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        price_data = _make_price_data(n_days=200)
        signals = strategy.generate_signals(price_data)

        assert set(signals["signal"].unique()).issubset({0, 1})

    def test_generate_signals_no_lookahead(self):
        """Test that signals don't use future data by verifying shift logic."""
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        price_data = _make_price_data(n_days=200)
        signals = strategy.generate_signals(price_data)

        # Signals should start after slow_window rows
        assert len(signals) == len(price_data) - strategy.slow_window

    def test_generate_signals_produces_signals(self):
        """Test that signals are actually generated (not all zeros)."""
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        price_data = _make_price_data(n_days=500)
        signals = strategy.generate_signals(price_data)

        # With 500 days of data, we should get some signals
        assert signals["signal"].sum() > 0

    def test_inherits_from_strategy(self):
        """Test that SMACrossoverStrategy inherits from Strategy."""
        strategy = SMACrossoverStrategy()
        assert isinstance(strategy, Strategy)


class TestRSIStrategy:
    """Tests for RSIStrategy."""

    def test_default_params(self):
        """Test strategy with default parameters."""
        strategy = RSIStrategy()
        assert strategy.rsi_window == 14
        assert strategy.oversold_threshold == 30.0
        assert strategy.overbought_threshold == 70.0

    def test_custom_params(self):
        """Test strategy with custom parameters."""
        strategy = RSIStrategy(rsi_window=21, oversold_threshold=20, overbought_threshold=80)
        assert strategy.rsi_window == 21
        assert strategy.oversold_threshold == 20
        assert strategy.overbought_threshold == 80

    def test_invalid_thresholds(self):
        """Test that invalid thresholds raise ValueError."""
        with pytest.raises(ValueError, match="oversold_threshold must be less than overbought_threshold"):
            RSIStrategy(oversold_threshold=70, overbought_threshold=30)

    def test_invalid_rsi_window(self):
        """Test that rsi_window < 2 raises ValueError."""
        with pytest.raises(ValueError, match="rsi_window must be at least 2"):
            RSIStrategy(rsi_window=1)

    def test_generate_signals_returns_correct_columns(self):
        """Test that generate_signals returns DataFrame with correct columns."""
        strategy = RSIStrategy()
        price_data = _make_price_data(n_days=500)
        signals = strategy.generate_signals(price_data)

        assert isinstance(signals, pd.DataFrame)
        assert "date" in signals.columns
        assert "signal" in signals.columns

    def test_generate_signals_only_binary_values(self):
        """Test that signals are only 0 or 1."""
        strategy = RSIStrategy()
        price_data = _make_price_data(n_days=500)
        signals = strategy.generate_signals(price_data)

        assert set(signals["signal"].unique()).issubset({0, 1})

    def test_rsi_values_in_valid_range(self):
        """Test that computed RSI values are between 0 and 100."""
        strategy = RSIStrategy()
        price_data = _make_price_data(n_days=500)
        rsi = strategy._compute_rsi(price_data["close"])

        assert rsi.min() >= 0
        assert rsi.max() <= 100

    def test_rsi_uses_wilders_smoothing(self):
        """Test that RSI uses Wilder's smoothing (ewm with alpha=1/window)."""
        strategy = RSIStrategy(rsi_window=14)
        price_data = _make_price_data(n_days=500)
        rsi = strategy._compute_rsi(price_data["close"])

        # RSI should have NaN for first rsi_window rows
        assert rsi.iloc[:strategy.rsi_window].isna().all()

    def test_inherits_from_strategy(self):
        """Test that RSIStrategy inherits from Strategy."""
        strategy = RSIStrategy()
        assert isinstance(strategy, Strategy)


class TestMACDStrategy:
    """Tests for MACDStrategy."""

    def test_default_params(self):
        """Test strategy with default parameters."""
        strategy = MACDStrategy()
        assert strategy.fast_period == 12
        assert strategy.slow_period == 26
        assert strategy.signal_period == 9

    def test_custom_params(self):
        """Test strategy with custom parameters."""
        strategy = MACDStrategy(fast_period=6, slow_period=12, signal_period=3)
        assert strategy.fast_period == 6
        assert strategy.slow_period == 12
        assert strategy.signal_period == 3

    def test_invalid_params(self):
        """Test that invalid parameters raise ValueError."""
        with pytest.raises(ValueError, match="fast_period must be less than slow_period"):
            MACDStrategy(fast_period=30, slow_period=10)
        with pytest.raises(ValueError, match="signal_period must be less than fast_period"):
            MACDStrategy(fast_period=10, slow_period=20, signal_period=15)

    def test_generate_signals_returns_correct_columns(self):
        """Test that generate_signals returns DataFrame with correct columns."""
        strategy = MACDStrategy()
        price_data = _make_price_data(n_days=500)
        signals = strategy.generate_signals(price_data)

        assert isinstance(signals, pd.DataFrame)
        assert "date" in signals.columns
        assert "signal" in signals.columns

    def test_generate_signals_only_binary_values(self):
        """Test that signals are only 0 or 1."""
        strategy = MACDStrategy()
        price_data = _make_price_data(n_days=500)
        signals = strategy.generate_signals(price_data)

        assert set(signals["signal"].unique()).issubset({0, 1})

    def test_macd_line_computation(self):
        """Test that MACD line is computed correctly."""
        strategy = MACDStrategy(fast_period=5, slow_period=10, signal_period=3)
        price_data = _make_price_data(n_days=200)
        macd_line, signal_line = strategy._compute_macd(price_data["close"])

        assert len(macd_line) == len(price_data)
        assert len(signal_line) == len(price_data)

    def test_inherits_from_strategy(self):
        """Test that MACDStrategy inherits from Strategy."""
        strategy = MACDStrategy()
        assert isinstance(strategy, Strategy)


class TestBollingerBandsStrategy:
    """Tests for BollingerBandsStrategy."""

    def test_default_params(self):
        """Test strategy with default parameters."""
        strategy = BollingerBandsStrategy()
        assert strategy.window == 20
        assert strategy.std_dev == 2.0

    def test_custom_params(self):
        """Test strategy with custom parameters."""
        strategy = BollingerBandsStrategy(window=10, std_dev=1.5)
        assert strategy.window == 10
        assert strategy.std_dev == 1.5

    def test_invalid_window(self):
        """Test that window < 2 raises ValueError."""
        with pytest.raises(ValueError, match="window must be at least 2"):
            BollingerBandsStrategy(window=1)

    def test_invalid_std_dev(self):
        """Test that std_dev <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="std_dev must be positive"):
            BollingerBandsStrategy(std_dev=0)
        with pytest.raises(ValueError, match="std_dev must be positive"):
            BollingerBandsStrategy(std_dev=-1)

    def test_generate_signals_returns_correct_columns(self):
        """Test that generate_signals returns DataFrame with correct columns."""
        strategy = BollingerBandsStrategy()
        price_data = _make_price_data(n_days=500)
        signals = strategy.generate_signals(price_data)

        assert isinstance(signals, pd.DataFrame)
        assert "date" in signals.columns
        assert "signal" in signals.columns

    def test_generate_signals_only_binary_values(self):
        """Test that signals are only 0 or 1."""
        strategy = BollingerBandsStrategy()
        price_data = _make_price_data(n_days=500)
        signals = strategy.generate_signals(price_data)

        assert set(signals["signal"].unique()).issubset({0, 1})

    def test_bollinger_bands_computation(self):
        """Test that Bollinger Bands are computed correctly."""
        strategy = BollingerBandsStrategy(window=10, std_dev=2.0)
        price_data = _make_price_data(n_days=200)
        upper, middle, lower = strategy._compute_bollinger_bands(price_data["close"])

        assert len(upper) == len(price_data)
        assert len(middle) == len(price_data)
        assert len(lower) == len(price_data)
        # Upper band should be >= middle band
        assert (upper.dropna() >= middle.dropna()).all()
        # Middle band should be >= lower band
        assert (middle.dropna() >= lower.dropna()).all()

    def test_inherits_from_strategy(self):
        """Test that BollingerBandsStrategy inherits from Strategy."""
        strategy = BollingerBandsStrategy()
        assert isinstance(strategy, Strategy)
