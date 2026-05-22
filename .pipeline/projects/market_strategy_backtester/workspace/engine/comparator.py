"""Strategy comparison and benchmarking module.

Compares multiple strategies on the same price data and produces
a ranked summary of their performance metrics.
"""

import pandas as pd
from typing import Dict, List, Any

from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.engine.monte_carlo import MonteCarloSimulator
from market_strategy_backtester.metrics.risk import MetricsCalculator
from market_strategy_backtester.strategies.registry import create_strategy


class StrategyComparator:
    """Compares multiple strategies on the same price data.

    Attributes:
        risk_free_rate: Annual risk-free rate for Sharpe calculation.
        n_simulations: Number of Monte Carlo simulations per strategy.
        seed: Random seed for reproducibility.
    """

    def __init__(
        self,
        risk_free_rate: float = 0.02,
        n_simulations: int = 1000,
        seed: int = 42,
    ):
        self.risk_free_rate = risk_free_rate
        self.n_simulations = n_simulations
        self.seed = seed

    def compare(
        self,
        price_data: pd.DataFrame,
        strategies: List[Dict[str, Any]],
    ) -> pd.DataFrame:
        """Compare multiple strategies on the same price data.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.
            strategies: List of dicts with 'name' and 'params' keys.
                Example: [{'name': 'sma_crossover', 'params': {'fast_window': 10, 'slow_window': 30}},
                          {'name': 'rsi', 'params': {'rsi_window': 14}}]

        Returns:
            DataFrame with strategy comparison metrics (one row per strategy).
        """
        results = []

        for strat_config in strategies:
            name = strat_config["name"]
            params = strat_config.get("params", {})

            # Create strategy
            strategy = create_strategy(name, **params)

            # Run backtest
            backtester = Backtester(strategy, risk_free_rate=self.risk_free_rate)
            equity_curve, per_trade_returns = backtester.run(price_data)

            # Monte Carlo simulation
            mc_simulator = MonteCarloSimulator(
                n_simulations=self.n_simulations,
                seed=self.seed,
                method="bootstrap",
            )
            simulation_curves = mc_simulator.run(per_trade_returns, equity_curve)

            # Calculate metrics
            calculator = MetricsCalculator(risk_free_rate=self.risk_free_rate)
            summary = calculator.compute_all_metrics(simulation_curves, equity_curve)

            # Collect results
            results.append({
                "strategy": name,
                "params": str(params),
                "annualized_return": summary["annualized_return"],
                "sharpe_ratio": summary["sharpe_ratio"],
                "max_drawdown": summary["max_drawdown"],
                "var_95": summary["var_95"],
                "cvar_95": summary["cvar_95"],
                "win_rate": summary["win_rate"],
                "profit_factor": summary["profit_factor"],
                "calmar_ratio": summary["calmar_ratio"],
                "kelly_fraction": summary["kelly_fraction"],
                "total_trades": len(per_trade_returns),
                "total_return": equity_curve.iloc[-1] - 1,
            })

        return pd.DataFrame(results)

    def get_best_strategy(
        self,
        price_data: pd.DataFrame,
        strategies: List[Dict[str, Any]],
        metric: str = "sharpe_ratio",
    ) -> Dict[str, Any]:
        """Find the best strategy based on a given metric.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.
            strategies: List of strategy configurations.
            metric: Metric to optimize (default: 'sharpe_ratio').

        Returns:
            Dict with the best strategy's name, params, and metric value.
        """
        comparison = self.compare(price_data, strategies)

        if comparison.empty:
            raise ValueError("No strategies were compared")

        best_idx = comparison[metric].idxmax()
        best = comparison.loc[best_idx]

        return {
            "strategy": best["strategy"],
            "params": best["params"],
            metric: best[metric],
        }
