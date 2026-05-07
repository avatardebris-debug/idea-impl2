"""Risk metrics calculator.

Computes annualized return, Sharpe ratio, max drawdown, VaR, CVaR,
and equity curve percentiles across simulations.
"""

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


class MetricsCalculator:
    """Calculator for risk-adjusted performance metrics.

    Attributes:
        risk_free_rate: Annual risk-free rate for Sharpe calculation (default: 0.02).
    """

    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate

    def compute_all_metrics(
        self,
        simulation_curves: pd.DataFrame,
        base_equity_curve: pd.Series,
    ) -> dict:
        """Compute all risk metrics for all simulations and the base curve.

        Args:
            simulation_curves: DataFrame of equity curves (rows=steps, cols=sims).
            base_equity_curve: Original equity curve.

        Returns:
            Dictionary with mean/percentile metrics across simulations and base curve metrics.
        """
        # Compute per-simulation metrics
        sim_metrics = []
        for col in simulation_curves.columns:
            curve = simulation_curves[col]
            metrics = self._compute_curve_metrics(curve)
            metrics["sim_id"] = col
            sim_metrics.append(metrics)

        sim_df = pd.DataFrame(sim_metrics)

        # Compute base curve metrics
        base_metrics = self._compute_curve_metrics(base_equity_curve)

        # Compute percentile bands across simulations
        percentiles = {}
        for p in [5, 50, 95]:
            percentiles[f"p{p}_final_equity"] = simulation_curves.iloc[-1].quantile(p / 100)

        # Summary statistics
        summary = {
            "mean_annualized_return": sim_df["annualized_return"].mean(),
            "median_annualized_return": sim_df["annualized_return"].median(),
            "std_annualized_return": sim_df["annualized_return"].std(),
            "mean_sharpe_ratio": sim_df["sharpe_ratio"].mean(),
            "median_sharpe_ratio": sim_df["sharpe_ratio"].median(),
            "mean_max_drawdown": sim_df["max_drawdown"].mean(),
            "median_max_drawdown": sim_df["max_drawdown"].median(),
            "mean_var_95": sim_df["var_95"].mean(),
            "median_var_95": sim_df["var_95"].median(),
            "mean_cvar_95": sim_df["cvar_95"].mean(),
            "mean_win_rate": sim_df["win_rate"].mean(),
            "mean_profit_factor": sim_df["profit_factor"].mean(),
            "mean_calmar_ratio": sim_df["calmar_ratio"].mean(),
            "mean_kelly_fraction": sim_df["kelly_fraction"].mean(),
            "base_annualized_return": base_metrics["annualized_return"],
            "base_sharpe_ratio": base_metrics["sharpe_ratio"],
            "base_max_drawdown": base_metrics["max_drawdown"],
            "base_var_95": base_metrics["var_95"],
            "base_final_equity": base_equity_curve.iloc[-1],
            **percentiles,
            "n_simulations": len(sim_df),
        }

        return summary

    def _compute_curve_metrics(self, curve: pd.Series) -> dict:
        """Compute metrics for a single equity curve."""
        # Daily returns from equity curve
        daily_returns = curve.pct_change().dropna()

        if len(daily_returns) == 0:
            return {
                "annualized_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "var_95": 0.0,
                "cvar_95": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "calmar_ratio": 0.0,
                "kelly_fraction": 0.0,
            }

        # Annualized return
        n_days = len(daily_returns)
        total_return = curve.iloc[-1] / curve.iloc[0]
        annualized_return = total_return ** (TRADING_DAYS_PER_YEAR / n_days) - 1

        # Sharpe ratio (annualized)
        excess_return = daily_returns.mean() - self.risk_free_rate / TRADING_DAYS_PER_YEAR
        sharpe_ratio = (excess_return / daily_returns.std()) * np.sqrt(TRADING_DAYS_PER_YEAR) if daily_returns.std() > 0 else 0.0

        # Max drawdown
        running_max = curve.cummax()
        drawdown = (curve - running_max) / running_max
        max_drawdown = drawdown.min()

        # VaR (Value at Risk) at 95% confidence
        var_95 = np.percentile(daily_returns, 5)

        # CVaR (Conditional VaR) at 95% confidence
        cvar_95 = daily_returns[daily_returns <= var_95].mean() if (daily_returns <= var_95).any() else var_95

        # Win rate
        win_rate = (daily_returns > 0).mean()

        # Profit factor (gross profit / gross loss)
        gains = daily_returns[daily_returns > 0].sum()
        losses = abs(daily_returns[daily_returns < 0].sum())
        profit_factor = gains / losses if losses > 0 else float("inf") if gains > 0 else 0.0

        # Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

        # Kelly fraction
        win_prob = (daily_returns > 0).mean()
        avg_win = daily_returns[daily_returns > 0].mean() if win_prob > 0 else 0
        avg_loss = abs(daily_returns[daily_returns < 0].mean()) if (daily_returns < 0).any() else 1
        kelly_fraction = (win_prob * avg_win - (1 - win_prob) * avg_loss) / avg_loss if avg_loss > 0 else 0.0

        return {
            "annualized_return": annualized_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "calmar_ratio": calmar_ratio,
            "kelly_fraction": kelly_fraction,
        }
