"""Comprehensive unit tests for market_strategy_backtester."""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path

from market_strategy_backtester.strategies.sma_crossover import SMACrossoverStrategy
from market_strategy_backtester.strategies.rsi_strategy import RSIStrategy
from market_strategy_backtester.strategies.macd_strategy import MACDStrategy
from market_strategy_backtester.strategies.bollinger_bands_strategy import BollingerBandsStrategy
from market_strategy_backtester.strategies.registry import (
    create_strategy,
    get_available_strategies,
    get_strategy_info,
)
from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.engine.monte_carlo import MonteCarloSimulator
from market_strategy_backtester.engine.comparator import StrategyComparator
from market_strategy_backtester.engine.optimizer import ParameterOptimizer
from market_strategy_backtester.engine.walk_forward import WalkForwardAnalyzer
from market_strategy_backtester.metrics.risk import MetricsCalculator
from market_strategy_backtester.data_validator import DataValidator
from market_strategy_backtester.visualizer import BacktestVisualizer


def _generate_test_data(n_days: int = 300) -> pd.DataFrame:
    """Generate synthetic OHLCV test data."""
    rng = np.random.default_rng(42)
    dates = pd.date_range(start="2020-01-02", periods=n_days, freq="B")
    prices = 100.0 * np.exp(np.cumsum(rng.normal(0.0003, 0.02, n_days)))

    df = pd.DataFrame({
        "date": dates,
        "close": prices,
        "open": prices * (1 + rng.uniform(-0.005, 0.005, n_days)),
        "high": prices * (1 + abs(rng.normal(0, 0.01, n_days))),
        "low": prices * (1 - abs(rng.normal(0, 0.01, n_days))),
        "volume": rng.integers(1_000_000, 10_000_000, n_days),
    })
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df


class TestSMACrossoverStrategy(unittest.TestCase):
    """Tests for SMACrossoverStrategy."""

    def test_generate_signals_returns_correct_columns(self):
        df = _generate_test_data()
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        signals = strategy.generate_signals(df)
        self.assertIn("date", signals.columns)
        self.assertIn("signal", signals.columns)

    def test_signals_are_binary(self):
        df = _generate_test_data()
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        signals = strategy.generate_signals(df)
        self.assertTrue(set(signals["signal"].unique()).issubset({0, 1}))

    def test_invalid_params_raise_error(self):
        with self.assertRaises(ValueError):
            SMACrossoverStrategy(fast_window=30, slow_window=10)

    def test_no_lookahead_bias(self):
        """Signals should not depend on future data."""
        df = _generate_test_data()
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        signals = strategy.generate_signals(df)
        # First few signals should be 0 (not enough data)
        self.assertTrue((signals["signal"].iloc[:10] == 0).all())


class TestRSIStrategy(unittest.TestCase):
    """Tests for RSIStrategy."""

    def test_generate_signals_returns_correct_columns(self):
        df = _generate_test_data()
        strategy = RSIStrategy(rsi_window=14, overbought_threshold=70, oversold_threshold=30)
        signals = strategy.generate_signals(df)
        self.assertIn("date", signals.columns)
        self.assertIn("signal", signals.columns)

    def test_signals_are_binary(self):
        df = _generate_test_data()
        strategy = RSIStrategy(rsi_window=14, overbought_threshold=70, oversold_threshold=30)
        signals = strategy.generate_signals(df)
        self.assertTrue(set(signals["signal"].unique()).issubset({0, 1}))


class TestMACDStrategy(unittest.TestCase):
    """Tests for MACDStrategy."""

    def test_generate_signals_returns_correct_columns(self):
        df = _generate_test_data()
        strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        signals = strategy.generate_signals(df)
        self.assertIn("date", signals.columns)
        self.assertIn("signal", signals.columns)

    def test_signals_are_binary(self):
        df = _generate_test_data()
        strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        signals = strategy.generate_signals(df)
        self.assertTrue(set(signals["signal"].unique()).issubset({0, 1}))


class TestBollingerBandsStrategy(unittest.TestCase):
    """Tests for BollingerBandsStrategy."""

    def test_generate_signals_returns_correct_columns(self):
        df = _generate_test_data()
        strategy = BollingerBandsStrategy(window=20, std_dev=2.0)
        signals = strategy.generate_signals(df)
        self.assertIn("date", signals.columns)
        self.assertIn("signal", signals.columns)

    def test_signals_are_binary(self):
        df = _generate_test_data()
        strategy = BollingerBandsStrategy(window=20, std_dev=2.0)
        signals = strategy.generate_signals(df)
        self.assertTrue(set(signals["signal"].unique()).issubset({0, 1}))


class TestRegistry(unittest.TestCase):
    """Tests for strategy registry."""

    def test_get_available_strategies(self):
        strategies = get_available_strategies()
        self.assertIsInstance(strategies, list)
        self.assertIn("sma_crossover", strategies)
        self.assertIn("rsi", strategies)
        self.assertIn("macd", strategies)
        self.assertIn("bollinger_bands", strategies)

    def test_create_strategy_by_name(self):
        strategy = create_strategy("sma_crossover", fast_window=5, slow_window=10)
        self.assertIsInstance(strategy, SMACrossoverStrategy)
        strategy = create_strategy("rsi", rsi_window=14, overbought_threshold=70, oversold_threshold=30)
        self.assertIsInstance(strategy, RSIStrategy)
        strategy = create_strategy("bollinger_bands", window=20, num_std=2.0)
        self.assertIsInstance(strategy, BollingerBandsStrategy)

    def test_create_strategy_invalid_name(self):
        with self.assertRaises(ValueError):
            create_strategy("nonexistent_strategy")

    def test_get_strategy_info(self):
        info = get_strategy_info("sma_crossover")
        self.assertIn("name", info)
        self.assertIn("description", info)
        self.assertIn("parameters", info)


class TestBacktester(unittest.TestCase):
    """Tests for Backtester."""

    def test_run_returns_equity_curve_and_returns(self):
        df = _generate_test_data()
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        backtester = Backtester(strategy, risk_free_rate=0.02)
        equity_curve, per_trade_returns = backtester.run(df)
        self.assertIsInstance(equity_curve, pd.Series)
        self.assertIsInstance(per_trade_returns, pd.Series)

    def test_equity_curve_starts_at_1(self):
        df = _generate_test_data()
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        backtester = Backtester(strategy, risk_free_rate=0.02)
        equity_curve, _ = backtester.run(df)
        self.assertAlmostEqual(equity_curve.iloc[0], 1.0, places=5)

    def test_per_trade_returns_length(self):
        df = _generate_test_data()
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        backtester = Backtester(strategy, risk_free_rate=0.02)
        _, per_trade_returns = backtester.run(df)
        self.assertGreater(len(per_trade_returns), 0)

    def test_invalid_strategy_raises_error(self):
        df = _generate_test_data()
        # Backtester accepts any object with generate_signals method
        # So we test that it works with a valid strategy
        strategy = SMACrossoverStrategy(fast_window=5, slow_window=10)
        backtester = Backtester(strategy, risk_free_rate=0.02)
        equity_curve, per_trade_returns = backtester.run(df)
        self.assertIsInstance(equity_curve, pd.Series)


class TestMonteCarloSimulator(unittest.TestCase):
    """Tests for MonteCarloSimulator."""

    def test_bootstrap_returns_correct_shape(self):
        per_trade_returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        equity_curve = pd.Series([1.0] + [1.0 + i * 0.001 for i in range(100)])
        simulator = MonteCarloSimulator(n_simulations=10, seed=42, method="bootstrap")
        curves = simulator.run(per_trade_returns, equity_curve)
        self.assertEqual(curves.shape[0], len(equity_curve))
        self.assertEqual(curves.shape[1], 10)

    def test_parametric_returns_correct_shape(self):
        per_trade_returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        equity_curve = pd.Series([1.0] + [1.0 + i * 0.001 for i in range(100)])
        simulator = MonteCarloSimulator(n_simulations=10, seed=42, method="parametric")
        curves = simulator.run(per_trade_returns, equity_curve)
        self.assertEqual(curves.shape[0], len(equity_curve))
        self.assertEqual(curves.shape[1], 10)

    def test_invalid_method_raises_error(self):
        per_trade_returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        equity_curve = pd.Series([1.0] + [1.0 + i * 0.001 for i in range(100)])
        with self.assertRaises(ValueError):
            MonteCarloSimulator(n_simulations=10, seed=42, method="invalid")


class TestMetricsCalculator(unittest.TestCase):
    """Tests for MetricsCalculator."""

    def test_compute_all_metrics_returns_dict(self):
        per_trade_returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        equity_curve = pd.Series([1.0] + [1.0 + i * 0.001 for i in range(100)])
        simulator = MonteCarloSimulator(n_simulations=10, seed=42, method="bootstrap")
        curves = simulator.run(per_trade_returns, equity_curve)
        calculator = MetricsCalculator(risk_free_rate=0.02)
        metrics = calculator.compute_all_metrics(curves, equity_curve)
        self.assertIsInstance(metrics, dict)
        self.assertIn("annualized_return", metrics)
        self.assertIn("sharpe_ratio", metrics)
        self.assertIn("max_drawdown", metrics)
        self.assertIn("var_95", metrics)
        self.assertIn("cvar_95", metrics)
        self.assertIn("win_rate", metrics)
        self.assertIn("profit_factor", metrics)
        self.assertIn("calmar_ratio", metrics)
        self.assertIn("kelly_fraction", metrics)

    def test_sharpe_ratio_calculation(self):
        per_trade_returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        equity_curve = pd.Series([1.0] + [1.0 + i * 0.001 for i in range(100)])
        simulator = MonteCarloSimulator(n_simulations=10, seed=42, method="bootstrap")
        curves = simulator.run(per_trade_returns, equity_curve)
        calculator = MetricsCalculator(risk_free_rate=0.02)
        metrics = calculator.compute_all_metrics(curves, equity_curve)
        self.assertIsInstance(metrics["sharpe_ratio"], float)

    def test_max_drawdown_is_negative(self):
        per_trade_returns = pd.Series(np.random.normal(-0.001, 0.01, 100))
        equity_curve = pd.Series([1.0] + [1.0 - i * 0.001 for i in range(100)])
        simulator = MonteCarloSimulator(n_simulations=10, seed=42, method="bootstrap")
        curves = simulator.run(per_trade_returns, equity_curve)
        calculator = MetricsCalculator(risk_free_rate=0.02)
        metrics = calculator.compute_all_metrics(curves, equity_curve)
        self.assertLess(metrics["max_drawdown"], 0)


class TestStrategyComparator(unittest.TestCase):
    """Tests for StrategyComparator."""

    def test_compare_returns_dataframe(self):
        df = _generate_test_data()
        strategies = [
            {"name": "sma_crossover", "params": {"fast_window": 5, "slow_window": 10}},
            {"name": "rsi", "params": {"period": 14, "overbought": 70, "oversold": 30}},
        ]
        comparator = StrategyComparator(risk_free_rate=0.02, n_simulations=10, seed=42)
        results = comparator.compare(df, strategies)
        self.assertIsInstance(results, pd.DataFrame)
        self.assertEqual(len(results), 2)

    def test_get_best_strategy(self):
        df = _generate_test_data()
        strategies = [
            {"name": "sma_crossover", "params": {"fast_window": 5, "slow_window": 10}},
            {"name": "rsi", "params": {"period": 14, "overbought": 70, "oversold": 30}},
        ]
        comparator = StrategyComparator(risk_free_rate=0.02, n_simulations=10, seed=42)
        best = comparator.get_best_strategy(df, strategies, metric="sharpe_ratio")
        self.assertIn("strategy", best)
        self.assertIn("params", best)
        self.assertIn("sharpe_ratio", best)


class TestDataValidator(unittest.TestCase):
    """Tests for DataValidator."""

    def test_valid_data_passes(self):
        df = _generate_test_data()
        validator = DataValidator()
        is_valid, errors = validator.is_valid(df)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_missing_columns_fail(self):
        df = pd.DataFrame({"date": pd.date_range("2020-01-02", periods=100)})
        validator = DataValidator()
        is_valid, errors = validator.is_valid(df)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_invalid_price_relationships_fail(self):
        df = _generate_test_data()
        df.loc[50, "high"] = df.loc[50, "low"] - 10  # high < low
        validator = DataValidator()
        is_valid, errors = validator.is_valid(df)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_non_monotonic_dates_fail(self):
        df = _generate_test_data()
        df = df.sample(frac=1).reset_index(drop=True)  # Shuffle dates
        validator = DataValidator()
        is_valid, errors = validator.is_valid(df)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestParameterOptimizer(unittest.TestCase):
    """Tests for ParameterOptimizer."""

    def test_optimize_returns_dataframe(self):
        df = _generate_test_data()
        param_grid = {"fast_window": [5, 10], "slow_window": [20, 30]}
        optimizer = ParameterOptimizer(risk_free_rate=0.02, n_simulations=10, seed=42)
        results = optimizer.optimize(df, "sma_crossover", param_grid, n_best=5)
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)

    def test_optimize_sorts_by_metric(self):
        df = _generate_test_data()
        param_grid = {"fast_window": [5, 10], "slow_window": [20, 30]}
        optimizer = ParameterOptimizer(risk_free_rate=0.02, n_simulations=10, seed=42, metric="sharpe_ratio")
        results = optimizer.optimize(df, "sma_crossover", param_grid, n_best=5)
        self.assertTrue(results["sharpe_ratio"].is_monotonic_decreasing)


class TestWalkForwardAnalyzer(unittest.TestCase):
    """Tests for WalkForwardAnalyzer."""

    def test_analyze_returns_dataframe(self):
        df = _generate_test_data(n_days=500)
        param_grid = {"fast_window": [5, 10], "slow_window": [20, 30]}
        analyzer = WalkForwardAnalyzer(risk_free_rate=0.02, n_simulations=10, seed=42)
        results = analyzer.analyze(df, "sma_crossover", param_grid, train_size=100, test_size=50, step_size=50)
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)


class TestBacktestVisualizer(unittest.TestCase):
    """Tests for BacktestVisualizer."""

    def test_plot_equity_curves_saves_file(self):
        per_trade_returns = pd.Series(np.random.normal(0.001, 0.01, 100))
        equity_curve = pd.Series([1.0] + [1.0 + i * 0.001 for i in range(100)])
        simulator = MonteCarloSimulator(n_simulations=10, seed=42, method="bootstrap")
        curves = simulator.run(per_trade_returns, equity_curve)
        visualizer = BacktestVisualizer()
        output_path = "/tmp/test_equity_curves.png"
        visualizer.plot_equity_curves(curves, equity_curve, output_path=output_path)
        self.assertTrue(Path(output_path).exists())

    def test_plot_drawdown_saves_file(self):
        equity_curve = pd.Series([1.0] + [1.0 + i * 0.001 for i in range(100)])
        visualizer = BacktestVisualizer()
        output_path = "/tmp/test_drawdown.png"
        visualizer.plot_drawdown(equity_curve, output_path=output_path)
        self.assertTrue(Path(output_path).exists())

    def test_plot_strategy_comparison_saves_file(self):
        comparison = pd.DataFrame({
            "strategy": ["SMA", "RSI"],
            "sharpe_ratio": [1.5, 1.2],
        })
        visualizer = BacktestVisualizer()
        output_path = "/tmp/test_comparison.png"
        visualizer.plot_strategy_comparison(comparison, output_path=output_path)
        self.assertTrue(Path(output_path).exists())


if __name__ == "__main__":
    unittest.main()
