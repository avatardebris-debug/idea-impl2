"""Demo script — runs a full game session programmatically."""

import json
from agentic_mirroring_game.core.game_engine import GameEngine
from agentic_mirroring_game.core.player import Player
from agentic_mirroring_game.core.empire import Empire
from agentic_mirroring_game.core.models import Resources, Territory, Building


def run_demo():
    """Run a complete demo game session end-to-end."""
    print("=" * 60)
    print("  AGENTIC MIRRORING GAME — Demo Session")
    print("=" * 60)

    # Create engine and start game
    engine = GameEngine(player_name="DemoPlayer")
    state = engine.start_game("DemoPlayer")
    print("\n[GAME STARTED]")
    print(json.dumps(state, indent=2))

    # Perform initial actions
    print("\n--- Action: Gather Resources ---")
    result = engine.process_action("gather_resources", amount=50)
    print(json.dumps(result, indent=2))

    # Run demo session
    print("\n--- Running Demo Session (5 turns) ---")
    results = engine.run_demo_session(num_turns=5)

    for r in results:
        print(f"\n[Turn {r['turn']}]")
        print(json.dumps(r['state'], indent=2))

    # Print mirroring events
    print("\n--- Mirroring Events ---")
    events = engine.mirroring_bridge.get_events()
    for event in events:
        print(json.dumps(event, indent=2))

    # Final state
    final_state = engine.get_state()
    print("\n--- Final Empire State ---")
    print(json.dumps(final_state, indent=2))

    print("\n" + "=" * 60)
    print("  Demo complete! Empire Score:", final_state['empire_score'])
    print("=" * 60)

    return engine


if __name__ == "__main__":
    run_demo()
