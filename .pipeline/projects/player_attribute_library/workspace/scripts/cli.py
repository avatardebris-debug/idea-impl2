#!/usr/bin/env python3
"""CLI for the player attribute library.

Usage:
    player-attr-cli create --name "Player" --speed 80 --shooting 85 ... --output player.json
    player-attr-cli match --target-file target.json --candidates-file candidates.json --output matches.json
    player-attr-cli list --file players.json
"""

import argparse
import json
import sys
from pathlib import Path

from player_attribute_library import (
    PlayerAttribute,
    create_player,
    match_players,
    load_players,
)

DEFAULT_ATTRIBUTES = [
    "speed", "shooting", "passing",
    "defending", "physical", "mental",
]


def cmd_create(args: argparse.Namespace) -> None:
    """Handle the 'create' subcommand."""
    kwargs = {"name": args.name}
    for attr in DEFAULT_ATTRIBUTES:
        if getattr(args, attr, None) is not None:
            kwargs[attr] = float(getattr(args, attr))
    player = create_player(**kwargs)
    output = args.output or f"{args.name.lower().replace(' ', '_')}.json"
    Path(output).write_text(player.to_json())
    print(f"Player '{player.name}' saved to {output}")


def cmd_match(args: argparse.Namespace) -> None:
    """Handle the 'match' subcommand."""
    target_data = json.loads(Path(args.target_file).read_text())
    target = PlayerAttribute.from_dict(target_data["name"], target_data)

    candidates_data = json.loads(Path(args.candidates_file).read_text())
    candidates = [PlayerAttribute.from_dict(c["name"], c) for c in candidates_data]

    results = match_players(
        target, candidates,
        metric=args.metric,
        top_n=args.top_n,
    )
    output = args.output or "matches.json"
    output_data = [
        {
            "player": {"name": r["player"].name, **r["player"].to_dict()},
            "score": r["score"],
        }
        for r in results
    ]
    Path(output).write_text(json.dumps(output_data, indent=2))
    print(f"Matches saved to {output}")
    for r in results:
        print(f"  {r['player'].name}: {r['score']:.4f}")


def cmd_list(args: argparse.Namespace) -> None:
    """Handle the 'list' subcommand."""
    players = load_players(args.file)
    for p in players:
        attrs = ", ".join(f"{k}={v:.1f}" for k, v in p.to_dict().items())
        print(f"{p.name}: {attrs}")


def main() -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="player-attr-cli",
        description="Create, query, and match football player attribute profiles.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create
    create_parser = subparsers.add_parser("create", help="Create a player and save to JSON")
    create_parser.add_argument("--name", required=True, help="Player name")
    for attr in DEFAULT_ATTRIBUTES:
        create_parser.add_argument(f"--{attr}", type=float, help=f"{attr.capitalize()} (0-100)")
    create_parser.add_argument("--output", "-o", help="Output file path")

    # match
    match_parser = subparsers.add_parser("match", help="Match players against a target")
    match_parser.add_argument("--target-file", required=True, help="JSON file with target player")
    match_parser.add_argument("--candidates-file", required=True, help="JSON file with candidate players (array)")
    match_parser.add_argument("--metric", choices=["cosine", "euclidean"], default="cosine", help="Similarity metric")
    match_parser.add_argument("--top-n", type=int, default=10, help="Number of top matches to return")
    match_parser.add_argument("--output", "-o", help="Output file path")

    # list
    list_parser = subparsers.add_parser("list", help="List players in a JSON file")
    list_parser.add_argument("--file", "-f", required=True, help="JSON file with player(s)")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "match":
        cmd_match(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
