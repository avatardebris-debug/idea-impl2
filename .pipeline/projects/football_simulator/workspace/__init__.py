"""American Football Simulator — a play-by-play simulation engine.

Usage:
    from football_simulator import FootballGame

    game = FootballGame(home_team="Chiefs", away_team="Eagles")
    game.simulate()
    print(game.stats.to_dict())
"""

from .field import Field
from .play import PlayCall, PlayType, RunDirection, PassRoute, Route, RunPath
from .players import Player, PlayerPosition
from .team import Team
from .game_state import GameState
from .simulation import FootballGame
from .stats import StatsTracker, PlayStats, DriveStats, GameStats
from .output import PlayByPlayWriter, GameSummary

__all__ = [
    "Field",
    "PlayCall",
    "PlayType",
    "RunDirection",
    "PassRoute",
    "Route",
    "RunPath",
    "Player",
    "PlayerPosition",
    "Team",
    "GameState",
    "FootballGame",
    "StatsTracker",
    "PlayStats",
    "DriveStats",
    "GameStats",
    "PlayByPlayWriter",
    "GameSummary",
]
