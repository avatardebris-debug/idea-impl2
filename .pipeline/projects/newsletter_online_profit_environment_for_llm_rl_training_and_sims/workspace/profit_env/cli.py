"""CLI module for the Newsletter Online Profit Environment."""

import argparse
import json
import csv
import sys
from typing import Optional
from .config import SimConfig
from .simulator import NewsletterSimulator


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for the CLI.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Newsletter Online Profit Environment - Simulation and Analysis Tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Sim subcommand
    sim_parser = subparsers.add_parser("sim", help="Simulation commands")
    sim_subparsers = sim_parser.add_subparsers(dest="sim_command", help="Simulation subcommands")
    
    # Sim run subcommand
    sim_run_parser = sim_subparsers.add_parser("run", help="Run a simulation")
    sim_run_parser.add_argument("--weeks", type=int, default=52, help="Number of weeks to simulate")
    sim_run_parser.add_argument("--subscribers", type=int, default=1000, help="Initial subscriber count")
    sim_run_parser.add_argument("--cpc", type=float, default=2.50, help="Cost per click for acquisition")
    sim_run_parser.add_argument("--retention", type=float, default=0.95, help="Subscriber retention rate")
    sim_run_parser.add_argument("--arpu", type=float, default=5.00, help="Average revenue per user")
    sim_run_parser.add_argument("--ad_rate", type=float, default=0.50, help="Revenue per subscriber from ads")
    sim_run_parser.add_argument("--sponsor_rate", type=float, default=100.00, help="Revenue per subscriber from sponsors")
    sim_run_parser.add_argument("--content_cost", type=float, default=500.00, help="Weekly content creation cost")
    sim_run_parser.add_argument("--operational_cost", type=float, default=300.00, help="Weekly operational cost")
    sim_run_parser.add_argument("--growth", type=float, default=0.1, help="Growth rate")
    sim_run_parser.add_argument("--churn", type=float, default=0.05, help="Churn rate")
    sim_run_parser.add_argument("--seasonal", type=float, default=1.0, help="Seasonal factor")
    sim_run_parser.add_argument("--competitors", type=int, default=5, help="Number of competitors")
    sim_run_parser.add_argument("--saturation", type=float, default=0.3, help="Market saturation")
    sim_run_parser.add_argument("--conversion", type=float, default=0.02, help="Conversion rate")
    sim_run_parser.add_argument("--engagement", type=float, default=0.75, help="Engagement score")
    sim_run_parser.add_argument("--sponsor_fill", type=float, default=0.8, help="Sponsor fill rate")
    sim_run_parser.add_argument("--refund", type=float, default=0.01, help="Refund rate")
    sim_run_parser.add_argument("--tax", type=float, default=0.25, help="Tax rate")
    sim_run_parser.add_argument("--discount", type=float, default=0.1, help="Discount rate")
    
    # Sim stats subcommand
    sim_stats_parser = sim_subparsers.add_parser("stats", help="Show simulation statistics")
    sim_stats_parser.add_argument("--weeks", type=int, default=52, help="Number of weeks to simulate")
    sim_stats_parser.add_argument("--subscribers", type=int, default=1000, help="Initial subscriber count")
    sim_stats_parser.add_argument("--cpc", type=float, default=2.50, help="Cost per click for acquisition")
    sim_stats_parser.add_argument("--retention", type=float, default=0.95, help="Subscriber retention rate")
    sim_stats_parser.add_argument("--arpu", type=float, default=5.00, help="Average revenue per user")
    sim_stats_parser.add_argument("--ad_rate", type=float, default=0.50, help="Revenue per subscriber from ads")
    sim_stats_parser.add_argument("--sponsor_rate", type=float, default=100.00, help="Revenue per subscriber from sponsors")
    sim_stats_parser.add_argument("--content_cost", type=float, default=500.00, help="Weekly content creation cost")
    sim_stats_parser.add_argument("--operational_cost", type=float, default=300.00, help="Weekly operational cost")
    sim_stats_parser.add_argument("--growth", type=float, default=0.1, help="Growth rate")
    sim_stats_parser.add_argument("--churn", type=float, default=0.05, help="Churn rate")
    sim_stats_parser.add_argument("--seasonal", type=float, default=1.0, help="Seasonal factor")
    sim_stats_parser.add_argument("--competitors", type=int, default=5, help="Number of competitors")
    sim_stats_parser.add_argument("--saturation", type=float, default=0.3, help="Market saturation")
    sim_stats_parser.add_argument("--conversion", type=float, default=0.02, help="Conversion rate")
    sim_stats_parser.add_argument("--engagement", type=float, default=0.75, help="Engagement score")
    sim_stats_parser.add_argument("--sponsor_fill", type=float, default=0.8, help="Sponsor fill rate")
    sim_stats_parser.add_argument("--refund", type=float, default=0.01, help="Refund rate")
    sim_stats_parser.add_argument("--tax", type=float, default=0.25, help="Tax rate")
    sim_stats_parser.add_argument("--discount", type=float, default=0.1, help="Discount rate")
    
    # Sim export subcommand
    sim_export_parser = sim_subparsers.add_parser("export", help="Export simulation results")
    sim_export_parser.add_argument("--weeks", type=int, default=52, help="Number of weeks to simulate")
    sim_export_parser.add_argument("--subscribers", type=int, default=1000, help="Initial subscriber count")
    sim_export_parser.add_argument("--cpc", type=float, default=2.50, help="Cost per click for acquisition")
    sim_export_parser.add_argument("--retention", type=float, default=0.95, help="Subscriber retention rate")
    sim_export_parser.add_argument("--arpu", type=float, default=5.00, help="Average revenue per user")
    sim_export_parser.add_argument("--ad_rate", type=float, default=0.50, help="Revenue per subscriber from ads")
    sim_export_parser.add_argument("--sponsor_rate", type=float, default=100.00, help="Revenue per subscriber from sponsors")
    sim_export_parser.add_argument("--content_cost", type=float, default=500.00, help="Weekly content creation cost")
    sim_export_parser.add_argument("--operational_cost", type=float, default=300.00, help="Weekly operational cost")
    sim_export_parser.add_argument("--growth", type=float, default=0.1, help="Growth rate")
    sim_export_parser.add_argument("--churn", type=float, default=0.05, help="Churn rate")
    sim_export_parser.add_argument("--seasonal", type=float, default=1.0, help="Seasonal factor")
    sim_export_parser.add_argument("--competitors", type=int, default=5, help="Number of competitors")
    sim_export_parser.add_argument("--saturation", type=float, default=0.3, help="Market saturation")
    sim_export_parser.add_argument("--conversion", type=float, default=0.02, help="Conversion rate")
    sim_export_parser.add_argument("--engagement", type=float, default=0.75, help="Engagement score")
    sim_export_parser.add_argument("--sponsor_fill", type=float, default=0.8, help="Sponsor fill rate")
    sim_export_parser.add_argument("--refund", type=float, default=0.01, help="Refund rate")
    sim_export_parser.add_argument("--tax", type=float, default=0.25, help="Tax rate")
    sim_export_parser.add_argument("--discount", type=float, default=0.1, help="Discount rate")
    sim_export_parser.add_argument("--output", type=str, required=True, help="Output file path")
    sim_export_parser.add_argument("--format", type=str, default="json", choices=["json", "csv"], help="Output format")
    
    return parser


def run_simulation(args: argparse.Namespace) -> int:
    """Execute the run command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config = SimConfig(
            subscriber_count=args.subscribers,
            retention_rate=args.retention,
            growth_rate=args.growth,
            churn_rate=args.churn,
            arpu=args.arpu,
            ad_rate=args.ad_rate,
            sponsor_rate=args.sponsor_rate,
            content_cost=args.content_cost,
            operational_cost=args.operational_cost,
            cpc=args.cpc,
            seasonal_factor=args.seasonal,
            competitor_count=args.competitors,
            market_saturation=args.saturation,
            conversion_rate=args.conversion,
            engagement_rate=args.engagement,
            sponsorship_fill_rate=args.sponsor_fill,
            refund_rate=args.refund,
            tax_rate=args.tax,
            discount_rate=args.discount
        )
        
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(args.weeks)
        
        stats = history.get_statistics()
        print("Simulation Results:")
        print(f"  Total Revenue: ${stats['total_revenue']:,.2f}")
        print(f"  Total Costs: ${stats['total_costs']:,.2f}")
        print(f"  Net Profit: ${stats['net_profit']:,.2f}")
        print(f"  Average Subscribers: {stats['avg_subscribers']:,.0f}")
        print(f"  Final Subscribers: {stats['final_subscribers']:,}")
        print(f"  Final Cumulative Profit: ${stats['final_cumulative_profit']:,.2f}")
        print(f"  Average Churn Rate: {stats['avg_churn_rate']:.2%}")
        print(f"  Total Acquired: {stats['total_acquired']:,}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def run_stats(args: argparse.Namespace) -> int:
    """Execute the stats command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        config = SimConfig(
            subscriber_count=args.subscribers,
            retention_rate=args.retention,
            growth_rate=args.growth,
            churn_rate=args.churn,
            arpu=args.arpu,
            ad_rate=args.ad_rate,
            sponsor_rate=args.sponsor_rate,
            content_cost=args.content_cost,
            operational_cost=args.operational_cost,
            cpc=args.cpc,
            seasonal_factor=args.seasonal,
            competitor_count=args.competitors,
            market_saturation=args.saturation,
            conversion_rate=args.conversion,
            engagement_rate=args.engagement,
            sponsorship_fill_rate=args.sponsor_fill,
            refund_rate=args.refund,
            tax_rate=args.tax,
            discount_rate=args.discount
        )
        
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(args.weeks)
        
        stats = history.get_statistics()
        print("Simulation Statistics:")
        print(f"  Total Revenue: ${stats['total_revenue']:,.2f}")
        print(f"  Total Costs: ${stats['total_costs']:,.2f}")
        print(f"  Net Profit: ${stats['net_profit']:,.2f}")
        print(f"  Average Subscribers: {stats['avg_subscribers']:,.0f}")
        print(f"  Final Subscribers: {stats['final_subscribers']:,}")
        print(f"  Final Cumulative Profit: ${stats['final_cumulative_profit']:,.2f}")
        print(f"  Average Churn Rate: {stats['avg_churn_rate']:.2%}")
        print(f"  Total Acquired: {stats['total_acquired']:,}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def run_export(args: argparse.Namespace) -> int:
    """Execute the export command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Validate format
        if args.format not in ["json", "csv"]:
            print(f"Error: Invalid format '{args.format}'. Must be 'json' or 'csv'", file=sys.stderr)
            sys.exit(1)
        
        config = SimConfig(
            subscriber_count=args.subscribers,
            retention_rate=args.retention,
            growth_rate=args.growth,
            churn_rate=args.churn,
            arpu=args.arpu,
            ad_rate=args.ad_rate,
            sponsor_rate=args.sponsor_rate,
            content_cost=args.content_cost,
            operational_cost=args.operational_cost,
            cpc=args.cpc,
            seasonal_factor=args.seasonal,
            competitor_count=args.competitors,
            market_saturation=args.saturation,
            conversion_rate=args.conversion,
            engagement_rate=args.engagement,
            sponsorship_fill_rate=args.sponsor_fill,
            refund_rate=args.refund,
            tax_rate=args.tax,
            discount_rate=args.discount
        )
        
        simulator = NewsletterSimulator(config)
        history = simulator.run_simulation(args.weeks)
        
        weekly_data = history.get_weekly_data()
        
        if args.format == "json":
            with open(args.output, "w") as f:
                json.dump(weekly_data, f, indent=2)
        elif args.format == "csv":
            if weekly_data:
                fieldnames = weekly_data[0].keys()
                with open(args.output, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(weekly_data)
        
        print(f"Results exported to {args.output}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point for the CLI.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command is None:
        parser.print_help()
        return 1
    
    if parsed_args.command == "sim":
        if parsed_args.sim_command is None:
            parser.parse_args(["sim", "-h"])
            return 1
        
        if parsed_args.sim_command == "run":
            return run_simulation(parsed_args)
        elif parsed_args.sim_command == "stats":
            return run_stats(parsed_args)
        elif parsed_args.sim_command == "export":
            return run_export(parsed_args)
        else:
            parser.parse_args(["sim", "-h"])
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
