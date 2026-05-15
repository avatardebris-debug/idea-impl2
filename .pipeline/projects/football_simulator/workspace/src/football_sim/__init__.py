"""Football Simulator - A physics-based American football simulation engine.

This package provides a complete football simulation system with:
- Physics-based player movement and ball physics
- AI decision making for offensive and defensive plays
- Comprehensive stats tracking
- Real-time visualization
"""

from .config import Config
from .football_field import Field
from .entities import Player, Formation
from .formation import create_formation
from .ball import Ball
from .play import Play, PlayCall, PlayType, RunDirection, PassRoute, Route, RunPath
from .game import Game, GamePhase, Down, GameResult, PlayResult, Team
from .ai import OffensiveAI, DefensiveAI, AIState, Decision
from .stats import StatsTracker, PlayStats, DriveStats, GameStats

__version__ = "0.1.0"
__all__ = [
    # Config
    "Config",
    # Field
    "Field",
    # Entities
    "Player",
    "Formation",
    # Formation
    "create_formation",
    # Ball
    "Ball",
    # Play
    "Play",
    "PlayCall",
    "PlayType",
    "RunDirection",
    "PassRoute",
    "Route",
    "RunPath",
    # Game
    "Game",
    "GamePhase",
    "Down",
    "GameResult",
    "PlayResult",
    "Team",
    # AI
    "OffensiveAI",
    "DefensiveAI",
    "AIState",
    "Decision",
    # Stats
    "StatsTracker",
    "PlayStats",
    "DriveStats",
    "GameStats",
]

