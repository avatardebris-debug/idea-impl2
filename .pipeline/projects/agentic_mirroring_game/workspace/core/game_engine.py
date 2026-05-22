"""Core game engine — state management and turn loop."""

from typing import Dict, List, Optional, Any

from agentic_mirroring_game.core.models import GameState, Resources, Territory, Building
from agentic_mirroring_game.core.player import Player
from agentic_mirroring_game.core.empire import Empire
from agentic_mirroring_game.core.mirroring import MirroringBridge


class GameEngine:
    """Manages game state, processes player actions, and runs a turn-based loop."""

    def __init__(self, player_name: str = "Player"):
        self._state = GameState(player_name=player_name)
        self._player = Player(
            name=player_name,
            resources=Resources(gold=100, wood=50, stone=30, food=80, population=10),
            empire=Empire(
                territory=Territory(tiles_controlled=1, expansion_level=0),
                buildings=[],
            ),
        )
        self._mirroring_bridge = MirroringBridge(player_name=player_name)
        self._turn_count = 0
        self._game_over = False

    @property
    def player(self) -> Player:
        return self._player

    @property
    def mirroring_bridge(self) -> MirroringBridge:
        return self._mirroring_bridge

    @property
    def turn_count(self) -> int:
        return self._turn_count

    @property
    def game_over(self) -> bool:
        return self._game_over

    def get_state(self) -> Dict[str, Any]:
        """Return a serializable dict of the current game state."""
        return self._state.to_dict()

    def process_turn(self) -> Dict[str, Any]:
        """Process one turn: apply resource production, update empire score, log events."""
        self._turn_count += 1
        self._state.turn = self._turn_count

        # Resource production from buildings
        for building in self._player.empire.buildings:
            for res, amount in building.resource_production.items():
                if res == "gold":
                    self._player.resources.gold += amount
                elif res == "wood":
                    self._player.resources.wood += amount
                elif res == "stone":
                    self._player.resources.stone += amount
                elif res == "food":
                    self._player.resources.food += amount

        # Population growth from buildings
        pop_growth = sum(
            b.resource_production.get("population", 0) for b in self._player.empire.buildings
        )
        self._player.resources.population += pop_growth

        # Update empire score
        self._player.empire.calculate_score()
        self._state.empire_score = self._player.empire.empire_score

        # Log mirroring event
        self._mirroring_bridge.log_event(
            event_type="turn_complete",
            turn=self._turn_count,
            state=self._state.to_dict(),
        )

        # Check game over condition (empire score >= 1000)
        if self._state.empire_score >= 1000:
            self._game_over = True
            self._mirroring_bridge.log_event(
                event_type="game_over",
                turn=self._turn_count,
                final_score=self._state.empire_score,
            )

        return self.get_state()

    def process_action(self, action_name: str, **kwargs) -> Dict[str, Any]:
        """Process a player action and return updated state."""
        result = self._player.perform_action(action_name, **kwargs)
        if result["success"]:
            # Update internal state from player
            self._state.resources = self._player.resources
            self._state.territory = self._player.empire.territory
            self._state.buildings = self._player.empire.buildings
            self._state.player_name = self._player.name

            self._mirroring_bridge.log_event(
                event_type="action",
                action=action_name,
                result=result,
                turn=self._turn_count,
            )
        return result

    def start_game(self, player_name: str = "Player") -> Dict[str, Any]:
        """Start a new game session."""
        self._state = GameState(player_name=player_name)
        self._player = Player(
            name=player_name,
            resources=Resources(gold=100, wood=50, stone=30, food=80, population=10),
            empire=Empire(
                territory=Territory(tiles_controlled=1, expansion_level=0),
                buildings=[],
            ),
        )
        self._mirroring_bridge = MirroringBridge(player_name=player_name)
        self._turn_count = 0
        self._game_over = False

        self._mirroring_bridge.log_event(
            event_type="game_start",
            player_name=player_name,
            initial_state=self._state.to_dict(),
        )
        return self.get_state()

    def run_demo_session(self, num_turns: int = 5) -> List[Dict[str, Any]]:
        """Run a demo game session with automated actions."""
        results = []

        # Initial action: gather resources
        self.process_action("gather_resources", amount=50)

        for turn in range(num_turns):
            # Process turn
            turn_state = self.process_turn()
            results.append({"turn": turn + 1, "state": turn_state})

            # Perform actions each turn
            if turn == 0:
                self.process_action("build_structure", building="farm", cost={"food": 20})
            elif turn == 1:
                self.process_action("expand_territory", tiles=5)
            elif turn == 2:
                self.process_action("recruit_units", count=5)
            elif turn == 3:
                self.process_action("gather_resources", amount=100)
                self.process_action("build_structure", building="mine", cost={"gold": 50})
            else:
                self.process_action("expand_territory", tiles=10)

        # Sync final state back to engine
        self._state.resources = self._player.resources
        self._state.territory = self._player.empire.territory
        self._state.buildings = self._player.empire.buildings
        self._state.empire_score = self._player.empire.empire_score

        return results
