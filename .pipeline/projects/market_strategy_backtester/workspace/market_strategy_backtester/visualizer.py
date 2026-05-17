"""Visualization module for backtesting results.

Generates matplotlib-based charts for equity curves, drawdowns,
and strategy comparison.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional


class BacktestVisualizer:
    """Generates visualizations for backtesting results.

    Attributes:
        figsize: Figure size as (width, height) tuple.
        dpi: Dots per inch for saved figures.
    """

    def __init__(self, figsize: tuple = (14, 7), dpi: int = 100):
        self.figsize = figsize
        self.dpi = dpi

    def plot_equity_curves(
        self,
        simulation_curves: pd.DataFrame,
        base_equity_curve: pd.Series,
        title: str = "Monte Carlo Equity Curves",
        output_path: Optional[str] = None,
    ) -> None:
        """Plot Monte Carlo equity curves with percentile bands.

        Args:
            simulation_curves: DataFrame of equity curves (rows=steps, cols=sims).
            base_equity_curve: Original equity curve.
            title: Chart title.
            output_path: Optional file path to save the figure.
        """
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=self.figsize)

        # Plot percentile bands
        n_sims = len(simulation_curves.columns)
        percentiles = [5, 25, 50, 75, 95]
        colors = ["#ff6b6b", "#ffa07a", "#4ecdc4", "#a8e6cf", "#88d8b0"]

        for i, p in enumerate(percentiles):
            vals = simulation_curves.quantile(p / 100, axis=1)
            label = f"{p}th percentile"
            alpha = 0.3 if p in [5, 95] else 0.6
            ax.plot(vals, label=label, color=colors[i], alpha=alpha, linewidth=1.5)

        # Plot median
        median_curve = simulation_curves.quantile(0.5, axis=1)
        ax.plot(median_curve, label="Median", color="black", linewidth=2, linestyle="--")

        # Plot base equity curve
        ax.plot(base_equity_curve, label="Base Strategy", color="blue", linewidth=2)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Trading Days", fontsize=12)
        ax.set_ylabel("Equity Multiplier", fontsize=12)
        ax.legend(loc="upper left", fontsize=10)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()

    def plot_equity_curves_comparison(
        self,
        equity_curves: Dict[str, pd.Series],
        title: str = "Equity Curves Comparison",
        output_path: Optional[str] = None,
    ) -> None:
        """Plot multiple equity curves on the same chart.

        Args:
            equity_curves: Dict mapping strategy names to equity curve Series.
            title: Chart title.
            output_path: Optional file path to save the figure.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=self.figsize)

        colors = ["#4ecdc4", "#ff6b6b", "#45b7d1", "#f9ca24", "#6c5ce7",
                  "#a8e6cf", "#fd79a8", "#e17055", "#00b894", "#636e72"]

        for i, (name, equity_curve) in enumerate(equity_curves.items()):
            color = colors[i % len(colors)]
            ax.plot(equity_curve, label=name, color=color, linewidth=1.5)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Trading Days", fontsize=12)
        ax.set_ylabel("Equity Multiplier", fontsize=12)
        ax.legend(loc="upper left", fontsize=10)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()

    def plot_drawdown(
        self,
        equity_curve: pd.Series,
        title: str = "Drawdown Analysis",
        output_path: Optional[str] = None,
    ) -> None:
        """Plot drawdown from equity curve.

        Args:
            equity_curve: Equity curve Series.
            title: Chart title.
            output_path: Optional file path to save the figure.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figsize, gridspec_kw={"height_ratios": [3, 1]})

        # Equity curve
        ax1.plot(equity_curve, color="blue", linewidth=1.5)
        ax1.set_title(title, fontsize=14, fontweight="bold")
        ax1.set_ylabel("Equity Multiplier", fontsize=12)
        ax1.grid(True, alpha=0.3)

        # Drawdown
        peak = equity_curve.cummax()
        drawdown = (equity_curve - peak) / peak
        ax2.fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.3)
        ax2.set_ylabel("Drawdown", fontsize=12)
        ax2.grid(True, alpha=0.3)

        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()

    def plot_strategy_comparison(
        self,
        comparison_results: pd.DataFrame,
        metric: str = "sharpe_ratio",
        title: str = "Strategy Comparison",
        output_path: Optional[str] = None,
    ) -> None:
        """Plot bar chart comparing strategies on a given metric.

        Args:
            comparison_results: DataFrame from StrategyComparator.compare().
            metric: Metric to compare (e.g., 'sharpe_ratio', 'annualized_return').
            title: Chart title.
            output_path: Optional file path to save the figure.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))

        strategies = comparison_results["strategy"].values
        values = comparison_results[metric].values
        colors = ["#4ecdc4" if v >= 0 else "#ff6b6b" for v in values]

        bars = ax.bar(strategies, values, color=colors, edgecolor="black", linewidth=0.5)

        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + (0.01 if val >= 0 else -0.05),
                f"{val:.2f}",
                ha="center",
                va="bottom" if val >= 0 else "top",
                fontsize=10,
            )

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_ylabel(metric.replace("_", " ").title(), fontsize=12)
        ax.set_xlabel("Strategy", fontsize=12)
        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.grid(True, alpha=0.3, axis="y")

        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()

    def plot_trade_distribution(
        self,
        per_trade_returns: pd.Series,
        title: str = "Trade Return Distribution",
        output_path: Optional[str] = None,
    ) -> None:
        """Plot histogram of per-trade returns.

        Args:
            per_trade_returns: Series of per-trade returns.
            title: Chart title.
            output_path: Optional file path to save the figure.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.hist(per_trade_returns, bins=50, color="#4ecdc4", edgecolor="black", alpha=0.7)
        ax.axvline(x=per_trade_returns.mean(), color="red", linestyle="--", linewidth=2, label=f"Mean: {per_trade_returns.mean():.4f}")
        ax.axvline(x=0, color="black", linewidth=0.5)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Trade Return", fontsize=12)
        ax.set_ylabel("Frequency", fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
            plt.close(fig)
        else:
            plt.show()
