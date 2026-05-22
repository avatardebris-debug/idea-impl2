"""Text report generator for backtesting results."""

from typing import Dict


class TextReport:
    """Generates human-readable text reports from backtesting results."""

    def __init__(self, summary: Dict):
        self.summary = summary

    def generate(self) -> str:
        """Generate a formatted text report.

        Returns:
            Formatted string with metrics summary.
        """
        s = self.summary
        lines = [
            "=" * 60,
            "  MARKET STRATEGY BACKTESTER — MONTE CARLO RESULTS",
            "=" * 60,
            "",
            "--- Monte Carlo Summary (across all simulations) ---",
            f"  Number of simulations: {s.get('n_simulations', 'N/A')}",
            "",
            "  Annualized Return:",
            f"    Mean:   {s['mean_annualized_return']:.4%}",
            f"    Median: {s['median_annualized_return']:.4%}",
            f"    Std:    {s['std_annualized_return']:.4%}",
            "",
            "  Sharpe Ratio:",
            f"    Mean:   {s['mean_sharpe_ratio']:.4f}",
            f"    Median: {s['median_sharpe_ratio']:.4f}",
            "",
            "  Max Drawdown:",
            f"    Mean:   {s['mean_max_drawdown']:.4%}",
            f"    Median: {s['median_max_drawdown']:.4%}",
            "",
            "  Value at Risk (95%):",
            f"    Mean:   {s['mean_var_95']:.4%}",
            f"    Median: {s['median_var_95']:.4%}",
            "",
            "  Conditional VaR (95%):",
            f"    Mean:   {s['mean_cvar_95']:.4%}",
            "",
            "  Win Rate:",
            f"    Mean:   {s['mean_win_rate']:.4%}",
            "",
            "  Profit Factor:",
            f"    Mean:   {s['mean_profit_factor']:.4f}",
            "",
            "  Calmar Ratio:",
            f"    Mean:   {s['mean_calmar_ratio']:.4f}",
            "",
            "  Kelly Fraction:",
            f"    Mean:   {s['mean_kelly_fraction']:.4f}",
            "",
            "--- Equity Curve Percentile Bands (final step) ---",
            f"  5th percentile:  {s.get('p5_final_equity', 'N/A'):.4f}",
            f"  50th percentile: {s.get('p50_final_equity', 'N/A'):.4f}",
            f"  95th percentile: {s.get('p95_final_equity', 'N/A'):.4f}",
            "",
            "--- Base (Original) Strategy ---",
            f"  Annualized Return: {s['base_annualized_return']:.4%}",
            f"  Sharpe Ratio:      {s['base_sharpe_ratio']:.4f}",
            f"  Max Drawdown:      {s['base_max_drawdown']:.4%}",
            f"  95% VaR:           {s['base_var_95']:.4%}",
            f"  Final Equity:      {s['base_final_equity']:.4f}",
            "",
            "=" * 60,
        ]
        return "\n".join(lines)
