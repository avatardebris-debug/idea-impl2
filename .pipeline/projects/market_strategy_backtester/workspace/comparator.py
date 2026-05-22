"""Strategy comparison module.

Compares multiple strategies on the same price data and produces
a comparison DataFrame with key metrics.
"""

import pandas as pd
from typing import List, Dict, Any

from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.metrics.risk import MetricsCalculator
from market_strategy_backtester.strategies.base import Strategy


class StrategyComparator:
    """Compares multiple strategies on the same price data.

    Attributes:
        initial_capital: Initial capital for backtesting (default: 100000.0).
        commission_pct: Commission percentage per trade (default: 0.001).
        slippage_pct: Slippage percentage per trade (default: 0.0005).
        risk_free_rate: Annual risk-free rate for Sharpe calculation (default: 0.02).
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        risk_free_rate: float = 0.02,
    ):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.risk_free_rate = risk_free_rate

    def compare(
        self,
        strategies: List[Strategy],
        price_data: pd.DataFrame,
        strategy_names: List[str] = None,
    ) -> pd.DataFrame:
        """Compare multiple strategies on the same price data.

        Args:
            strategies: List of Strategy instances to compare.
            price_data: DataFrame with OHLCV columns and a 'date' column.
            strategy_names: Optional list of names for each strategy.
                If not provided, uses class names.

        Returns:
            DataFrame with columns [strategy, annualized_return, sharpe_ratio,
                max_drawdown, win_rate, profit_factor, calmar_ratio,
                kelly_fraction, final_equity, n_trades]
        """
        if strategy_names is None:
            strategy_names = [s.__class__.__name__ for s in strategies]

        if len(strategies) != len(strategy_names):
            raise ValueError("strategies and strategy_names must have the same length")

        results = []
        metrics_calc = MetricsCalculator()

        for name, strategy in zip(strategy_names, strategies):
            backtester = Backtester(
                strategy=strategy,
                initial_capital=self.initial_capital,
                commission_pct=self.commission_pct,
                slippage_pct=self.slippage_pct,
                risk_free_rate=self.risk_free_rate,
            )
            result_df = backtester.run_backtest(price_data)

            equity_curve = result_df["equity"] / self.initial_capital
            strategy_return = result_df["strategy_return"]

            # Calculate per-trade returns
            per_trade_returns = strategy_return[strategy_return != 0].reset_index(drop=True)
            n_trades = len(per_trade_returns)

            # Calculate metrics
            metrics = metrics_calc.compute_all_metrics(
                pd.DataFrame(),  # No MC simulations for single strategy
                equity_curve,
            )

            # Add strategy-specific info
            metrics["strategy"] = name
            metrics["n_trades"] = n_trades
            metrics["final_equity"] = equity_curve.iloc[-1]

            results.append(metrics)

        comparison_df = pd.DataFrame(results)
        return comparison_df

    def compare_with_mc(
        self,
        strategies: List[Strategy],
        price_data: pd.DataFrame,
        strategy_names: List[str] = None,
        n_simulations: int = 1000,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Compare multiple strategies with Monte Carlo simulations.

        Args:
            strategies: List of Strategy instances to compare.
            price_data: DataFrame with OHLCV columns and a 'date' column.
            strategy_names: Optional list of names for each strategy.
            n_simulations: Number of Monte Carlo simulations per strategy.
            seed: Random seed for reproducibility.

        Returns:
            DataFrame with columns [strategy, mean_annualized_return,
                mean_sharpe_ratio, mean_max_drawdown, mean_var_95,
                mean_win_rate, mean_profit_factor, mean_calmar_ratio,
                mean_kelly_fraction, n_trades, final_equity]
        """
        from market_strategy_backtester.engine.monte_carlo import MonteCarloSimulator

        if strategy_names is None:
            strategy_names = [s.__class__.__name__ for s in strategies]

        if len(strategies) != len(strategy_names):
            raise ValueError("strategies and strategy_names must have the same length")

        results = []
        metrics_calc = MetricsCalculator()
        mc_simulator = MonteCarloSimulator(n_simulations=n_simulations, seed=seed)

        for name, strategy in zip(strategy_names, strategies):
            backtester = Backtester(
                strategy=strategy,
                initial_capital=self.initial_capital,
                commission_pct=self.commission_pct,
                slippage_pct=self.slippage_pct,
                risk_free_rate=self.risk_free_rate,
            )
            result_df = backtester.run_backtest(price_data)

            equity_curve = result_df["equity"] / self.initial_capital
            strategy_return = result_df["strategy_return"]

            # Calculate per-trade returns
            per_trade_returns = strategy_return[strategy_return != 0].reset_index(drop=True)

            # Run Monte Carlo
            simulation_curves = mc_simulator.run(per_trade_returns, equity_curve)

            # Calculate metrics
            metrics = metrics_calc.compute_all_metrics(simulation_curves, equity_curve)

            # Add strategy-specific info
            metrics["strategy"] = name
            metrics["n_trades"] = len(per_trade_returns)
            metrics["final_equity"] = equity_curve.iloc[-1]

            results.append(metrics)

        comparison_df = pd.DataFrame(results)
        return comparison_df
