"""CLI entry point for the Market Strategy Backtester."""

import argparse
import sys
from pathlib import Path

import yaml

from market_strategy_backtester.engine.backtester import Backtester
from market_strategy_backtester.engine.monte_carlo import MonteCarloSimulator
from market_strategy_backtester.metrics.risk import MetricsCalculator
from market_strategy_backtester.reporting.csv_export import export_csv
from market_strategy_backtester.reporting.text_report import TextReport
from market_strategy_backtester.data.loader import load_ohlcv_data
from market_strategy_backtester.strategies.sma_crossover import SMACrossoverStrategy


def load_config(config_path: str) -> dict:
    """Load YAML configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def run(config_path: str) -> None:
    """Run the full backtesting pipeline."""
    config = load_config(config_path)

    # 1. Load data
    data_path = config["data"]["path"]
    price_data = load_ohlcv_data(data_path)
    print(f"Loaded {len(price_data)} trading days from {data_path}")

    # 2. Build strategy
    strategy_name = config["strategy"]["name"]
    strategy_params = config["strategy"]["params"]
    if strategy_name == "sma_crossover":
        strategy = SMACrossoverStrategy(**strategy_params)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    # 3. Backtest
    backtester = Backtester(strategy)
    equity_curve, per_trade_returns = backtester.run(price_data)
    print(f"Backtest complete: {len(per_trade_returns)} trades, "
          f"final equity: {equity_curve.iloc[-1]:.2f}")

    # 4. Monte Carlo simulation
    mc_config = config["monte_carlo"]
    mc_simulator = MonteCarloSimulator(
        n_simulations=mc_config["n_simulations"],
        seed=mc_config["seed"],
        method=mc_config.get("method", "bootstrap"),
    )
    simulation_curves = mc_simulator.run(per_trade_returns, equity_curve)
    print(f"Monte Carlo complete: {mc_config['n_simulations']} simulations")

    # 5. Calculate metrics
    calculator = MetricsCalculator()
    summary = calculator.compute_all_metrics(simulation_curves, equity_curve)
    print(f"Mean annualized return: {summary['mean_annualized_return']:.4f}")
    print(f"Mean Sharpe ratio: {summary['mean_sharpe_ratio']:.4f}")
    print(f"Mean max drawdown: {summary['mean_max_drawdown']:.4f}")
    print(f"Mean 95% VaR: {summary['mean_var_95']:.4f}")

    # 6. Export results
    output_config = config.get("output", {})
    results_dir = Path(output_config.get("results_dir", "results"))
    results_dir.mkdir(parents=True, exist_ok=True)

    if output_config.get("csv_export", True):
        export_csv(simulation_curves, summary, results_dir)
        print(f"CSV export written to {results_dir}")

    if output_config.get("text_report", True):
        report = TextReport(summary)
        report_text = report.generate()
        print(report_text)
        report_path = results_dir / "text_report.txt"
        report_path.write_text(report_text)
        print(f"Text report written to {report_path}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Market Strategy Backtester — Monte Carlo backtesting engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    run_parser = subparsers.add_parser("run", help="Run the backtesting pipeline")
    run_parser.add_argument(
        "--config", "-c",
        type=str,
        required=True,
        help="Path to YAML configuration file",
    )

    args = parser.parse_args()

    if args.command == "run":
        run(args.config)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
