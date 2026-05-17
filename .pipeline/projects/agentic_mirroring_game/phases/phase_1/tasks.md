# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and package structure
  - What: Create the Python package skeleton with proper module layout, __init__.py files, and a pyproject.toml for importability
  - Files: agentic_mirroring_game/__init__.py, agentic_mirroring_game/core/__init__.py, agentic_mirroring_game/core/game_engine.py, agentic_mirroring_game/core/player.py, agentic_mirroring_game/core/empire.py, pyproject.toml
  - Done when: `pip install -e .` succeeds and `from agentic_mirroring_game.core import GameEngine, Player, Empire` imports without error

- [ ] Task 2: Core game engine — state management and turn loop
  - What: Implement the GameEngine class that manages the game state, processes player actions, and runs a turn-based loop. Include a basic data model for the game world (resources, territory, population)
  - Files: agentic_mirroring_game/core/game_engine.py (update), agentic_mirroring_game/core/models.py
  - Done when: GameEngine can be instantiated, a turn can be processed, and the engine exposes a `get_state()` method returning a serializable dict of the current game state

- [ ] Task 3: Player model and action system
  - What: Implement the Player class with attributes (name, resources, empire) and an action system that lets players perform actions (e.g., gather resources, expand territory, recruit units). Actions consume resources and produce outcomes
  - Files: agentic_mirroring_game/core/player.py (update), agentic_mirroring_game/core/actions.py
  - Done when: A Player can perform at least 3 different actions, each action modifies game state correctly, and actions can be chained in a turn loop

- [ ] Task 4: Empire building mechanics
  - What: Implement the Empire class that tracks territory, buildings, population growth, and resource production. Empire score determines progress toward the "real-life mirroring" goal
  - Files: agentic_mirroring_game/core/empire.py (update), agentic_mirroring_game/core/empire.py (buildings, territory, scoring)
  - Done when: Empire can be initialized with a starting state, buildings can be constructed, territory can expand, and an `empire_score` property reflects overall progress

- [ ] Task 5: Mirroring bridge — data pipeline from game to real-world interface
  - What: Implement a MirroringBridge class that maps game actions/state changes to a structured output format (JSON events) suitable for downstream integration (agentic commerce, robotics, etc.). Include a simple event log
  - Files: agentic_mirroring_game/core/mirroring.py, agentic_mirroring_game/core/events.py
  - Done when: MirroringBridge captures every game state change as a structured event, events are serializable to JSON, and the bridge exposes a `get_events()` method to retrieve the event log

- [ ] Task 6: CLI entry point and demo script
  - What: Create a CLI (`agentic-mirroring-game`) that starts a game, accepts player input, runs the turn loop, and outputs the current empire state and mirroring events. Include a demo script that runs a full game session programmatically
  - Files: agentic_mirroring_game/cli.py, agentic_mirroring_game/demo.py, pyproject.toml (scripts entry)
  - Done when: Running `agentic-mirroring-game demo` executes a complete game session end-to-end, prints empire state and mirroring events, and exits cleanly