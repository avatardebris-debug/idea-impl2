"""CLI argument parsing and orchestration for FFO.

Provides the ``build_parser`` function that creates an argparse.ArgumentParser
with all supported flags, and the ``main`` function that ties parsing to the
optimizer.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from ffo.io_utils import load_json, save_json, IOError
from ffo.models.player import Player, FreeAgent
from ffo.models.salary_cap import SalaryCap
from ffo.models.free_agent_pool import FreeAgentPool
from ffo.optimizer import optimize_roster


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="ffo",
        description="Football Financial Optimizer — optimize a roster "
                    "by adding/subtracting free agents within a salary cap.",
    )
    parser.add_argument(
        "--roster",
        required=True,
        help="Path to a JSON file containing the current roster "
             "(list of player dicts).",
    )
    parser.add_argument(
        "--pool",
        required=True,
        help="Path to a JSON file containing the free agent pool "
             "(list of free agent dicts).",
    )
    parser.add_argument(
        "--cap",
        type=float,
        required=True,
        help="Salary cap limit in dollars (e.g. 150000000).",
    )
    parser.add_argument(
        "--age-weight",
        type=float,
        default=1.0,
        help="Weight for the age factor in valuation (default: 1.0).",
    )
    parser.add_argument(
        "--contract-weight",
        type=float,
        default=1.0,
        help="Weight for the contract factor in valuation (default: 1.0).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write the optimized roster JSON to. "
             "If omitted, output is printed to stdout.",
    )
    return parser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_players(data: list[dict]) -> list[Player]:
    """Convert a list of player dicts to Player objects.

    Args:
        data: List of dictionaries with player fields.

    Returns:
        List of Player instances.
    """
    players: list[Player] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError(f"Each roster entry must be a dict, got {type(item).__name__}")
        players.append(Player(**item))
    return players


def _parse_free_agents(data: list[dict]) -> list[FreeAgent]:
    """Convert a list of free agent dicts to FreeAgent objects.

    Args:
        data: List of dictionaries with free agent fields.

    Returns:
        List of FreeAgent instances.
    """
    agents: list[FreeAgent] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError(f"Each pool entry must be a dict, got {type(item).__name__}")
        agents.append(FreeAgent(**item))
    return agents


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    """Run the FFO optimizer from the command line.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 on success, 1 on error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load roster
    try:
        roster_data = load_json(args.roster)
    except IOError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not isinstance(roster_data, list):
        print("Error: Roster file must contain a JSON array of player objects.", file=sys.stderr)
        return 1

    # Load pool
    try:
        pool_data = load_json(args.pool)
    except IOError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not isinstance(pool_data, list):
        print("Error: Pool file must contain a JSON array of free agent objects.", file=sys.stderr)
        return 1

    # Validate cap
    if args.cap <= 0:
        print("Error: Salary cap must be a positive number.", file=sys.stderr)
        return 1

    # Parse objects
    try:
        roster = _parse_players(roster_data)
        agents = _parse_free_agents(pool_data)
    except (TypeError, KeyError) as exc:
        print(f"Error: Invalid player data — {exc}", file=sys.stderr)
        return 1

    # Run optimizer
    cap = SalaryCap(cap_limit=args.cap)
    pool = FreeAgentPool(agents)

    optimized = optimize_roster(
        roster=roster,
        cap=cap,
        pool=pool,
        age_weight=args.age_weight,
        contract_weight=args.contract_weight,
    )

    # Output
    output_data = [p.to_dict() for p in optimized]
    output_json = json.dumps(output_data, indent=2, default=str)

    if args.output:
        try:
            save_json(output_data, args.output)
            print(f"Optimized roster written to {args.output}", file=sys.stderr)
        except IOError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    else:
        print(output_json)

    return 0
