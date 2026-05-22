"""CLI entry point for the Agentic Mirroring Game."""

import argparse
import sys
import json

from agentic_mirroring_game.core.game_engine import GameEngine
from agentic_mirroring_game.core.player import Player
from agentic_mirroring_game.core.empire import Empire


def _print_state(state: dict) -> None:
    """Pretty-print the current game state."""
    print("\n" + "=" * 50)
    print(f"  TURN {state['turn']} — Empire of {state['player_name']}")
    print("=" * 50)
    print(f"  Resources:  Gold={state['resources']['gold']}, "
          f"Wood={state['resources']['wood']}, "
          f"Stone={state['resources']['stone']}, "
          f"Food={state['resources']['food']}")
    print(f"  Population: {state['resources']['population']}")
    print(f"  Territory:  {state['territory']['tiles_controlled']}/{state['territory']['max_tiles']} tiles")
    print(f"  Buildings:  {len(state['buildings'])}")
    for b in state['buildings']:
        print(f"    - {b['name']} (Lv.{b['level']})")
    print(f"  Empire Score: {state['empire_score']}")
    print("=" * 50 + "\n")


def _print_events(events: list) -> None:
    """Pretty-print mirroring events."""
    if not events:
        return
    print("\n" + "-" * 50)
    print("  MIRRORING EVENTS")
    print("-" * 50)
    for event in events:
        print(f"  [{event['event_type']}] Turn {event['turn']}")
        if event.get('data'):
            for k, v in event['data'].items():
                if k != 'state':
                    print(f"    {k}: {v}")
    print("-" * 50 + "\n")


def cmd_start(args: argparse.Namespace) -> None:
    """Start an interactive game session."""
    engine = GameEngine(player_name=args.player or "Player")
    state = engine.start_game(args.player or "Player")
    _print_state(state)

    actions = [
        "gather_resources",
        "expand_territory",
        "recruit_units",
        "build_structure",
        "trade",
        "quit",
    ]

    while not engine.game_over:
        print("Available actions:")
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")

        try:
            choice = input("\nChoose action (number): ").strip()
            idx = int(choice) - 1
            if idx < 0 or idx >= len(actions):
                print("Invalid choice.")
                continue
        except (ValueError, EOFError):
            print("Exiting game.")
            break

        action = actions[idx]
        if action == "quit":
            print("Game ended by player.")
            break

        if action == "gather_resources":
            amount = int(input("Amount to gather: ") or "10")
            result = engine.process_action("gather_resources", amount=amount)
        elif action == "expand_territory":
            tiles = int(input("Tiles to expand: ") or "5")
            result = engine.process_action("expand_territory", tiles=tiles)
        elif action == "recruit_units":
            count = int(input("Units to recruit: ") or "5")
            result = engine.process_action("recruit_units", count=count)
        elif action == "build_structure":
            building = input("Building name (farm/mine/barracks/market): ") or "farm"
            result = engine.process_action("build_structure", building=building)
        elif action == "trade":
            res_from = input("Resource to trade from (gold/wood/stone/food): ") or "gold"
            amount = int(input("Amount: ") or "10")
            res_to = input("Resource to receive (gold/wood/stone/food): ") or "wood"
            result = engine.process_action("trade", resource_from=res_from, amount=amount, resource_to=res_to)

        if result.get("success"):
            print(f"  ✓ {result['action']} succeeded!")
        else:
            print(f"  ✗ {result.get('error', 'Action failed')}")

        # Process turn
        state = engine.process_turn()
        _print_state(state)

    _print_events(engine.mirroring_bridge.get_events())
    print(f"Game Over! Final Empire Score: {state['empire_score']}")


def cmd_demo(args: argparse.Namespace) -> None:
    """Run a demo game session programmatically."""
    engine = GameEngine(player_name=args.player or "DemoPlayer")
    state = engine.start_game(args.player or "DemoPlayer")
    _print_state(state)

    num_turns = args.turns or 5
    results = engine.run_demo_session(num_turns=num_turns)

    for r in results:
        print(f"\n--- After Turn {r['turn']} ---")
        _print_state(r['state'])

    _print_events(engine.mirroring_bridge.get_events())
    final_state = engine.get_state()
    print(f"Demo complete! Final Empire Score: {final_state['empire_score']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agentic-mirroring-game",
        description="Agentic Mirroring Game — Build your empire!",
    )
    subparsers = parser.add_subparsers(dest="command")

    # start command
    start_parser = subparsers.add_parser("start", help="Start interactive game")
    start_parser.add_argument("--player", "-p", type=str, default="Player", help="Player name")

    # demo command
    demo_parser = subparsers.add_parser("demo", help="Run demo game session")
    demo_parser.add_argument("--player", "-p", type=str, default="DemoPlayer", help="Player name")
    demo_parser.add_argument("--turns", "-t", type=int, default=5, help="Number of turns")

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args)
    elif args.command == "demo":
        cmd_demo(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
