"""
CLI entry point for dfs_arb.

Provides command-line interface for running arbitrage detection,
promo evaluation, and data processing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from dfs_arb.core.models import OddsEntry, MarketType, PromoOffer, PromoType
from dfs_arb.core.odds import american_to_decimal
from dfs_arb.core.arbitrage import find_arbitrage, find_arbitrage_with_bankroll
from dfs_arb.core.promos import evaluate_promo, evaluate_all_promos
from dfs_arb.core.engine import ArbEngine


def load_sample_data() -> dict:
    """Load sample data from the package data directory."""
    data_path = Path(__file__).parent / "data" / "sample_data.json"
    with open(data_path, "r") as f:
        return json.load(f)


def odds_entries_from_sample(market_data: dict) -> List[OddsEntry]:
    """Convert sample market data to OddsEntry objects."""
    entries = []
    for market in market_data.get("markets", []):
        market_id = market["market_id"]
        market_type = MarketType(market["market_type"])
        event_name = market["event_name"]
        event_date = market.get("event_date", "")
        sport = market.get("sport", "")

        for odds in market.get("odds", []):
            bookmaker = odds["bookmaker"]
            side = odds["side"]
            odds_value = odds["odds_value"]
            odds_format = odds.get("odds_format", "american")
            line_value = odds.get("line_value")

            if odds_format == "american":
                decimal_odds = american_to_decimal(odds_value)
            else:
                decimal_odds = odds_value

            entry = OddsEntry(
                market_id=market_id,
                market_type=market_type,
                event_name=event_name,
                event_date=event_date,
                sport=sport,
                bookmaker=bookmaker,
                side=side,
                decimal_odds=decimal_odds,
                line_value=line_value,
                odds_format=odds_format,
                odds_value=odds_value,
            )
            entries.append(entry)

    return entries


def promos_from_sample(promo_data: list) -> List[PromoOffer]:
    """Convert sample promo data to PromoOffer objects."""
    promos = []
    for promo in promo_data:
        offer = PromoOffer(
            promo_id=promo["promo_id"],
            promo_type=PromoType(promo["promo_type"]),
            provider=promo["provider"],
            description=promo["description"],
            max_bonus=promo["max_bonus"],
            min_deposit=promo.get("min_deposit", 0.0),
            rollover_requirement=promo.get("rollover_requirement", 1.0),
            expiry_date=promo.get("expiry_date"),
            eligible_markets=promo.get("eligible_markets", []),
            terms=promo.get("terms", ""),
        )
        promos.append(offer)
    return promos


def cmd_arbitrage(args: argparse.Namespace) -> None:
    """Run arbitrage detection."""
    # Load data
    sample_data = load_sample_data()
    entries = odds_entries_from_sample(sample_data)
    promos = promos_from_sample(sample_data.get("promos", []))

    # Create engine
    engine = ArbEngine(
        entries=entries,
        promos=promos,
        bankroll=args.bankroll if hasattr(args, "bankroll") and args.bankroll else 1000.0,
        min_profit_pct=args.min_profit if hasattr(args, "min_profit") else 0.5,
        max_stake_pct=args.max_stake_pct if hasattr(args, "max_stake_pct") else 0.1,
    )

    # Find opportunities
    opportunities = engine.find_arbitrage_opportunities()

    if not opportunities:
        print("No arbitrage opportunities found.")
        return

    print(f"\nFound {len(opportunities)} arbitrage opportunity(s):\n")

    for i, opp in enumerate(opportunities, 1):
        print(f"Opportunity #{i}:")
        print(f"  Market: {opp.event_name}")
        print(f"  Market Type: {opp.market_type.value}")
        print(f"  Total Implied Probability: {opp.total_implied_prob:.4f}")
        print(f"  Profit Percentage: {opp.profit_pct:.2f}%")
        print(f"  Total Stake: ${opp.total_stake:.2f}")
        print(f"  Guaranteed Profit: ${opp.guaranteed_profit:.2f}")
        print(f"  Stake Distribution:")
        for side, stake in opp.stake_distribution.items():
            print(f"    - {side}: ${stake:.2f}")
        print(f"  Outcomes:")
        for side, bookmaker, odds in opp.outcomes:
            print(f"    - {side} @ {bookmaker} ({odds:.2f})")
        print()


def cmd_promos(args: argparse.Namespace) -> None:
    """Run promo evaluation."""
    # Load data
    sample_data = load_sample_data()
    entries = odds_entries_from_sample(sample_data)
    promos = promos_from_sample(sample_data.get("promos", []))

    # Evaluate promos
    evaluations = evaluate_all_promos(promos, entries)

    if not evaluations:
        print("No promo evaluations available.")
        return

    print(f"\nEvaluated {len(evaluations)} promo(s):\n")

    for i, eval_result in enumerate(evaluations, 1):
        print(f"Promo #{i}:")
        print(f"  ID: {eval_result.promo.promo_id}")
        print(f"  Type: {eval_result.promo.promo_type.value}")
        print(f"  Provider: {eval_result.promo.provider}")
        print(f"  Description: {eval_result.promo.description}")
        print(f"  Expected Value: ${eval_result.expected_value:.2f}")
        print(f"  Profitable: {eval_result.is_profitable}")
        print(f"  Best Strategy: {eval_result.best_strategy}")
        print(f"  Risk Level: {eval_result.risk_level}")
        if eval_result.details:
            print(f"  Details:")
            for key, value in eval_result.details.items():
                print(f"    - {key}: {value}")
        print()


def cmd_engine(args: argparse.Namespace) -> None:
    """Run full engine analysis."""
    # Load data
    sample_data = load_sample_data()
    entries = odds_entries_from_sample(sample_data)
    promos = promos_from_sample(sample_data.get("promos", []))

    # Create engine
    engine = ArbEngine(
        entries=entries,
        promos=promos,
        bankroll=args.bankroll if hasattr(args, "bankroll") and args.bankroll else 1000.0,
        min_profit_pct=args.min_profit if hasattr(args, "min_profit") else 0.5,
        max_stake_pct=args.max_stake_pct if hasattr(args, "max_stake_pct") else 0.1,
    )

    # Run analysis
    results = engine.run_analysis()

    print("\n=== DFS Arb Analysis Results ===\n")

    print(f"Total Markets Analyzed: {results['total_markets']}")
    print(f"Total Bookmakers: {results['total_bookmakers']}")
    print(f"Arbitrage Opportunities: {len(results['arbitrage_opportunities'])}")
    print(f"Promo Evaluations: {len(results['promo_evaluations'])}")

    if results["arbitrage_opportunities"]:
        print("\n--- Arbitrage Opportunities ---")
        for opp in results["arbitrage_opportunities"]:
            print(f"  {opp.event_name}: {opp.profit_pct:.2f}% profit")

    if results["promo_evaluations"]:
        print("\n--- Promo Evaluations ---")
        for eval_result in results["promo_evaluations"]:
            if eval_result.is_profitable:
                print(f"  {eval_result.promo.provider} ({eval_result.promo.promo_type.value}): ${eval_result.expected_value:.2f} EV")

    print("\n=== End of Analysis ===\n")


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="DFS Arb - Sports Betting Arbitrage and Promo Hunter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m dfs_arb.cli arbitrage
  python -m dfs_arb.cli promos
  python -m dfs_arb.cli engine --bankroll 5000
  python -m dfs_arb.cli engine --min-profit 1.0 --max-stake-pct 0.05
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Arbitrage command
    arb_parser = subparsers.add_parser("arbitrage", help="Find arbitrage opportunities")
    arb_parser.add_argument(
        "--bankroll",
        type=float,
        default=1000.0,
        help="Total bankroll (default: 1000.0)",
    )
    arb_parser.add_argument(
        "--min-profit",
        type=float,
        default=0.5,
        help="Minimum profit percentage (default: 0.5)",
    )
    arb_parser.add_argument(
        "--max-stake-pct",
        type=float,
        default=0.1,
        help="Maximum stake as percentage of bankroll (default: 0.1)",
    )

    # Promos command
    promo_parser = subparsers.add_parser("promos", help="Evaluate promotional offers")

    # Engine command
    engine_parser = subparsers.add_parser("engine", help="Run full engine analysis")
    engine_parser.add_argument(
        "--bankroll",
        type=float,
        default=1000.0,
        help="Total bankroll (default: 1000.0)",
    )
    engine_parser.add_argument(
        "--min-profit",
        type=float,
        default=0.5,
        help="Minimum profit percentage (default: 0.5)",
    )
    engine_parser.add_argument(
        "--max-stake-pct",
        type=float,
        default=0.1,
        help="Maximum stake as percentage of bankroll (default: 0.1)",
    )

    args = parser.parse_args()

    if args.command == "arbitrage":
        cmd_arbitrage(args)
    elif args.command == "promos":
        cmd_promos(args)
    elif args.command == "engine":
        cmd_engine(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
