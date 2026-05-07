"""CSV export for backtesting results."""

import pandas as pd
from pathlib import Path
from typing import Dict


def export_csv(
    simulation_curves: pd.DataFrame,
    summary: Dict,
    results_dir: Path,
) -> None:
    """Export simulation results to CSV files.

    Args:
        simulation_curves: DataFrame of equity curves (rows=steps, cols=sims).
        summary: Dictionary of summary statistics.
        results_dir: Directory to write output files.
    """
    results_dir.mkdir(parents=True, exist_ok=True)

    # Export per-simulation equity curves
    curves_path = results_dir / "equity_curves.csv"
    simulation_curves.to_csv(curves_path, index_label="step")

    # Export summary statistics
    summary_path = results_dir / "summary_statistics.csv"
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(summary_path, index=False)
