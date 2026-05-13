"""Tests for the backtester engine."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.strategies.sma_crossover import SMACrossoverStrategy
from market_strategy_backtester.strategies.rsi_strategy import RSIStrategy


def _make_price_data(n_days=500, start_price=100.0, seed=42):
    """Create synthetic OHLCV price data for testing."""
    rng = np.random.RandomState(seed)
    dates = pd.date_range(start=datetime(2020, 1, 1), periods=n_days, freq="B")
    returns = rng.normal(0.0005, 0.02, n_days)
    prices = start_price * np.cumprod(1 + returns)
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


class TestBacktester:
    """Tests for Backtester class."""

    def test_default_initialization(self):
        """Test Backtester with default parameters."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)

        assert backtester.strategy == strategy
        assert backtester.initial_capital == 100000.0
        assert backtester.commission_pct == 0.001
        assert backtester.slippage_pct == 0.0005
        assert backtester.risk_free_rate == 0.02

    def test_custom_initialization(self):
        """Test Backtester with custom parameters."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(
            strategy=strategy,
            initial_capital=50000.0,
            commission_pct=0.002,
            slippage_pct=0.001,
            risk_free_rate=0.03,
        )

        assert backtester.initial_capital == 50000.0
        assert backtester.commission_pct == 0.002
        assert backtester.slippage_pct == 0.001
        assert backtester.risk_free_rate == 0.03

    def test_run_backtest_returns_correct_type(self):
        """Test that run_backtest returns a DataFrame."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)

    def test_run_backtest_has_required_columns(self):
        """Test that run_backtest returns DataFrame with required columns."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(price_data)

        required_columns = ["date", "equity", "position", "cash", "trades"]
        for col in required_columns:
            assert col in result.columns

    def test_run_backtest_equity_starts_at_initial_capital(self):
        """Test that equity starts at initial capital."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy, initial_capital=100000.0)
        result = backtester.run_backtest(price_data)

        assert result["equity"].iloc[0] == 100000.0

    def test_run_backtest_equity_changes_over_time(self):
        """Test that equity changes over time (not constant)."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(price_data)

        # Equity should not be constant
        assert result["equity"].nunique() > 1

    def test_run_backtest_position_is_binary(self):
        """Test that position values are 0 or 1."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(price_data)

        assert set(result["position"].unique()).issubset({0, 1})

    def test_run_backtest_with_rsi_strategy(self):
        """Test backtest with RSI strategy."""
        price_data = _make_price_data(n_days=500)
        strategy = RSIStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_run_backtest_with_different_initial_capital(self):
        """Test that different initial capital affects equity."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()

        backtester1 = Backtester(strategy=strategy, initial_capital=100000.0)
        result1 = backtester1.run_backtest(price_data)

        backtester2 = Backtester(strategy=strategy, initial_capital=200000.0)
        result2 = backtester2.run_backtest(price_data)

        # Final equity should be roughly double
        assert abs(result2["equity"].iloc[-1] - 2 * result1["equity"].iloc[-1]) < 1000

    def test_run_backtest_with_zero_commission(self):
        """Test backtest with zero commission."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy, commission_pct=0.0)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_run_backtest_with_high_commission(self):
        """Test backtest with high commission."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy, commission_pct=0.01)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_run_backtest_with_slippage(self):
        """Test backtest with slippage."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy, slippage_pct=0.005)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_run_backtest_with_high_risk_free_rate(self):
        """Test backtest with high risk-free rate."""
        price_data = _make_price_data(n_days=500)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy, risk_free_rate=0.10)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_run_backtest_short_data(self):
        """Test backtest with short data (minimum length)."""
        price_data = _make_price_data(n_days=50)
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_run_backtest_long_data(self):
        """Test backtest with long data."""
        price_data = _make_price_data(n_days=2000)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2000

    def test_run_backtest_reproducible(self):
        """Test that backtest is reproducible with same seed."""
        price_data = _make_price_data(n_days=500, seed=42)
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result1 = backtester.run_backtest(price_data)

        price_data2 = _make_price_data(n_days=500, seed=42)
        result2 = backtester.run_backtest(price_data2)

        pd.testing.assert_frame_equal(result1, result2)

    def test_run_backtest_different_seeds_different_results(self):
        """Test that different seeds produce different results."""
        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)

        price_data1 = _make_price_data(n_days=500, seed=42)
        result1 = backtester.run_backtest(price_data1)

        price_data2 = _make_price_data(n_days=500, seed=123)
        result2 = backtester.run_backtest(price_data2)

        # Results should be different
        assert not result1["equity"].equals(result2["equity"])

    def test_run_backtest_no_trades_possible(self):
        """Test backtest when no trades are possible (flat price)."""
        rng = np.random.RandomState(42)
        dates = pd.date_range(start=datetime(2020, 1, 1), periods=500, freq="B")
        close = np.full(500, 100.0)
        open_ = np.full(500, 100.0)
        high = np.full(500, 100.0)
        low = np.full(500, 100.0)
        volume = rng.randint(1000, 100000, 500)

        df = pd.DataFrame({
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })

        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 500

    def test_run_backtest_with_large_price_jumps(self):
        """Test backtest with large price jumps."""
        price_data = _make_price_data(n_days=500)
        # Add a large jump
        price_data.loc[100, "close"] = price_data.loc[100, "close"] * 2
        price_data.loc[100, "high"] = price_data.loc[100, "close"]
        price_data.loc[100, "low"] = price_data.loc[100, "close"] * 0.5

        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(price_data)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 500

    def test_run_backtest_with_negative_returns(self):
        """Test backtest with consistently negative returns."""
        rng = np.random.RandomState(42)
        dates = pd.date_range(start=datetime(2020, 1, 1), periods=500, freq="B")
        returns = rng.normal(-0.001, 0.02, 500)
        prices = 100.0 * np.cumprod(1 + returns)
        close = prices
        open_ = close * (1 + rng.uniform(-0.005, 0.005, 500))
        high = close * (1 + rng.uniform(0.005, 0.02, 500))
        low = close * (1 - rng.uniform(0.005, 0.02, 500))
        volume = rng.randint(1000, 100000, 500)

        df = pd.DataFrame({
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })

        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 500
        # Equity should be less than initial capital
        assert result["equity"].iloc[-1] < 100000.0

    def test_run_backtest_with_positive_returns(self):
        """Test backtest with consistently positive returns."""
        rng = np.random.RandomState(42)
        dates = pd.date_range(start=datetime(2020, 1, 1), periods=500, freq="B")
        returns = rng.normal(0.001, 0.02, 500)
        prices = 100.0 * np.cumprod(1 + returns)
        close = prices
        open_ = close * (1 + rng.uniform(-0.005, 0.005, 500))
        high = close * (1 + rng.uniform(0.005, 0.02, 500))
        low = close * (1 - rng.uniform(0.005, 0.02, 500))
        volume = rng.randint(1000, 100000, 500)

        df = pd.DataFrame({
            "date": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })

        strategy = SMACrossoverStrategy()
        backtester = Backtester(strategy=strategy)
        result = backtester.run_backtest(df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 500
        # Equity should be greater than initial capital (on average)
        assert result["equity"].iloc[-1] > 100000.0
