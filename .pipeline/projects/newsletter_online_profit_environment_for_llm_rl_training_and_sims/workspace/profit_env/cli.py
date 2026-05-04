"""CLI module for the Newsletter Online Profit Environment."""

import argparse
import json
import csv
import sys
from typing import List, Optional
from .config import SimConfig
from .simulator import NewsletterSimulator


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.
    
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Newsletter Online Profit Environment - Simulation and Analysis Tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sim subcommand
    sim_parser = subparsers.add_parser("sim", help="Simulation commands", add_help=False)
    sim_subparsers = sim_parser.add_subparsers(dest="sim_command", help="Simulation subcommands")
    
    # Sim run subcommand
    run_parser = sim_subparsers.add_parser("run", help="Run a simulation")
    _add_common_args(run_parser)
    
    # Sim stats subcommand
    stats_parser = sim_subparsers.add_parser("stats", help="Run simulation and print statistics")
    _add_common_args(stats_parser)
    
    # Sim export subcommand
    export_parser = sim_subparsers.add_parser("export", help="Run simulation and export results")
    _add_common_args(export_parser)
    export_parser.add_argument("--output", "-o", type=str, help="Output file path")
    export_parser.add_argument("--format", "-f", type=str, default="json", choices=["json", "csv"],
                               help="Output format (json or csv)")
    
    return parser


def _add_common_args(parser: argparse.ArgumentParser):
    """Add common simulation arguments to a parser.
    
    Args:
        parser: ArgumentParser to add arguments to.
    """
    parser.add_argument("--weeks", "-w", type=int, default=52, help="Number of weeks to simulate")
    parser.add_argument("--subscribers", "-s", type=int, default=1000, help="Initial subscriber count")
    parser.add_argument("--cpc", type=float, default=2.50, help="Cost per click for acquisition")
    parser.add_argument("--retention", type=float, default=0.95, help="Weekly retention rate")
    parser.add_argument("--arpu", type=float, default=5.00, help="Average revenue per user")
    parser.add_argument("--ad-rate", type=float, default=0.50, help="Revenue per subscriber from ads")
    parser.add_argument("--sponsor-rate", type=float, default=100.00, help="Revenue per sponsor")
    parser.add_argument("--content-cost", type=float, default=500.00, help="Weekly content production cost")
    parser.add_argument("--operational-cost", type=float, default=300.00, help="Weekly operational cost")
    parser.add_argument("--growth", type=float, default=0.1, help="Weekly growth rate")
    parser.add_argument("--churn", type=float, default=0.05, help="Weekly churn rate")
    parser.add_argument("--seasonal", type=float, default=1.0, help="Seasonal factor")
    parser.add_argument("--competitors", type=int, default=5, help="Number of competitors")
    parser.add_argument("--saturation", type=float, default=0.3, help="Market saturation")
    parser.add_argument("--conversion", type=float, default=0.02, help="Conversion rate")
    parser.add_argument("--engagement", type=float, default=0.75, help="Engagement rate")
    parser.add_argument("--sponsor-fill", type=float, default=0.8, help="Sponsorship fill rate")
    parser.add_argument("--refund", type=float, default=0.01, help="Refund rate")
    parser.add_argument("--tax", type=float, default=0.25, help="Tax rate")
    parser.add_argument("--discount", type=float, default=0.1, help="Discount rate")


def run_simulation(args) -> List[dict]:
    """Run a simulation with the given arguments.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        List of dictionaries containing weekly results.
    """
    config = SimConfig(
        subscriber_count=args.subscribers,
        retention_rate=args.retention,
        churn_rate=args.churn,
        growth_rate=args.growth,
        cpc=args.cpc,
        arpu=args.arpu,
        ad_rate=args.ad_rate,
        sponsor_rate=args.sponsor_rate,
        content_cost=args.content_cost,
        operational_cost=args.operational_cost,
        seasonal_factor=args.seasonal,
        competitor_count=args.competitors,
        market_saturation=args.saturation,
        conversion_rate=args.conversion,
        engagement_rate=args.engagement,
        sponsorship_fill_rate=args.sponsor_fill,
        refund_rate=args.refund,
        tax_rate=args.tax,
        discount_rate=args.discount,
    )
    
    simulator = NewsletterSimulator(config=config)
    results = simulator.run_simulation(weeks=args.weeks)
    
    return results


def run_stats(args):
    """Run a simulation and print statistics.
    
    Args:
        args: Parsed command-line arguments.
    """
    results = run_simulation(args)
    
    if not results:
        print("No results to display.")
        return
    
    # Calculate summary statistics
    total_revenue = sum(r["revenue"] for r in results)
    total_costs = sum(r["costs"] for r in results)
    total_profit = sum(r["profit"] for r in results)
    avg_weekly_revenue = total_revenue / len(results)
    avg_weekly_profit = total_profit / len(results)
    final_subscribers = results[-1]["subscribers"]
    total_churned = sum(r["churned"] for r in results)
    total_acquired = sum(r["acquired"] for r in results)
    
    print(f"Simulation Results ({args.weeks} weeks):")
    print(f"  Final Subscribers: {final_subscribers}")
    print(f"  Total Revenue: ${total_revenue:,.2f}")
    print(f"  Total Costs: ${total_costs:,.2f}")
    print(f"  Total Profit: ${total_profit:,.2f}")
    print(f"  Avg Weekly Revenue: ${avg_weekly_revenue:,.2f}")
    print(f"  Avg Weekly Profit: ${avg_weekly_profit:,.2f}")
    print(f"  Total Churned: {total_churned}")
    print(f"  Total Acquired: {total_acquired}")


def run_export(args):
    """Run a simulation and export results.
    
    Args:
        args: Parsed command-line arguments.
    """
    if not args.output:
        print("Error: --output is required for export command", file=sys.stderr)
        sys.exit(1)
    
    results = run_simulation(args)
    
    if not results:
        print("No results to export.", file=sys.stderr)
        sys.exit(1)
    
    if args.format == "json":
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
    elif args.format == "csv":
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"Results exported to {args.output}")


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "sim":
        if not hasattr(args, "sim_command") or not args.sim_command:
            parser.parse_args(["sim", "--help"])
            sys.exit(1)
        
        if args.sim_command == "run":
            run_simulation(args)
        elif args.sim_command == "stats":
            run_stats(args)
        elif args.sim_command == "export":
            run_export(args)
        else:
            parser.parse_args(["sim", args.sim_command, "--help"])
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
