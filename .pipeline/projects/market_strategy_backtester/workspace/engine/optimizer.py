"""Parameter optimization module.

Performs grid search over strategy parameters to find the best configuration.
"""

import itertools
from typing import Dict, List, Any, Optional

import pandas as pd

from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.engine.monte_carlo import MonteCarloSimulator
from market_strategy_backtester.metrics.risk import MetricsCalculator
from market_strategy_backtester.strategies.registry import create_strategy


class ParameterOptimizer:
    """Grid search optimizer for strategy parameters.

    Attributes:
        risk_free_rate: Annual risk-free rate for Sharpe calculation.
        n_simulations: Number of Monte Carlo simulations per parameter set.
        seed: Random seed for reproducibility.
        metric: Metric to optimize (default: 'sharpe_ratio').
    """

    def __init__(
        self,
        risk_free_rate: float = 0.02,
        n_simulations: int = 500,
        seed: int = 42,
        metric: str = "sharpe_ratio",
    ):
        self.risk_free_rate = risk_free_rate
        self.n_simulations = n_simulations
        self.seed = seed
        self.metric = metric

    def optimize(
        self,
        price_data: pd.DataFrame,
        strategy_name: str,
        param_grid: Dict[str, List[Any]],
        n_best: int = 5,
    ) -> pd.DataFrame:
        """Perform grid search over strategy parameters.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.
            strategy_name: Name of the strategy to optimize.
            param_grid: Dictionary mapping parameter names to lists of values.
                Example: {'fast_window': [5, 10, 15], 'slow_window': [20, 30, 40]}
            n_best: Number of top results to return.

        Returns:
            DataFrame with parameter combinations and their metrics, sorted by the optimization metric.
        """
        results = []

        # Generate all parameter combinations
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = list(itertools.product(*values))

        total = len(combinations)
        print(f"Optimizing strategy '{strategy_name}' with {total} parameter combinations...")

        for i, combo in enumerate(combinations):
            params = dict(zip(keys, combo))

            # Skip invalid combinations (e.g., fast >= slow)
            if not self._is_valid_params(strategy_name, params):
                continue

            try:
                # Create strategy
                strategy = create_strategy(strategy_name, **params)

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
                result = {
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
                }
                results.append(result)

                if (i + 1) % 10 == 0 or i == total - 1:
                    print(f"  Completed {i + 1}/{total} combinations")

            except Exception as e:
                print(f"  Error with params {params}: {e}")
                continue

        if not results:
            raise ValueError("No valid parameter combinations were found")

        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values(by=self.metric, ascending=False)

        return results_df.head(n_best)

    def _is_valid_params(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """Check if parameter combination is valid for the strategy.

        Args:
            strategy_name: Name of the strategy.
            params: Parameter dictionary.

        Returns:
            True if parameters are valid, False otherwise.
        """
        if strategy_name == "sma_crossover":
            fast = params.get("fast_window", 0)
            slow = params.get("slow_window", 0)
            if fast >= slow:
                return False
        elif strategy_name == "macd":
            fast = params.get("fast_period", 0)
            slow = params.get("slow_period", 0)
            signal = params.get("signal_period", 0)
            if fast >= slow or signal >= fast:
                return False
        return True
