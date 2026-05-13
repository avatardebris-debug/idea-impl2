"""Stats tracking for the football simulator.

Provides StatsTracker, PlayStats, DriveStats, and GameStats classes for
tracking comprehensive football statistics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from collections import defaultdict

from .play import PlayType


@dataclass
class PlayStats:
    """Statistics for a single play.

    Attributes:
        play_id: ID of the play.
        play_type: Type of play.
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
        pass_distance: Distance of the pass (if applicable).
        pass_completion: Whether the pass was completed.
        time_elapsed: Time elapsed during the play.
    """
    play_id: str = ""
    play_type: PlayType = PlayType.RUN
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
    pass_distance: float = 0.0
    pass_completion: bool = False
    time_elapsed: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary with play stats.
        """
        return {
            "play_id": self.play_id,
            "play_type": self.play_type.value,
            "yards_gained": self.yards_gained,
            "is_first_down": self.is_first_down,
            "is_touchdown": self.is_touchdown,
            "is_turnover": self.is_turnover,
            "is_penalty": self.is_penalty,
            "penalty_type": self.penalty_type,
            "penalty_yards": self.penalty_yards,
            "carrier_id": self.carrier_id,
            "passer_id": self.passer_id,
            "receiver_id": self.receiver_id,
            "pass_distance": self.pass_distance,
            "pass_completion": self.pass_completion,
            "time_elapsed": self.time_elapsed,
        }


@dataclass
class DriveStats:
    """Statistics for a single drive.

    Attributes:
        drive_id: ID of the drive.
        team_id: ID of the team on drive.
        is_offense: Whether this team is on offense.
        start_field_position: Field position at the start of the drive.
        end_field_position: Field position at the end of the drive.
        plays: List of play stats for the drive.
        total_yards: Total yards gained on the drive.
        rushing_yards: Total rushing yards on the drive.
        passing_yards: Total passing yards on the drive.
        first_downs: Number of first downs on the drive.
        third_down_conversions: Number of third down conversions.
        third_down_attempts: Number of third down attempts.
        fourth_down_conversions: Number of fourth down conversions.
        fourth_down_attempts: Number of fourth down attempts.
        turnovers: Number of turnovers on the drive.
        penalties: Number of penalties on the drive.
        penalty_yards: Total penalty yards on the drive.
        time_of_possession: Time of possession on the drive.
        is_touchdown_drive: Whether the drive ended in a touchdown.
        is_field_goal_drive: Whether the drive ended in a field goal.
        is_turnover_drive: Whether the drive ended in a turnover.
    """
    drive_id: str = "drive_1"
    team_id: str = ""
    is_offense: bool = True
    start_field_position: float = 25.0
    end_field_position: float = 25.0
    plays: List[PlayStats] = field(default_factory=list)
    total_yards: float = 0.0
    rushing_yards: float = 0.0
    passing_yards: float = 0.0
    first_downs: int = 0
    third_down_conversions: int = 0
    third_down_attempts: int = 0
    fourth_down_conversions: int = 0
    fourth_down_attempts: int = 0
    turnovers: int = 0
    penalties: int = 0
    penalty_yards: float = 0.0
    time_of_possession: float = 0.0
    is_touchdown_drive: bool = False
    is_field_goal_drive: bool = False
    is_turnover_drive: bool = False

    def start_drive(self, team_id: str) -> None:
        """Start a new drive.

        Args:
            team_id: ID of the team starting the drive.
        """
        self.team_id = team_id
        self.is_offense = True
        self.start_field_position = 25.0
        self.end_field_position = 25.0
        self.plays = []
        self.total_yards = 0.0
        self.rushing_yards = 0.0
        self.passing_yards = 0.0
        self.first_downs = 0
        self.third_down_conversions = 0
        self.third_down_attempts = 0
        self.fourth_down_conversions = 0
        self.fourth_down_attempts = 0
        self.turnovers = 0
        self.penalties = 0
        self.penalty_yards = 0.0
        self.time_of_possession = 0.0
        self.is_touchdown_drive = False
        self.is_field_goal_drive = False
        self.is_turnover_drive = False

    def add_play(self, play_stats: PlayStats) -> None:
        """Add a play to the drive.

        Args:
            play_stats: The play stats to add.
        """
        self.plays.append(play_stats)
        self.total_yards += play_stats.yards_gained
        self.time_of_possession += play_stats.time_elapsed

        if play_stats.play_type == PlayType.RUN:
            self.rushing_yards += play_stats.yards_gained
        elif play_stats.play_type == PlayType.PASS:
            self.passing_yards += play_stats.yards_gained

        if play_stats.is_first_down:
            self.first_downs += 1

        if play_stats.is_touchdown:
            self.is_touchdown_drive = True

        if play_stats.is_turnover:
            self.turnovers += 1
            self.is_turnover_drive = True

        if play_stats.is_penalty:
            self.penalties += 1
            self.penalty_yards += play_stats.penalty_yards

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary with drive stats.
        """
        return {
            "drive_id": self.drive_id,
            "team_id": self.team_id,
            "is_offense": self.is_offense,
            "start_field_position": self.start_field_position,
            "end_field_position": self.end_field_position,
            "total_yards": self.total_yards,
            "rushing_yards": self.rushing_yards,
            "passing_yards": self.passing_yards,
            "first_downs": self.first_downs,
            "third_down_conversions": self.third_down_conversions,
            "third_down_attempts": self.third_down_attempts,
            "fourth_down_conversions": self.fourth_down_conversions,
            "fourth_down_attempts": self.fourth_down_attempts,
            "turnovers": self.turnovers,
            "penalties": self.penalties,
            "penalty_yards": self.penalty_yards,
            "time_of_possession": self.time_of_possession,
            "is_touchdown_drive": self.is_touchdown_drive,
            "is_field_goal_drive": self.is_field_goal_drive,
            "is_turnover_drive": self.is_turnover_drive,
        }


@dataclass
class GameStats:
    """Statistics for a complete game.

    Attributes:
        game_id: ID of the game.
        home_team_stats: Stats for the home team.
        away_team_stats: Stats for the away team.
        total_plays: Total number of plays in the game.
        total_yards: Total yards in the game.
        total_touchdowns: Total touchdowns in the game.
        total_turnovers: Total turnovers in the game.
        total_penalties: Total penalties in the game.
        total_penalty_yards: Total penalty yards in the game.
        home_drives: List of drive stats for the home team.
        away_drives: List of drive stats for the away team.
        play_by_play: List of play stats for the game.
    """
    game_id: str = "game_1"
    home_team_stats: Dict[str, Any] = field(default_factory=dict)
    away_team_stats: Dict[str, Any] = field(default_factory=dict)
    total_plays: int = 0
    total_yards: float = 0.0
    total_touchdowns: int = 0
    total_turnovers: int = 0
    total_penalties: int = 0
    total_penalty_yards: float = 0.0
    home_drives: List[DriveStats] = field(default_factory=list)
    away_drives: List[DriveStats] = field(default_factory=list)
    play_by_play: List[PlayStats] = field(default_factory=list)

    def add_play(self, play_stats: PlayStats, team_id: str) -> None:
        """Add a play to the game stats.

        Args:
            play_stats: The play stats to add.
            team_id: ID of the team that made the play.
        """
        self.total_plays += 1
        self.total_yards += play_stats.yards_gained
        self.total_touchdowns += 1 if play_stats.is_touchdown else 0
        self.total_turnovers += 1 if play_stats.is_turnover else 0
        self.total_penalties += 1 if play_stats.is_penalty else 0
        self.total_penalty_yards += play_stats.penalty_yards

        self.play_by_play.append(play_stats)

        if team_id == "home":
            self.home_team_stats.setdefault("plays", []).append(play_stats)
            self.home_team_stats.setdefault("yards", []).append(play_stats.yards_gained)
            self.home_team_stats.setdefault("touchdowns", []).append(1 if play_stats.is_touchdown else 0)
            self.home_team_stats.setdefault("turnovers", []).append(1 if play_stats.is_turnover else 0)
            self.home_team_stats.setdefault("penalties", []).append(1 if play_stats.is_penalty else 0)
            self.home_team_stats.setdefault("penalty_yards", []).append(play_stats.penalty_yards)
        else:
            self.away_team_stats.setdefault("plays", []).append(play_stats)
            self.away_team_stats.setdefault("yards", []).append(play_stats.yards_gained)
            self.away_team_stats.setdefault("touchdowns", []).append(1 if play_stats.is_touchdown else 0)
            self.away_team_stats.setdefault("turnovers", []).append(1 if play_stats.is_turnover else 0)
            self.away_team_stats.setdefault("penalties", []).append(1 if play_stats.is_penalty else 0)
            self.away_team_stats.setdefault("penalty_yards", []).append(play_stats.penalty_yards)

    def add_drive(self, drive_stats: DriveStats, team_id: str) -> None:
        """Add a drive to the game stats.

        Args:
            drive_stats: The drive stats to add.
            team_id: ID of the team that had the drive.
        """
        if team_id == "home":
            self.home_drives.append(drive_stats)
        else:
            self.away_drives.append(drive_stats)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary with game stats.
        """
        return {
            "game_id": self.game_id,
            "home_team_stats": self.home_team_stats,
            "away_team_stats": self.away_team_stats,
            "total_plays": self.total_plays,
            "total_yards": self.total_yards,
            "total_touchdowns": self.total_touchdowns,
            "total_turnovers": self.total_turnovers,
            "total_penalties": self.total_penalties,
            "total_penalty_yards": self.total_penalty_yards,
            "home_drives": [d.to_dict() for d in self.home_drives],
            "away_drives": [d.to_dict() for d in self.away_drives],
            "play_by_play": [p.to_dict() for p in self.play_by_play],
        }


class StatsTracker:
    """Tracker for game statistics.

    Attributes:
        game_stats: Game statistics.
        current_drive: Current drive stats.
        current_play: Current play stats.
    """
    def __init__(self) -> None:
        """Initialize the stats tracker."""
        self.game_stats = GameStats()
        self.current_drive = DriveStats()
        self.current_play = PlayStats()

    def record_play(
        self,
        play_result: "PlayResult",
        offensive_team: Any,
        defensive_team: Any,
    ) -> None:
        """Record a play in the stats tracker.

        Args:
            play_result: The result of the play.
            offensive_team: The offensive team.
            defensive_team: The defensive team.
        """
        # Create play stats
        self.current_play = PlayStats(
            play_id="",
            play_type=play_result.play_type,
            yards_gained=play_result.yards_gained,
            is_first_down=play_result.is_first_down,
            is_touchdown=play_result.is_touchdown,
            is_turnover=play_result.is_turnover,
            is_penalty=play_result.is_penalty,
            penalty_type=play_result.penalty_type,
            penalty_yards=play_result.penalty_yards,
            carrier_id=play_result.carrier_id,
            passer_id=play_result.passer_id,
            receiver_id=play_result.receiver_id,
            pass_distance=0.0,
            pass_completion=False,
            time_elapsed=0.0,
        )

        # Add play to current drive
        self.current_drive.add_play(self.current_play)

        # Add play to game stats
        self.game_stats.add_play(self.current_play, offensive_team.team_id)

    def start_drive(self, team_id: str) -> None:
        """Start a new drive.

        Args:
            team_id: ID of the team starting the drive.
        """
        self.current_drive = DriveStats()
        self.current_drive.start_drive(team_id)

    def end_drive(self, team_id: str) -> None:
        """End the current drive.

        Args:
            team_id: ID of the team that had the drive.
        """
        self.game_stats.add_drive(self.current_drive, team_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get the current stats.

        Returns:
            Dictionary with current stats.
        """
        return self.game_stats.to_dict()

    def reset(self) -> None:
        """Reset the stats tracker."""
        self.game_stats = GameStats()
        self.current_drive = DriveStats()
        self.current_play = PlayStats()
