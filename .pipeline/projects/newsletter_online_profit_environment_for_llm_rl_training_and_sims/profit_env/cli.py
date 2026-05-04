"""Command-line interface for the newsletter profit simulator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .config import SimConfig
from .simulator import NewsletterSimulator


def run_simulation(args: argparse.Namespace) -> dict:
    """Run a simulation with given arguments.

    Args:
        args: Parsed command line arguments.

    Returns:
        dict: Simulation results.
    """
    config = SimConfig(
        initial_subscribers=args.subscribers,
        initial_revenue=args.revenue,
        growth_rate=args.growth,
        churn_rate=args.churn,
        revenue_per_subscriber=args.rps,
        content_cost=args.content_cost,
        marketing_cost=args.marketing_cost,
        platform_fee=args.platform_fee,
        max_months=args.months,
        seed=args.seed,
    )

    sim = NewsletterSimulator(config)
    history = sim.run()

    results = {
        "config": config.to_dict(),
        "summary": sim.get_metrics(),
        "history": [s.to_dict() for s in history],
    }

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

    if args.verbose:
        print(f"Simulation complete. {len(history)} months simulated.")
        print(f"Final subscribers: {history[-1].subscribers}")
        print(f"Final cumulative profit: ${history[-1].cumulative_profit:.2f}")

    return results


def analyze_results(args: argparse.Namespace) -> dict:
    """Analyze simulation results from a file.

    Args:
        args: Parsed command line arguments.

    Returns:
        dict: Analysis results.
    """
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path) as f:
        data = json.load(f)

    history = data.get("history", [])
    if not history:
        print("Error: No history data found in input file.", file=sys.stderr)
        sys.exit(1)

    analysis = {
        "total_months": len(history),
        "subscribers": {
            "initial": history[0].get("subscribers", 0),
            "final": history[-1].get("subscribers", 0),
            "peak": max(h.get("subscribers", 0) for h in history),
        },
        "revenue": {
            "initial": history[0].get("revenue", 0.0),
            "final": history[-1].get("revenue", 0.0),
            "total": sum(h.get("revenue", 0.0) for h in history),
        },
        "profit": {
            "initial": history[0].get("profit", 0.0),
            "final": history[-1].get("profit", 0.0),
            "total": sum(h.get("profit", 0.0) for h in history),
            "cumulative": history[-1].get("cumulative_profit", 0.0),
        },
    }

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(analysis, f, indent=2)

    return analysis


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Newsletter Profit Simulator"
    )

    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a simulation")
    run_parser.add_argument("--subscribers", type=int, default=1000, help="Initial subscribers")
    run_parser.add_argument("--revenue", type=float, default=5000.0, help="Initial revenue")
    run_parser.add_argument("--growth", type=float, default=0.05, help="Growth rate")
    run_parser.add_argument("--churn", type=float, default=0.02, help="Churn rate")
    run_parser.add_argument("--rps", type=float, default=5.0, help="Revenue per subscriber")
    run_parser.add_argument("--content-cost", type=float, default=1000.0, help="Content cost")
    run_parser.add_argument("--marketing-cost", type=float, default=500.0, help="Marketing cost")
    run_parser.add_argument("--platform-fee", type=float, default=0.05, help="Platform fee")
    run_parser.add_argument("--months", type=int, default=12, help="Max months")
    run_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    run_parser.add_argument("--output", type=str, default=None, help="Output file path")
    run_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze simulation results")
    analyze_parser.add_argument("--input", type=str, required=True, help="Input file path")
    analyze_parser.add_argument("--output", type=str, default=None, help="Output file path")

    return parser


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "run":
        run_simulation(args)
    elif args.command == "analyze":
        analyze_results(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
