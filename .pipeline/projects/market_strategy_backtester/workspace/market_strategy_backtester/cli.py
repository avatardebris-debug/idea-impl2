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
from market_strategy_backtester.strategies.registry import create_strategy
from market_strategy_backtester.comparator import StrategyComparator
from market_strategy_backtester.visualizer import BacktestVisualizer


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
    df_result = backtester.run_backtest(price_data)
    equity_curve = df_result["equity"] / backtester.initial_capital
    strategy_return = df_result["strategy_return"]
    per_trade_returns = strategy_return[strategy_return != 0].reset_index(drop=True)
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


def run_comparison(config_path: str) -> None:
    """Run strategy comparison from YAML config."""
    config = load_config(config_path)

    # 1. Load data
    data_path = config["data"]["path"]
    price_data = load_ohlcv_data(data_path)
    print(f"Loaded {len(price_data)} trading days from {data_path}")

    # 2. Build strategies
    strategies_config = config["strategies"]
    strategies = []
    strategy_names = []
    for sc in strategies_config:
        strategy = create_strategy(sc["name"], **sc.get("params", {}))
        strategies.append(strategy)
        strategy_names.append(sc.get("name", strategy.__class__.__name__))
    print(f"Built {len(strategies)} strategies: {', '.join(strategy_names)}")

    # 3. Compare
    use_mc = config.get("comparison", {}).get("use_monte_carlo", False)
    n_sims = config.get("comparison", {}).get("n_simulations", 1000)
    seed = config.get("comparison", {}).get("seed", 42)

    comparator = StrategyComparator(
        initial_capital=config.get("backtester", {}).get("initial_capital", 100000.0),
        commission_pct=config.get("backtester", {}).get("commission_pct", 0.001),
        slippage_pct=config.get("backtester", {}).get("slippage_pct", 0.0005),
        risk_free_rate=config.get("backtester", {}).get("risk_free_rate", 0.02),
    )

    if use_mc:
        comparison_df = comparator.compare_with_mc(
            strategies=strategies,
            price_data=price_data,
            strategy_names=strategy_names,
            n_simulations=n_sims,
            seed=seed,
        )
        print(f"Comparison complete (Monte Carlo with {n_sims} simulations)")
    else:
        comparison_df = comparator.compare(
            strategies=strategies,
            price_data=price_data,
            strategy_names=strategy_names,
        )
        print("Comparison complete (direct backtest)")

    # 4. Print comparison
    print("\n" + "=" * 60)
    print("  STRATEGY COMPARISON RESULTS")
    print("=" * 60)
    print(comparison_df.to_string(index=False))
    print("=" * 60)

    # 5. Export
    output_config = config.get("output", {})
    results_dir = Path(output_config.get("results_dir", "results"))
    results_dir.mkdir(parents=True, exist_ok=True)

    # Export comparison CSV
    csv_path = results_dir / "strategy_comparison.csv"
    comparison_df.to_csv(csv_path, index=False)
    print(f"Comparison CSV written to {csv_path}")

    # Export equity curves for each strategy
    for i, (name, strategy) in enumerate(zip(strategy_names, strategies)):
        backtester = Backtester(
            strategy=strategy,
            initial_capital=config.get("backtester", {}).get("initial_capital", 100000.0),
            commission_pct=config.get("backtester", {}).get("commission_pct", 0.001),
            slippage_pct=config.get("backtester", {}).get("slippage_pct", 0.0005),
            risk_free_rate=config.get("backtester", {}).get("risk_free_rate", 0.02),
        )
        result_df = backtester.run_backtest(price_data)
        equity_path = results_dir / f"equity_curve_{name}.csv"
        result_df.to_csv(equity_path, index=False)
        print(f"Equity curve for '{name}' written to {equity_path}")

    # 6. Visualize
    viz_config = config.get("visualization", {})
    if viz_config.get("enabled", False):
        visualizer = BacktestVisualizer(
            figsize=tuple(viz_config.get("figsize", [14, 7])),
            dpi=viz_config.get("dpi", 100),
        )

        # Plot comparison bar chart
        metric = viz_config.get("comparison_metric", "sharpe_ratio")
        comp_path = results_dir / "strategy_comparison.png"
        visualizer.plot_strategy_comparison(
            comparison_df,
            metric=metric,
            title=f"Strategy Comparison ({metric.replace('_', ' ').title()})",
            output_path=str(comp_path),
        )
        print(f"Comparison chart written to {comp_path}")

        # Plot equity curves for each strategy
        equity_curves = {}
        for name, strategy in zip(strategy_names, strategies):
            backtester = Backtester(
                strategy=strategy,
                initial_capital=config.get("backtester", {}).get("initial_capital", 100000.0),
                commission_pct=config.get("backtester", {}).get("commission_pct", 0.001),
                slippage_pct=config.get("backtester", {}).get("slippage_pct", 0.0005),
                risk_free_rate=config.get("backtester", {}).get("risk_free_rate", 0.02),
            )
            result_df = backtester.run_backtest(price_data)
            equity_curves[name] = result_df["equity"] / config.get("backtester", {}).get("initial_capital", 100000.0)

        # Plot all equity curves on one chart
        eq_path = results_dir / "equity_curves_comparison.png"
        visualizer.plot_equity_curves_comparison(
            equity_curves=equity_curves,
            title="Strategy Equity Curves Comparison",
            output_path=str(eq_path),
        )
        print(f"Equity curves comparison chart written to {eq_path}")

        # Plot drawdown for each strategy
        for name, strategy in zip(strategy_names, strategies):
            backtester = Backtester(
                strategy=strategy,
                initial_capital=config.get("backtester", {}).get("initial_capital", 100000.0),
                commission_pct=config.get("backtester", {}).get("commission_pct", 0.001),
                slippage_pct=config.get("backtester", {}).get("slippage_pct", 0.0005),
                risk_free_rate=config.get("backtester", {}).get("risk_free_rate", 0.02),
            )
            result_df = backtester.run_backtest(price_data)
            dd_path = results_dir / f"drawdown_{name}.png"
            visualizer.plot_drawdown(
                result_df["equity"] / config.get("backtester", {}).get("initial_capital", 100000.0),
                title=f"Drawdown - {name}",
                output_path=str(dd_path),
            )
            print(f"Drawdown chart for '{name}' written to {dd_path}")

        # Plot trade distribution for each strategy
        for name, strategy in zip(strategy_names, strategies):
            backtester = Backtester(
                strategy=strategy,
                initial_capital=config.get("backtester", {}).get("initial_capital", 100000.0),
                commission_pct=config.get("backtester", {}).get("commission_pct", 0.001),
                slippage_pct=config.get("backtester", {}).get("slippage_pct", 0.0005),
                risk_free_rate=config.get("backtester", {}).get("risk_free_rate", 0.02),
            )
            result_df = backtester.run_backtest(price_data)
            strategy_return = result_df["strategy_return"]
            per_trade_returns = strategy_return[strategy_return != 0].reset_index(drop=True)

            if len(per_trade_returns) > 0:
                td_path = results_dir / f"trade_distribution_{name}.png"
                visualizer.plot_trade_distribution(
                    per_trade_returns,
                    title=f"Trade Return Distribution - {name}",
                    output_path=str(td_path),
                )
                print(f"Trade distribution chart for '{name}' written to {td_path}")


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

    compare_parser = subparsers.add_parser("compare", help="Compare multiple strategies")
    compare_parser.add_argument(
        "--config", "-c",
        type=str,
        required=True,
        help="Path to YAML configuration file",
    )

    args = parser.parse_args()

    if args.command == "run":
        run(args.config)
    elif args.command == "compare":
        run_comparison(args.config)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
