"""Play calling and execution engine.

Provides Play, PlayType, and PlayCall classes for defining and executing
football plays. Supports run plays, pass plays, and special teams plays.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field as dc_field
from typing import List, Optional, Tuple, Dict, Any

from .entities import Player, Formation
from .ball import Ball
from .football_field import Field


class PlayType(enum.Enum):
    """Types of football plays."""
    RUN = "run"
    PASS = "pass"
    PUNT = "punt"
    FIELD_GOAL = "field_goal"
    KICKOFF = "kickoff"
    TWO_POINT = "two_point"
    EXTRA_POINT = "extra_point"


class RunDirection(enum.Enum):
    """Direction for run plays."""
    LEFT_TACKLE = "left_tackle"
    LEFT_GUARD = "left_guard"
    UP_THE_MIDDLE = "up_the_middle"
    RIGHT_GUARD = "right_guard"
    RIGHT_TACKLE = "right_tackle"
    OFF_TACKLE_LEFT = "off_tackle_left"
    OFF_TACKLE_RIGHT = "off_tackle_right"
    CIRCLE = "circle"
    DRAW = "draw"


class PassRoute(enum.Enum):
    """Standard pass routes."""
    SLANT = "slant"
    POST = "post"
    CORNER = "corner"
    OUT = "out"
    IN = "in"
    FLAT = "flat"
    STREAK = "streak"
    DRAG = "drag"
    SWEEP = "sweep"
    CHECK_DOWN = "check_down"
    SCREEN = "screen"


@dataclass
class Route:
    """A pass route for a receiver.

    Attributes:
        player_id: ID of the player running the route.
        route_type: Type of route.
        depth_yards: How deep the route goes (for routes that go deep).
        break_angle: Angle at which the route breaks (degrees).
        break_yard: Yard line at which the route breaks.
        target_y: Target y-coordinate at the end of the route.
    """
    player_id: str
    route_type: PassRoute
    depth_yards: float = 15.0
    break_angle: float = 45.0
    break_yard: float = 10.0
    target_y: float = 26.665

    def get_target_position(self, start_x: float, start_y: float) -> Tuple[float, float]:
        """Calculate the target position for this route.

        Args:
            start_x: Starting x position.
            start_y: Starting y position.

        Returns:
            Target (x, y) position.
        """
        if self.route_type in (PassRoute.SLANT, PassRoute.POST, PassRoute.CORNER,
                               PassRoute.STREAK, PassRoute.DRAG):
            # Deep routes go forward
            end_x = start_x + self.depth_yards
            if self.route_type == PassRoute.SLANT:
                # Slant goes diagonally toward the middle
                direction = 1 if start_y > 26.665 else -1
                end_y = start_y + direction * self.depth_yards * math.sin(math.radians(self.break_angle))
            elif self.route_type == PassRoute.POST:
                # Post goes straight then breaks toward the middle
                end_y = 26.665
            elif self.route_type == PassRoute.CORNER:
                # Corner goes straight then breaks toward the sideline
                direction = 1 if start_y > 26.665 else -1
                end_y = start_y + direction * self.depth_yards * math.cos(math.radians(self.break_angle))
            else:
                # Streak and Drag go straight
                end_y = start_y
            return (end_x, end_y)
        elif self.route_type in (PassRoute.OUT, PassRoute.IN, PassRoute.FLAT):
            # Short routes break at break_yard
            if start_x + self.break_yard < start_x + self.depth_yards:
                break_x = start_x + self.break_yard
            else:
                break_x = start_x + self.depth_yards

            if self.route_type == PassRoute.OUT:
                direction = 1 if start_y > 26.665 else -1
                end_y = start_y + direction * 5.0
            elif self.route_type == PassRoute.IN:
                direction = -1 if start_y > 26.665 else 1
                end_y = start_y + direction * 5.0
            else:  # FLAT
                end_y = start_y + (1 if start_y > 26.665 else -1) * 3.0
            return (break_x, end_y)
        elif self.route_type == PassRoute.SWEEP:
            # Sweep goes around the end
            end_x = start_x + self.depth_yards
            direction = 1 if start_y > 26.665 else -1
            end_y = start_y + direction * 10.0
            return (end_x, end_y)
        elif self.route_type == PassRoute.SCREEN:
            # Screen goes forward then stops
            end_x = start_x + 5.0
            end_y = start_y
            return (end_x, end_y)
        elif self.route_type == PassRoute.CHECK_DOWN:
            # Check down goes straight back
            end_x = start_x + 3.0
            end_y = start_y
            return (end_x, end_y)
        else:
            return (start_x + self.depth_yards, start_y)


@dataclass
class RunPath:
    """A run path for the ball carrier.

    Attributes:
        direction: Direction of the run.
        depth_yards: How far the run goes before cutting.
        cut_angle: Angle at which the run cuts (degrees).
    """
    direction: RunDirection
    depth_yards: float = 10.0
    cut_angle: float = 45.0

    def get_target_position(self, start_x: float, start_y: float) -> Tuple[float, float]:
        """Calculate the target position for this run path.

        Args:
            start_x: Starting x position.
            start_y: Starting y position.

        Returns:
            Target (x, y) position.
        """
        if self.direction == RunDirection.UP_THE_MIDDLE:
            return (start_x + self.depth_yards, start_y)
        elif self.direction in (RunDirection.LEFT_TACKLE, RunDirection.LEFT_GUARD):
            direction = -1
            end_x = start_x + self.depth_yards * 0.8
            end_y = start_y + direction * self.depth_yards * math.sin(math.radians(self.cut_angle))
            return (end_x, end_y)
        elif self.direction in (RunDirection.RIGHT_TACKLE, RunDirection.RIGHT_GUARD):
            direction = 1
            end_x = start_x + self.depth_yards * 0.8
            end_y = start_y + direction * self.depth_yards * math.sin(math.radians(self.cut_angle))
            return (end_x, end_y)
        elif self.direction == RunDirection.OFF_TACKLE_LEFT:
            direction = -1
            end_x = start_x + self.depth_yards
            end_y = start_y + direction * self.depth_yards * math.cos(math.radians(self.cut_angle))
            return (end_x, end_y)
        elif self.direction == RunDirection.OFF_TACKLE_RIGHT:
            direction = 1
            end_x = start_x + self.depth_yards
            end_y = start_y + direction * self.depth_yards * math.cos(math.radians(self.cut_angle))
            return (end_x, end_y)
        elif self.direction == RunDirection.CIRCLE:
            # Circle around the end
            end_x = start_x + self.depth_yards * 1.2
            direction = 1 if start_y > 26.665 else -1
            end_y = start_y + direction * 15.0
            return (end_x, end_y)
        elif self.direction == RunDirection.DRAW:
            # Draw goes straight up the middle
            return (start_x + self.depth_yards, start_y)
        else:
            return (start_x + self.depth_yards, start_y)


@dataclass
class PlayCall:
    """A play call with all necessary information.

    Attributes:
        play_type: Type of play.
        run_path: Run path (for run plays).
        routes: Dictionary of player_id -> Route (for pass plays).
        qb_drop: QB drop depth (yards).
        protection: List of player IDs providing protection.
        snap_type: Type of snap (under_center, shotgun, wildcat).
        formation: Formation name.
    """
    play_type: PlayType
    run_path: Optional[RunPath] = None
    routes: Dict[str, Route] = dc_field(default_factory=dict)
    qb_drop: float = 5.0
    protection: List[str] = dc_field(default_factory=list)
    snap_type: str = "shotgun"
    formation: str = "i_formation"


@dataclass
class Play:
    """A football play.

    Attributes:
        play_id: Unique identifier for the play.
        play_call: The PlayCall for this play.
        formation: The Formation for this play.
        ball: The Ball object.
        field: The Field object.
        is_running: Whether the play is currently running.
        is_complete: Whether the play has been completed.
        play_result: The result of the play.
        play_stats: Statistics for the play.
        timeline: List of (time, event) tuples.
    """
    play_id: str = "play_1"
    play_call: Optional[PlayCall] = None
    formation: Optional[Formation] = None
    ball: Optional[Ball] = None
    field: Optional[Field] = None
    is_running: bool = False
    is_complete: bool = False
    play_result: Optional[Dict[str, Any]] = None
    play_stats: Dict[str, Any] = dc_field(default_factory=dict)
    timeline: List[Tuple[float, str]] = dc_field(default_factory=list)

    def __post_init__(self):
        if self.ball is None:
            self.ball = Ball()
        if self.field is None:
            self.field = Field()

    def start(self, play_call: PlayCall, formation: Formation) -> None:
        """Start the play.

        Args:
            play_call: The PlayCall for this play.
            formation: The Formation for this play.
        """
        self.play_call = play_call
        self.formation = formation
        self.is_running = True
        self.is_complete = False
        self.play_result = None
        self.play_stats = {}
        self.timeline = []
        self.ball.reset()

        # Set ball position based on snap type
        if formation is not None:
            qb = None
            for p in formation.offensive_players:
                if p.name == "QB":
                    qb = p
                    break
            if qb is not None:
                if play_call.snap_type == "under_center":
                    self.ball.position = (qb.x - 0.5, qb.y)
                else:
                    self.ball.position = (qb.x - play_call.qb_drop, qb.y)
                self.ball.velocity = (0.0, 0.0)
                self.ball.is_active = True
                self.timeline.append((0.0, "play_started"))

    def step(self, dt: float) -> None:
        """Step the play by one time step.

        Args:
            dt: Time step in seconds.
        """
        if not self.is_running or self.is_complete:
            return

        # Step all players
        if self.formation is not None:
            self.formation.step_all(dt)

        # Step the ball
        if self.ball is not None and self.ball.is_active:
            self.ball.step(dt)

        # Check for play completion
        self._check_play_completion(dt)

    def _check_play_completion(self, dt: float) -> None:
        """Check if the play should be completed.

        Args:
            dt: Time step in seconds.
        """
        if self.ball is None or self.formation is None:
            return

        # Check if ball carrier is out of bounds
        if self.ball.carrier_id is not None:
            carrier = None
            for p in self.formation.offensive_players + self.formation.defensive_players:
                if p.player_id == self.ball.carrier_id:
                    carrier = p
                    break

            if carrier is not None:
                # Check if out of bounds
                if carrier.y < 0 or carrier.y > self.field.width:
                    self._complete_play("out_of_bounds", carrier)
                    return

                # Check if ball carrier has reached the end zone
                if carrier.x >= self.field.end_zone_start:
                    self._complete_play("touchdown", carrier)
                    return

                # Check if ball carrier has been tackled
                for p in self.formation.defensive_players:
                    dx = carrier.x - p.x
                    dy = carrier.y - p.y
                    distance = math.sqrt(dx ** 2 + dy ** 2)
                    if distance <= carrier.radius + p.radius:
                        # Check if tackle is successful
                        if carrier.strength < p.strength * 1.2:
                            self._complete_play("tackle", carrier)
                            return

        # Check if ball is fumbled
        if self.ball.is_fumbled:
            self._complete_play("fumble", None)
            return

        # Check if ball is caught
        if self.ball.is_caught:
            # Check if any defender is close enough to make a play
            for p in self.formation.defensive_players:
                dx = self.ball.x - p.x
                dy = self.ball.y - p.y
                distance = math.sqrt(dx ** 2 + dy ** 2)
                if distance <= p.radius + self.ball.radius:
                    # Defender makes a play on the ball
                    if self.ball.catch(p.player_id, p.position, p.radius):
                        self.timeline.append((sum(t[0] for t in self.timeline) + dt, "ball_caught"))
                        return

        # Check if play time has expired
        elapsed_time = sum(t[0] for t in self.timeline) + dt
        if elapsed_time > 10.0:  # 10 second play clock
            self._complete_play("play_clock_violation", None)
            return

    def _complete_play(self, result_type: str, carrier: Optional[Player] = None) -> None:
        """Complete the play with a result.

        Args:
            result_type: Type of result.
            carrier: Ball carrier (if applicable).
        """
        self.is_running = False
        self.is_complete = True
        self.timeline.append((sum(t[0] for t in self.timeline), f"play_completed_{result_type}"))

        if result_type == "touchdown":
            self.play_result = {
                "result": "touchdown",
                "carrier_id": carrier.player_id if carrier else None,
                "yards_gained": 0,
                "time_elapsed": sum(t[0] for t in self.timeline),
            }
        elif result_type == "tackle":
            yards_gained = 0
            if self.formation is not None:
                yards_gained = self.formation.line_of_scrimmage_x - (carrier.x if carrier else 0)
            self.play_result = {
                "result": "tackle",
                "carrier_id": carrier.player_id if carrier else None,
                "yards_gained": yards_gained,
                "time_elapsed": sum(t[0] for t in self.timeline),
            }
        elif result_type == "out_of_bounds":
            yards_gained = 0
            if self.formation is not None:
                yards_gained = self.formation.line_of_scrimmage_x - (carrier.x if carrier else 0)
            self.play_result = {
                "result": "out_of_bounds",
                "carrier_id": carrier.player_id if carrier else None,
                "yards_gained": yards_gained,
                "time_elapsed": sum(t[0] for t in self.timeline),
            }
        elif result_type == "fumble":
            self.play_result = {
                "result": "fumble",
                "carrier_id": None,
                "yards_gained": 0,
                "time_elapsed": sum(t[0] for t in self.timeline),
            }
        else:
            self.play_result = {
                "result": result_type,
                "carrier_id": None,
                "yards_gained": 0,
                "time_elapsed": sum(t[0] for t in self.timeline),
            }

    def get_play_state(self) -> Dict[str, Any]:
        """Get the current state of the play.

        Returns:
            Dictionary with play state.
        """
        state = {
            "play_id": self.play_id,
            "is_running": self.is_running,
            "is_complete": self.is_complete,
            "play_result": self.play_result,
            "ball": self.ball.to_dict() if self.ball else None,
            "formation": self.formation.to_dict() if self.formation else None,
        }
        return state

    def reset(self) -> None:
        """Reset the play to its initial state."""
        self.is_running = False
        self.is_complete = False
        self.play_result = None
        self.play_stats = {}
        self.timeline = []
        if self.ball:
            self.ball.reset()

    def __repr__(self) -> str:
        status = "inactive"
        if self.is_running:
            status = "running"
        elif self.is_complete:
            if self.play_result:
                status = f"complete ({self.play_result['result']})"
            else:
                status = "complete"
        return f"Play(id={self.play_id}, status={status})"

