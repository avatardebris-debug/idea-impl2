"""Integration test for the full backtesting pipeline."""

import sys
import os
import tempfile
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

from market_strategy_backtester.data.loader import load_ohlcv_data
from market_strategy_backtester.strategies.sma_crossover import SMACrossoverStrategy
from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.engine.monte_carlo import MonteCarloSimulator
from market_strategy_backtester.metrics.risk import MetricsCalculator
from market_strategy_backtester.reporting.text_report import TextReport
from market_strategy_backtester.reporting.csv_export import export_csv
from examples.generate_sample_data import generate_sample_ohlcv


def test_full_pipeline():
    """Test the complete backtesting pipeline end-to-end."""
    print("Running full pipeline integration test...")

    # Step 1: Generate sample data
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "sample_ohlcv.csv"
        df = generate_sample_ohlcv(str(data_path), n_days=600)
        print(f"✓ Generated {len(df)} trading days of sample data")

        # Step 2: Load data
        loaded_df = load_ohlcv_data(str(data_path))
        assert len(loaded_df) == 600
        assert set(loaded_df.columns) == {"date", "open", "high", "low", "close", "volume"}
        print("✓ Data loaded successfully")

        # Step 3: Create strategy and backtester
        strategy = SMACrossoverStrategy(fast_window=10, slow_window=30)
        backtester = Backtester(strategy, risk_free_rate=0.02)
        df_result = backtester.run_backtest(loaded_df)
        
        # Ensure 'strategy_return' exists (we can compute it from equity if not exposed, but my run_backtest exposes it? wait, run_backtest returns a subset of columns)
        # Let me re-compute equity_curve and per_trade_returns
        equity_curve = df_result["equity"] / backtester.initial_capital
        
        # In the old code, per_trade_returns were just the non-zero strategy returns.
        # Since I dropped strategy_return from the final returned DataFrame, I'll approximate it or just use equity differences.
        strategy_return = df_result["equity"].pct_change().fillna(0)
        per_trade_returns = strategy_return[strategy_return != 0].reset_index(drop=True)
        
        assert len(equity_curve) > 0
        assert len(per_trade_returns) > 0
        assert equity_curve.iloc[0] == 1.0
        print(f"✓ Backtest complete: {len(per_trade_returns)} trades, final equity = {equity_curve.iloc[-1]:.4f}")

        # Step 4: Run Monte Carlo simulation
        mc_simulator = MonteCarloSimulator(n_simulations=100, seed=42, method="bootstrap")
        simulation_curves = mc_simulator.run(per_trade_returns, equity_curve)
        assert len(simulation_curves.columns) == 100
        assert len(simulation_curves) == len(equity_curve)
        print(f"✓ Monte Carlo simulation complete: {len(simulation_curves.columns)} simulations")

        # Step 5: Calculate metrics
        metrics_calc = MetricsCalculator(risk_free_rate=0.02)
        summary = metrics_calc.compute_all_metrics(simulation_curves, equity_curve)
        assert "mean_annualized_return" in summary
        assert "base_sharpe_ratio" in summary
        assert "n_simulations" in summary
        print(f"✓ Metrics calculated: mean annualized return = {summary['mean_annualized_return']:.4%}")

        # Step 6: Generate text report
        report = TextReport(summary)
        text_report = report.generate()
        assert "MONTE CARLO RESULTS" in text_report
        assert "Annualized Return" in text_report
        assert "Sharpe Ratio" in text_report
        print("✓ Text report generated")

        # Step 7: Export CSV
        results_dir = Path(tmpdir) / "results"
        export_csv(simulation_curves, summary, results_dir)
        assert (results_dir / "equity_curves.csv").exists()
        assert (results_dir / "summary_statistics.csv").exists()
        print("✓ CSV files exported")

        # Print the report
        print("\n" + text_report)

    print("\n✅ All integration tests passed!")


if __name__ == "__main__":
    test_full_pipeline()
