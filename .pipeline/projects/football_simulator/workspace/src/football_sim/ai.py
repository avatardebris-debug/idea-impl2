"""AI decision making for offensive and defensive players.

Provides OffensiveAI and DefensiveAI classes that make decisions about
play calling, route running, and defensive positioning.
"""

from __future__ import annotations

import enum
import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from .config import Config
from .field import Field
from .play import PlayCall, PlayType, RunDirection, PassRoute, Route, RunPath


class AIState(enum.Enum):
    """States for AI decision making."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    ADAPTING = "adapting"
    RESETTING = "resetting"


@dataclass
class Decision:
    """A decision made by the AI.

    Attributes:
        decision_type: Type of decision.
        confidence: Confidence in the decision (0-1).
        reasoning: Reasoning for the decision.
        parameters: Additional parameters for the decision.
    """
    decision_type: str
    confidence: float = 0.5
    reasoning: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OffensiveAI:
    """AI for offensive decision making.

    Attributes:
        aggression: Aggression level (0-1).
        pass_heavy: Whether to favor passing (0-1).
        run_heavy: Whether to favor running (0-1).
        risk_tolerance: Risk tolerance (0-1).
        play_call_history: History of play calls.
        state: Current AI state.
    """
    aggression: float = 0.5
    pass_heavy: float = 0.5
    run_heavy: float = 0.5
    risk_tolerance: float = 0.5
    play_call_history: List[PlayType] = field(default_factory=list)
    state: AIState = AIState.IDLE

    def get_play_call(
        self,
        down: int,
        yards_to_go: float,
        line_of_scrimmage: float,
        field: Field,
    ) -> PlayCall:
        """Get a play call based on game state.

        Args:
            down: Current down.
            yards_to_go: Yards needed for a first down.
            line_of_scrimmage: X position of the line of scrimmage.
            field: The football field.

        Returns:
            The PlayCall for this situation.
        """
        self.state = AIState.PLANNING

        # Determine play type based on down and distance
        play_type = self._determine_play_type(down, yards_to_go, line_of_scrimmage, field)

        # Determine formation
        formation = self._determine_formation(down, yards_to_go)

        # Create the play call
        if play_type == PlayType.RUN:
            run_path = self._determine_run_path(down, yards_to_go)
            play_call = PlayCall(
                play_type=play_type,
                run_path=run_path,
                formation=formation,
                snap_type="shotgun",
            )
        elif play_type == PlayType.PASS:
            routes = self._determine_pass_routes(down, yards_to_go)
            play_call = PlayCall(
                play_type=play_type,
                routes=routes,
                formation=formation,
                snap_type="shotgun",
            )
        else:
            play_call = PlayCall(
                play_type=play_type,
                formation=formation,
                snap_type="shotgun",
            )

        self.play_call_history.append(play_type)
        self.state = AIState.EXECUTING

        return play_call

    def _determine_play_type(
        self,
        down: int,
        yards_to_go: float,
        line_of_scrimmage: float,
        field: Field,
    ) -> PlayType:
        """Determine the play type based on game state.

        Args:
            down: Current down.
            yards_to_go: Yards needed for a first down.
            line_of_scrimmage: X position of the line of scrimmage.
            field: The football field.

        Returns:
            The PlayType for this situation.
        """
        # In the red zone, favor passing
        if line_of_scrimmage >= field.end_zone_start - 10:
            return PlayType.PASS

        # On third down, favor passing
        if down == 3:
            if yards_to_go <= 3:
                return PlayType.RUN
            else:
                return PlayType.PASS

        # On fourth down, go for it if close to first down
        if down == 4:
            if yards_to_go <= 3:
                return PlayType.PASS
            else:
                return PlayType.RUN

        # Default to run if run_heavy, otherwise pass
        if self.run_heavy > self.pass_heavy:
            return PlayType.RUN
        else:
            return PlayType.PASS

    def _determine_formation(self, down: int, yards_to_go: float) -> str:
        """Determine the formation based on game state.

        Args:
            down: Current down.
            yards_to_go: Yards needed for a first down.

        Returns:
            The formation name.
        """
        # On third down, use a passing formation
        if down == 3:
            return "11_personnel"

        # On fourth down, use a running formation
        if down == 4:
            return "12_personnel"

        # Default to a balanced formation
        return "11_personnel"

    def _determine_run_path(self, down: int, yards_to_go: float) -> RunPath:
        """Determine the run path based on game state.

        Args:
            down: Current down.
            yards_to_go: Yards needed for a first down.

        Returns:
            The RunPath for this play.
        """
        # Determine direction
        directions = [
            RunDirection.LEFT_TACKLE,
            RunDirection.LEFT_GUARD,
            RunDirection.UP_THE_MIDDLE,
            RunDirection.RIGHT_GUARD,
            RunDirection.RIGHT_TACKLE,
            RunDirection.OFF_TACKLE_LEFT,
            RunDirection.OFF_TACKLE_RIGHT,
        ]
        direction = random.choice(directions)

        # Aim for a bit more than needed
        depth = yards_to_go + 5.0

        return RunPath(
            direction=direction,
            depth_yards=depth,
        )

    def _determine_pass_routes(self, down: int, yards_to_go: float) -> Dict[str, Route]:
        """Determine the pass routes based on game state.

        Args:
            down: Current down.
            yards_to_go: Yards needed for a first down.

        Returns:
            Dictionary of player_id -> Route for this play.
        """
        routes: Dict[str, Route] = {}

        # Determine number of receivers
        num_receivers = random.randint(2, 4)

        # Generate routes for each receiver
        route_types = list(PassRoute)
        for i in range(num_receivers):
            route_type = random.choice(route_types)
            depth = random.uniform(5.0, 20.0)
            break_angle = random.uniform(30.0, 60.0)
            break_yard = random.uniform(5.0, 15.0)

            routes[f"receiver_{i}"] = Route(
                player_id=f"receiver_{i}",
                route_type=route_type,
                depth_yards=depth,
                break_angle=break_angle,
                break_yard=break_yard,
            )

        return routes


@dataclass
class DefensiveAI:
    """AI for defensive decision making.

    Attributes:
        aggression: Aggression level (0-1).
        blitz_heavy: Whether to favor blitzing (0-1).
        zone_heavy: Whether to favor zone coverage (0-1).
        man_heavy: Whether to favor man coverage (0-1).
        state: Current AI state.
    """
    aggression: float = 0.5
    blitz_heavy: float = 0.5
    zone_heavy: float = 0.5
    man_heavy: float = 0.5
    state: AIState = AIState.IDLE

    def get_defensive_alignment(
        self,
        offensive_formation: str,
        down: int,
        yards_to_go: float,
        line_of_scrimmage: float,
        field: Field,
    ) -> Dict[str, Any]:
        """Get defensive alignment based on game state.

        Args:
            offensive_formation: The offensive formation.
            down: Current down.
            yards_to_go: Yards needed for a first down.
            line_of_scrimmage: X position of the line of scrimmage.
            field: The football field.

        Returns:
            Dictionary with defensive alignment parameters.
        """
        self.state = AIState.PLANNING

        # Determine coverage type
        coverage = self._determine_coverage(down, yards_to_go)

        # Determine blitz strategy
        blitz = self._determine_blitz(down, yards_to_go)

        # Determine gap assignments
        gaps = self._determine_gaps(offensive_formation)

        self.state = AIState.EXECUTING

        return {
            "coverage": coverage,
            "blitz": blitz,
            "gaps": gaps,
        }

    def _determine_coverage(self, down: int, yards_to_go: float) -> str:
        """Determine the coverage type based on game state.

        Args:
            down: Current down.
            yards_to_go: Yards needed for a first down.

        Returns:
            The coverage type.
        """
        # On third down, favor zone coverage
        if down == 3:
            if self.zone_heavy > self.man_heavy:
                return "zone"
            else:
                return "man"

        # On fourth down, favor man coverage
        if down == 4:
            return "man"

        # Default to zone coverage
        if self.zone_heavy > self.man_heavy:
            return "zone"
        else:
            return "man"

    def _determine_blitz(self, down: int, yards_to_go: float) -> bool:
        """Determine whether to blitz based on game state.

        Args:
            down: Current down.
            yards_to_go: Yards needed for a first down.

        Returns:
            Whether to blitz.
        """
        # On third down, favor blitzing
        if down == 3:
            if self.blitz_heavy > 0.5:
                return True
            else:
                return False

        # On fourth down, favor blitzing
        if down == 4:
            if self.blitz_heavy > 0.5:
                return True
            else:
                return False

        # Default to no blitz
        return False

    def _determine_gaps(self, offensive_formation: str) -> Dict[str, str]:
        """Determine gap assignments based on offensive formation.

        Args:
            offensive_formation: The offensive formation.

        Returns:
            Dictionary with gap assignments.
        """
        # Default gap assignments
        gaps = {
            "A_gap": "defensive_tackle",
            "B_gap": "linebacker",
            "C_gap": "cornerback",
        }

        # Adjust based on formation
        if "12_personnel" in offensive_formation:
            gaps["A_gap"] = "defensive_end"

        return gaps

    def make_play_call(self, offensive_play: PlayCall) -> Decision:
        """Make a defensive play call based on the offensive play.

        Args:
            offensive_play: The offensive play call.

        Returns:
            The defensive decision.
        """
        self.state = AIState.ADAPTING

        # Determine defensive response
        if offensive_play.play_type == PlayType.RUN:
            decision_type = "run_stops"
        elif offensive_play.play_type == PlayType.PASS:
            decision_type = "pass_rush"
        else:
            decision_type = "kick_return"

        # Determine confidence
        confidence = random.uniform(0.5, 1.0)

        # Determine reasoning
        reasoning = f"Responding to {offensive_play.play_type.value} play"

        # Determine parameters
        parameters = {
            "aggression": self.aggression,
            "blitz": self._determine_blitz(3, 5),  # Default to third down
        }

        self.state = AIState.EXECUTING

        return Decision(
            decision_type=decision_type,
            confidence=confidence,
            reasoning=reasoning,
            parameters=parameters,
        )
