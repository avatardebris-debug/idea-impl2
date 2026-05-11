"""CLI interface for the sports betting strategy simulator.

Accepts parameters (odds format, odds value, true probability, bankroll, stake fraction,
number of bets, strategy type, seed) and runs a full simulation.
Prints a readable text report with all performance metrics.
"""

from __future__ import annotations
import argparse
import sys

from ..engine.market import Market, BetType, OddsFormat
from ..engine.monte_carlo import MonteCarloEngine
from ..strategies.kelly import KellyStrategy, FixedStakeStrategy
from ..backtest.bankroll import Bankroll
from ..backtest.runner import BacktestRunner
from ..backtest.metrics import MetricsCalculator


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Sports Betting Strategy Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default run: 2% Kelly on +150 odds with 55% true probability over 1000 bets
  python main.py

  # Custom parameters
  python main.py --odds-american +150 --true-probability 0.55 --bankroll 10000 --n-bets 5000 --strategy kelly --kelly-fraction 0.5 --seed 42

  # Fixed stake strategy
  python main.py --odds-decimal 2.0 --true-probability 0.55 --bankroll 1000 --n-bets 1000 --strategy fixed --stake-fraction 0.02
        """,
    )

    # Odds parameters
    odds_group = parser.add_argument_group("Odds parameters")
    odds_group.add_argument(
        "--odds-decimal",
        type=float,
        default=None,
        help="Decimal odds (e.g., 2.50)",
    )
    odds_group.add_argument(
        "--odds-american",
        type=str,
        default=None,
        help="American odds (e.g., +150 or -110)",
    )
    odds_group.add_argument(
        "--odds-fractional",
        type=str,
        default=None,
        help="Fractional odds (e.g., 3/2)",
    )

    # Market parameters
    market_group = parser.add_argument_group("Market parameters")
    market_group.add_argument(
        "--bet-type",
        type=str,
        default="moneyline",
        choices=["moneyline", "point_spread", "over_under"],
        help="Type of bet (default: moneyline)",
    )
    market_group.add_argument(
        "--true-probability",
        type=float,
        default=0.55,
        help="True probability of the outcome (default: 0.55)",
    )

    # Bankroll parameters
    bankroll_group = parser.add_argument_group("Bankroll parameters")
    bankroll_group.add_argument(
        "--bankroll",
        type=float,
        default=10000.0,
        help="Initial bankroll (default: 10000)",
    )
    bankroll_group.add_argument(
        "--n-bets",
        type=int,
        default=1000,
        help="Number of bets to simulate (default: 1000)",
    )

    # Strategy parameters
    strategy_group = parser.add_argument_group("Strategy parameters")
    strategy_group.add_argument(
        "--strategy",
        type=str,
        default="kelly",
        choices=["kelly", "fixed"],
        help="Betting strategy (default: kelly)",
    )
    strategy_group.add_argument(
        "--kelly-fraction",
        type=float,
        default=1.0,
        help="Fraction of full Kelly to bet (default: 1.0)",
    )
    strategy_group.add_argument(
        "--stake-fraction",
        type=float,
        default=0.02,
        help="Fixed stake fraction (used with --strategy fixed, default: 0.02)",
    )

    # Simulation parameters
    sim_group = parser.add_argument_group("Simulation parameters")
    sim_group.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    return parser.parse_args(argv)


def create_market(args: argparse.Namespace) -> Market:
    """Create a Market object from parsed arguments.

    Args:
        args: Parsed arguments namespace.

    Returns:
        Market object.
    """
    # Determine odds format
    if args.odds_decimal is not None:
        odds_decimal = args.odds_decimal
        odds_american = None
        odds_fractional = None
    elif args.odds_american is not None:
        odds_decimal = None
        odds_american = int(args.odds_american)
        odds_fractional = None
    elif args.odds_fractional is not None:
        parts = args.odds_fractional.split("/")
        if len(parts) != 2:
            raise ValueError("Fractional odds must be in format 'numerator/denominator' (e.g., 3/2)")
        odds_decimal = None
        odds_american = None
        odds_fractional = (int(parts[0]), int(parts[1]))
    else:
        # Default: +150 American odds
        odds_decimal = None
        odds_american = 150
        odds_fractional = None

    bet_type = BetType(args.bet_type)
    true_prob = args.true_probability

    return Market(
        bet_type=bet_type,
        odds_decimal=odds_decimal,
        odds_american=odds_american,
        odds_fractional=odds_fractional,
        true_probability=true_prob,
    )


def create_strategy(args: argparse.Namespace) -> object:
    """Create a Strategy object from parsed arguments.

    Args:
        args: Parsed arguments namespace.

    Returns:
        Strategy object.
    """
    if args.strategy == "kelly":
        return KellyStrategy(fractional_factor=args.kelly_fraction)
    elif args.strategy == "fixed":
        return FixedStakeStrategy(stake_fraction=args.stake_fraction)
    else:
        raise ValueError(f"Unknown strategy: {args.strategy}")


def format_report(
    market: Market,
    strategy: object,
    metrics: dict[str, float],
    n_bets: int,
    seed: int,
) -> str:
    """Format a readable text report of the simulation results.

    Args:
        market: The Market object used in the simulation.
        strategy: The Strategy object used.
        metrics: Dictionary of computed metrics.
        n_bets: Number of bets simulated.
        seed: Random seed used.

    Returns:
        Formatted report string.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("SPORTS BETTING STRATEGY SIMULATOR - RESULTS")
    lines.append("=" * 60)
    lines.append("")
    lines.append("MARKET PARAMETERS")
    lines.append("-" * 40)
    lines.append(f"  Bet Type:           {market.bet_type.value}")
    lines.append(f"  Decimal Odds:       {market.odds_decimal:.2f}")
    lines.append(f"  American Odds:      {market.odds_american:+d}")
    lines.append(f"  Fractional Odds:    {market.odds_fractional[0]}/{market.odds_fractional[1]}")
    lines.append(f"  Implied Probability: {market.implied_probability:.4f}")
    lines.append(f"  True Probability:   {market.true_probability:.4f}")
    lines.append(f"  Edge:               {market.edge:.4f}")
    lines.append("")
    lines.append("STRATEGY PARAMETERS")
    lines.append("-" * 40)
    lines.append(f"  Strategy:           {strategy}")
    lines.append(f"  Number of Bets:     {n_bets}")
    lines.append(f"  Random Seed:        {seed}")
    lines.append("")
    lines.append("PERFORMANCE METRICS")
    lines.append("-" * 40)
    lines.append(f"  Final Bankroll:     ${metrics['final_bankroll']:,.2f}")
    lines.append(f"  Total Return:       {metrics['total_return']:.2%}")
    lines.append(f"  ROI:                {metrics['roi']:.2%}")
    lines.append(f"  Win Rate:           {metrics['win_rate']:.2%}")
    lines.append(f"  Max Drawdown:       {metrics['max_drawdown']:.2%}")
    lines.append(f"  Sharpe Ratio:       {metrics['sharpe_ratio']:.4f}")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    args = parse_args(argv)

    # Create market
    market = create_market(args)

    # Create strategy
    strategy = create_strategy(args)

    # Create bankroll
    bankroll = Bankroll(initial_bankroll=args.bankroll)

    # Run backtest
    runner = BacktestRunner(
        strategy=strategy,
        market=market,
        bankroll=bankroll,
        n_bets=args.n_bets,
        seed=args.seed,
    )
    records = runner.run()

    # Compute metrics
    calculator = MetricsCalculator(records, args.bankroll)
    metrics = calculator.compute()

    # Print report
    report = format_report(market, strategy, metrics, args.n_bets, args.seed)
    print(report)


if __name__ == "__main__":
    main()
