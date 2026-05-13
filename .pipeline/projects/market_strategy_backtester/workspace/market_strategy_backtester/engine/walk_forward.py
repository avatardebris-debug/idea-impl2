"""Walk-forward analysis module.

Performs walk-forward (rolling) analysis to test strategy robustness
across different time periods.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.engine.monte_carlo import MonteCarloSimulator
from market_strategy_backtester.metrics.risk import MetricsCalculator
from market_strategy_backtester.strategies.base import Strategy


class WalkForwardAnalyzer:
    """Performs walk-forward analysis on a strategy.

    Splits the data into in-sample (training) and out-of-sample (testing)
    periods, optimizing parameters on in-sample and testing on out-of-sample.

    Attributes:
        risk_free_rate: Annual risk-free rate for Sharpe calculation.
        n_simulations: Number of Monte Carlo simulations per period.
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

    def analyze(
        self,
        price_data: pd.DataFrame,
        strategy_name: str,
        param_grid: Dict[str, List[Any]],
        train_size: int = 252,  # 1 year of trading days
        test_size: int = 63,    # 1 quarter of trading days
        step_size: int = 21,    # 1 month step
    ) -> pd.DataFrame:
        """Perform walk-forward analysis.

        Args:
            price_data: DataFrame with OHLCV columns and a 'date' column.
            strategy_name: Name of the strategy to analyze.
            param_grid: Dictionary mapping parameter names to lists of values.
            train_size: Number of data points for training (in-sample).
            test_size: Number of data points for testing (out-of-sample).
            step_size: Step size for rolling window.

        Returns:
            DataFrame with walk-forward results (one row per period).
        """
        results = []
        dates = price_data["date"].values

        # Calculate number of periods
        n_periods = (len(dates) - train_size) // step_size

        print(f"Walk-forward analysis: {n_periods} periods, train={train_size}, test={test_size}")

        for i in range(n_periods):
            train_start = i * step_size
            train_end = train_start + train_size
            test_start = train_end
            test_end = test_start + test_size

            if test_end > len(dates):
                break

            train_data = price_data.iloc[train_start:train_end]
            test_data = price_data.iloc[test_start:test_end]

            # Optimize on training data
            best_params = self._optimize_on_train(
                train_data, strategy_name, param_grid
            )

            # Test on out-of-sample data
            try:
                strategy = create_strategy(strategy_name, **best_params)
                backtester = Backtester(strategy, risk_free_rate=self.risk_free_rate)
                equity_curve, per_trade_returns = backtester.run(test_data)

                if len(per_trade_returns) < 5:
                    print(f"  Period {i + 1}: Too few trades ({len(per_trade_returns)})")
                    continue

                mc_simulator = MonteCarloSimulator(
                    n_simulations=self.n_simulations,
                    seed=self.seed,
                    method="bootstrap",
                )
                simulation_curves = mc_simulator.run(per_trade_returns, equity_curve)

                calculator = MetricsCalculator(risk_free_rate=self.risk_free_rate)
                summary = calculator.compute_all_metrics(simulation_curves, equity_curve)

                results.append({
                    "period": i + 1,
                    "train_start": train_start,
                    "train_end": train_end,
                    "test_start": test_start,
                    "test_end": test_end,
                    "best_params": str(best_params),
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

                if (i + 1) % 5 == 0:
                    print(f"  Completed period {i + 1}/{n_periods}")

            except Exception as e:
                print(f"  Error in period {i + 1}: {e}")
                continue

        if not results:
            raise ValueError("No valid walk-forward periods were found")

        return pd.DataFrame(results)

    def _optimize_on_train(
        self,
        train_data: pd.DataFrame,
        strategy_name: str,
        param_grid: Dict[str, List[Any]],
    ) -> Dict[str, Any]:
        """Optimize parameters on training data.

        Args:
            train_data: Training data DataFrame.
            strategy_name: Strategy name.
            param_grid: Parameter grid.

        Returns:
            Best parameter dictionary.
        """
        from market_strategy_backtester.engine.optimizer import ParameterOptimizer

        optimizer = ParameterOptimizer(
            risk_free_rate=self.risk_free_rate,
            n_simulations=self.n_simulations,
            seed=self.seed,
            metric=self.metric,
        )
        results = optimizer.optimize(train_data, strategy_name, param_grid, n_best=1)

        if results.empty:
            raise ValueError("No valid parameters found during training")

        # Parse params string back to dict
        params_str = results.iloc[0]["params"]
        # Simple parsing: extract key-value pairs from string like "{'fast_window': 10, 'slow_window': 30}"
        params = eval(params_str)  # Safe here as we control the input
        return params


def create_strategy(name: str, **params):
    """Helper to import create_strategy locally."""
    from market_strategy_backtester.strategies.registry import create_strategy as _create
    return _create(name, **params)
