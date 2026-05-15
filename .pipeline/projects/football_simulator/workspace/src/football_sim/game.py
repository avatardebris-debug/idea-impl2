"""Game engine for the football simulator.

Provides the Game class that manages the overall game state, including
team scores, down and distance, game clock, and play execution.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any

from .config import Config
from .football_field import Field
from .entities import Player, Formation
from .formation import create_formation
from .ball import Ball
from .play import Play, PlayCall, PlayType, RunDirection, PassRoute, Route, RunPath
from .ai import OffensiveAI, DefensiveAI, AIState
from .stats import StatsTracker, PlayStats, DriveStats, GameStats


class GamePhase(enum.Enum):
    """Phases of a football game."""
    PRE_GAME = "pre_game"
    FIRST_HALF = "first_half"
    HALFTIME = "halftime"
    SECOND_HALF = "second_half"
    OVERTIME = "overtime"
    POST_GAME = "post_game"


class Down(enum.Enum):
    """Down numbers."""
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4


class GameResult(enum.Enum):
    """Possible game results."""
    HOME_WIN = "home_win"
    AWAY_WIN = "away_win"
    TIE = "tie"


@dataclass
class PlayResult:
    """Result of a single play.

    Attributes:
        play_type: Type of play executed.
        yards_gained: Yards gained on the play.
        is_first_down: Whether the play resulted in a first down.
        is_touchdown: Whether the play resulted in a touchdown.
        is_turnover: Whether the play resulted in a turnover.
        is_penalty: Whether a penalty occurred.
        penalty_type: Type of penalty (if any).
        penalty_yards: Yards of penalty (if any).
        carrier_id: ID of the ball carrier.
        passer_id: ID of the passer (if applicable).
        receiver_id: ID of the receiver (if applicable).
        time_remaining: Time remaining in the half.
    """
    play_type: PlayType
    yards_gained: float = 0.0
    is_first_down: bool = False
    is_touchdown: bool = False
    is_turnover: bool = False
    is_penalty: bool = False
    penalty_type: Optional[str] = None
    penalty_yards: float = 0.0
    carrier_id: Optional[str] = None
    passer_id: Optional[str] = None
    receiver_id: Optional[str] = None
    time_remaining: float = 0.0


@dataclass
class Team:
    """A football team.

    Attributes:
        team_id: Unique identifier for the team.
        name: Team name.
        score: Current score.
        formation: Current formation.
        offense: Offensive AI.
        defense: Defensive AI.
        stats: Game stats for the team.
        drive: Current drive stats.
        is_home: Whether this is the home team.
    """
    team_id: str
    name: str
    score: int = 0
    formation: Optional[Formation] = None
    offense: Optional[OffensiveAI] = None
    defense: Optional[DefensiveAI] = None
    stats: GameStats = field(default_factory=GameStats)
    drive: Optional[DriveStats] = None
    is_home: bool = False

    def __post_init__(self):
        if self.offense is None:
            self.offense = OffensiveAI()
        if self.defense is None:
            self.defense = DefensiveAI()
        if self.drive is None:
            self.drive = DriveStats()


@dataclass
class Game:
    """A football game.

    Attributes:
        game_id: Unique identifier for the game.
        home_team: Home team.
        away_team: Away team.
        field: The football field.
        ball: The football.
        current_down: Current down.
        yards_to_go: Yards needed for a first down.
        line_of_scrimmage: X position of the line of scrimmage.
        first_down_line: X position of the first down line.
        game_phase: Current phase of the game.
        game_clock: Time remaining in the game (seconds).
        half_clock: Time remaining in the current half (seconds).
        play_clock: Time remaining for the play clock (seconds).
        current_play: Current play being executed.
        play_history: History of all plays.
        stats_tracker: Stats tracker for the game.
        is_running: Whether the game is currently running.
        is_complete: Whether the game is complete.
        result: Final result of the game.
    """
    game_id: str = "game_1"
    home_team: Optional[Team] = None
    away_team: Optional[Team] = None
    football_field: Field = field(default_factory=Field)
    ball: Ball = field(default_factory=Ball)
    current_down: Down = Down.FIRST
    yards_to_go: float = 10.0
    line_of_scrimmage: float = 25.0
    first_down_line: float = 35.0
    game_phase: GamePhase = GamePhase.PRE_GAME
    game_clock: float = 3600.0  # 60 minutes in seconds
    half_clock: float = 1800.0  # 30 minutes in seconds
    play_clock: float = 40.0  # 40 second play clock
    current_play: Optional[Play] = None
    play_history: List[PlayResult] = field(default_factory=list)
    stats_tracker: StatsTracker = field(default_factory=StatsTracker)
    is_running: bool = False
    is_complete: bool = False
    result: Optional[GameResult] = None

    def __post_init__(self):
        if self.home_team is None:
            self.home_team = Team(
                team_id="home",
                name="Home Team",
                is_home=True,
            )
        if self.away_team is None:
            self.away_team = Team(
                team_id="away",
                name="Away Team",
                is_home=False,
            )

    def start_game(self) -> None:
        """Start the game."""
        self.game_phase = GamePhase.FIRST_HALF
        self.game_clock = 3600.0
        self.half_clock = 1800.0
        self.play_clock = 40.0
        self.current_down = Down.FIRST
        self.yards_to_go = 10.0
        self.line_of_scrimmage = 25.0
        self.first_down_line = 35.0
        self.is_running = True
        self.is_complete = False
        self.result = None

        # Set up initial formations
        self._setup_initial_formations()

        # Start the first drive
        self.away_team.drive = DriveStats()
        self.away_team.drive.start_drive(self.away_team.team_id)

        # Kick off to home team
        self._execute_kickoff()

    def _setup_initial_formations(self) -> None:
        """Set up the initial formations for both teams."""
        # Away team (offense) formation
        away_formation = create_formation(
            formation_name="shotgun",
            line_of_scrimmage_x=self.line_of_scrimmage,
            is_offense=True,
        )
        self.away_team.formation = away_formation

        # Home team (defense) formation
        home_formation = create_formation(
            formation_name="4_3",
            line_of_scrimmage_x=self.line_of_scrimmage,
            is_offense=False,
        )
        self.home_team.formation = home_formation

    def _execute_kickoff(self) -> None:
        """Execute the kickoff to start the game."""
        # Create a kickoff play
        kickoff_play = Play(
            play_id="kickoff_1",
            play_call=PlayCall(
                play_type=PlayType.KICKOFF,
                snap_type="kickoff",
            ),
            formation=self.away_team.formation,
            ball=self.ball,
            field=self.football_field,
        )
        kickoff_play.start(
            play_call=PlayCall(
                play_type=PlayType.KICKOFF,
                snap_type="kickoff",
            ),
            formation=self.away_team.formation,
        )

        # Step the kickoff play
        for _ in range(60):  # 1 second at 60fps
            kickoff_play.step(1.0 / 60.0)

        # Check if the kickoff was returned
        if kickoff_play.is_complete and kickoff_play.play_result:
            result = kickoff_play.play_result
            if result["result"] == "touchdown":
                # Touchback - ball at 25 yard line
                self.line_of_scrimmage = 25.0
                self.first_down_line = self.line_of_scrimmage + 10.0
                self.current_down = Down.FIRST
                self.yards_to_go = 10.0
                self.home_team.drive = DriveStats()
                self.home_team.drive.start_drive(self.home_team.team_id)
            else:
                # Ball returned to some position
                self.line_of_scrimmage = result.get("yards_gained", 25.0)
                self.first_down_line = self.line_of_scrimmage + 10.0
                self.current_down = Down.FIRST
                self.yards_to_go = 10.0
                self.home_team.drive = DriveStats()
                self.home_team.drive.start_drive(self.home_team.team_id)

    def start_drive(self, team: Team) -> None:
        """Start a new drive for a team.

        Args:
            team: The team starting the drive.
        """
        team.drive = DriveStats()
        team.drive.start_drive(team.team_id)
        self.current_down = Down.FIRST
        self.yards_to_go = 10.0
        self.line_of_scrimmage = 25.0
        self.first_down_line = self.line_of_scrimmage + 10.0

    def execute_play(self) -> PlayResult:
        """Execute the current play.

        Returns:
            The result of the play.
        """
        if not self.is_running or self.is_complete:
            raise RuntimeError("Game is not running")

        # Get play call from AI
        offensive_team = self.away_team if self.away_team.drive and self.away_team.drive.is_offense else self.home_team
        defensive_team = self.home_team if offensive_team == self.away_team else self.away_team

        # Get play call from offensive AI
        play_call = offensive_team.offense.get_play_call(
            down=self.current_down,
            yards_to_go=self.yards_to_go,
            line_of_scrimmage=self.line_of_scrimmage,
            field=self.football_field,
        )

        # Set up the play
        if self.current_play is None:
            self.current_play = Play(
                play_id=f"play_{len(self.play_history) + 1}",
                ball=self.ball,
                field=self.football_field,
            )

        # Create formation for the play
        formation = create_formation(
            formation_name=play_call.formation,
            line_of_scrimmage_x=self.line_of_scrimmage,
            is_offense=True,
        )

        # Set up defensive formation
        defensive_formation = create_formation(
            formation_name="4_3",  # Default defensive formation
            line_of_scrimmage_x=self.line_of_scrimmage,
            is_offense=False,
        )

        # Start the play
        self.current_play.start(play_call, formation)

        # Execute the play
        for _ in range(60):  # 1 second at 60fps
            self.current_play.step(1.0 / 60.0)

        # Get the play result
        play_result = self._get_play_result(play_call)

        # Update game state
        self._update_game_state(play_result)

        # Record the play
        self.play_history.append(play_result)

        # Update stats
        self.stats_tracker.record_play(play_result, offensive_team, defensive_team)

        # Reset for next play
        self.play_clock = 40.0
        self.current_play = None

        return play_result

    def _get_play_result(self, play_call: PlayCall) -> PlayResult:
        """Get the result of the play.

        Args:
            play_call: The play call that was executed.

        Returns:
            The result of the play.
        """
        if self.current_play is None or self.current_play.play_result is None:
            return PlayResult(play_type=play_call.play_type)

        result = self.current_play.play_result
        yards_gained = result.get("yards_gained", 0.0)

        # Determine if it's a first down
        is_first_down = self.line_of_scrimmage + yards_gained >= self.first_down_line

        # Determine if it's a touchdown
        is_touchdown = self.line_of_scrimmage + yards_gained >= self.football_field.end_zone_start

        # Determine if it's a turnover
        is_turnover = result.get("result") in ("fumble", "interception")

        # Determine if there was a penalty
        is_penalty = False
        penalty_type = None
        penalty_yards = 0.0

        # Check for penalties based on play type
        if play_call.play_type == PlayType.PASS:
            # Check for pass interference
            if self.current_play.formation is not None:
                for p in self.current_play.formation.defensive_players:
                    if p.is_penalty:
                        is_penalty = True
                        penalty_type = "pass_interference"
                        penalty_yards = 15.0
                        break

        return PlayResult(
            play_type=play_call.play_type,
            yards_gained=yards_gained,
            is_first_down=is_first_down,
            is_touchdown=is_touchdown,
            is_turnover=is_turnover,
            is_penalty=is_penalty,
            penalty_type=penalty_type,
            penalty_yards=penalty_yards,
            carrier_id=result.get("carrier_id"),
            passer_id=result.get("passer_id"),
            receiver_id=result.get("receiver_id"),
            time_remaining=self.half_clock,
        )

    def _update_game_state(self, play_result: PlayResult) -> None:
        """Update the game state based on the play result.

        Args:
            play_result: The result of the play.
        """
        # Update game clock
        self.game_clock -= 1.0 / 60.0 * 60.0  # 1 second per play
        self.half_clock -= 1.0 / 60.0 * 60.0

        # Update half clock
        if self.half_clock <= 0:
            if self.game_phase == GamePhase.FIRST_HALF:
                self.game_phase = GamePhase.HALFTIME
                self.is_running = False
                return
            elif self.game_phase == GamePhase.SECOND_HALF:
                self.game_phase = GamePhase.POST_GAME
                self.is_complete = True
                self._determine_game_result()
                return

        # Update score if touchdown
        if play_result.is_touchdown:
            offensive_team = self.away_team if self.away_team.drive and self.away_team.drive.is_offense else self.home_team
            offensive_team.score += 6  # Touchdown is 6 points

        # Update down and distance
        if play_result.is_first_down:
            self.current_down = Down.FIRST
            self.yards_to_go = 10.0
            self.line_of_scrimmage = self.first_down_line
            self.first_down_line = self.line_of_scrimmage + 10.0
        else:
            self.current_down = Down(self.current_down.value + 1)
            self.yards_to_go -= play_result.yards_gained
            self.line_of_scrimmage += play_result.yards_gained
            self.first_down_line += play_result.yards_gained

        # Check for fourth down turnover
        if self.current_down == Down.FOURTH and not play_result.is_first_down:
            # Turnover on downs
            offensive_team = self.away_team if self.away_team.drive and self.away_team.drive.is_offense else self.home_team
            defensive_team = self.home_team if offensive_team == self.away_team else self.away_team

            # Switch possession
            if offensive_team == self.away_team:
                self.away_team.drive = None
                self.home_team.drive = DriveStats()
                self.home_team.drive.start_drive(self.home_team.team_id)
            else:
                self.home_team.drive = None
                self.away_team.drive = DriveStats()
                self.away_team.drive.start_drive(self.away_team.team_id)

            self.current_down = Down.FIRST
            self.yards_to_go = 10.0
            self.line_of_scrimmage = 35.0 - self.line_of_scrimmage + 25.0  # Flip field
            self.first_down_line = self.line_of_scrimmage + 10.0

        # Check for penalty
        if play_result.is_penalty:
            if play_result.penalty_type == "pass_interference":
                # 15 yard penalty
                self.line_of_scrimmage += play_result.penalty_yards
                self.first_down_line += play_result.penalty_yards

    def _determine_game_result(self) -> None:
        """Determine the result of the game."""
        if self.home_team.score > self.away_team.score:
            self.result = GameResult.HOME_WIN
        elif self.away_team.score > self.home_team.score:
            self.result = GameResult.AWAY_WIN
        else:
            self.result = GameResult.TIE

    def step(self, dt: float = 1.0 / 60.0) -> None:
        """Step the game by one time step.

        Args:
            dt: Time step in seconds.
        """
        if not self.is_running or self.is_complete:
            return

        # Step the current play if running
        if self.current_play is not None and self.current_play.is_running:
            self.current_play.step(dt)

        # Update game clock
        self.game_clock -= dt
        self.half_clock -= dt

        # Check for half end
        if self.half_clock <= 0:
            if self.game_phase == GamePhase.FIRST_HALF:
                self.game_phase = GamePhase.HALFTIME
                self.is_running = False
            elif self.game_phase == GamePhase.SECOND_HALF:
                self.game_phase = GamePhase.POST_GAME
                self.is_complete = True
                self._determine_game_result()

        # Check for game end
        if self.game_clock <= 0:
            self.game_phase = GamePhase.POST_GAME
            self.is_complete = True
            self._determine_game_result()

    def get_game_state(self) -> Dict[str, Any]:
        """Get the current state of the game.

        Returns:
            Dictionary with game state.
        """
        state = {
            "game_id": self.game_id,
            "game_phase": self.game_phase.value,
            "game_clock": self.game_clock,
            "half_clock": self.half_clock,
            "play_clock": self.play_clock,
            "current_down": self.current_down.value,
            "yards_to_go": self.yards_to_go,
            "line_of_scrimmage": self.line_of_scrimmage,
            "first_down_line": self.first_down_line,
            "home_score": self.home_team.score,
            "away_score": self.away_team.score,
            "is_running": self.is_running,
            "is_complete": self.is_complete,
            "result": self.result.value if self.result else None,
            "home_team": {
                "name": self.home_team.name,
                "score": self.home_team.score,
                "drive": self.home_team.drive.to_dict() if self.home_team.drive else None,
            },
            "away_team": {
                "name": self.away_team.name,
                "score": self.away_team.score,
                "drive": self.away_team.drive.to_dict() if self.away_team.drive else None,
            },
            "current_play": self.current_play.get_play_state() if self.current_play else None,
            "play_history": [
                {
                    "play_type": pr.play_type.value,
                    "yards_gained": pr.yards_gained,
                    "is_first_down": pr.is_first_down,
                    "is_touchdown": pr.is_touchdown,
                    "is_turnover": pr.is_turnover,
                    "time_remaining": pr.time_remaining,
                }
                for pr in self.play_history
            ],
        }
        return state

    def reset(self) -> None:
        """Reset the game to its initial state."""
        self.game_phase = GamePhase.PRE_GAME
        self.game_clock = 3600.0
        self.half_clock = 1800.0
        self.play_clock = 40.0
        self.current_down = Down.FIRST
        self.yards_to_go = 10.0
        self.line_of_scrimmage = 25.0
        self.first_down_line = 35.0
        self.is_running = False
        self.is_complete = False
        self.result = None
        self.current_play = None
        self.play_history = []
        self.home_team.score = 0
        self.away_team.score = 0
        self.home_team.drive = None
        self.away_team.drive = None
        self.home_team.formation = None
        self.away_team.formation = None
        self.ball.reset()

    def __repr__(self) -> str:
        status = "inactive"
        if self.is_running:
            status = "running"
        elif self.is_complete:
            if self.result:
                status = f"complete ({self.result.value})"
            else:
                status = "complete"
        return (
            f"Game(id={self.game_id}, phase={self.game_phase.value}, "
            f"score={self.away_team.score}-{self.home_team.score}, "
            f"status={status})"
        )

