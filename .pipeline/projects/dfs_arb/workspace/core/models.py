"""
Data models for DFS lines, markets, and odds.

Defines Pydantic models for player props, team lines, odds formats,
and market metadata.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class OddsFormat(str, Enum):
    """Supported odds formats."""
    AMERICAN = "american"
    DECIMAL = "decimal"
    FRACTIONAL = "fractional"


class MarketType(str, Enum):
    """Types of DFS markets."""
    PLAYER_PROP = "player_prop"
    TEAM_LINE = "team_line"
    GAME_TOTAL = "game_total"
    TEAM_TOTAL = "team_total"
    PLAYER_POINTS = "player_points"
    PLAYER_RUSHING_YARDS = "player_rushing_yards"
    PLAYER_PASSING_YARDS = "player_passing_yards"
    PLAYER_RECEIVING_YARDS = "player_receiving_yards"
    PLAYER_TOUCHDOWNS = "player_touchdowns"
    PLAYER_ANYTIME_TD = "player_anytime_td"
    PLAYER_FG_MADE = "player_fg_made"
    PLAYER_RECEPTIONS = "player_receptions"
    TWO_SIDED = "two_sided"
    SPREAD = "spread"
    MLR = "mlr"


class OddsEntry(BaseModel):
    """A single odds line from a bookmaker.

    Attributes:
        bookmaker: Name of the bookmaker offering this line.
        odds_value: The numeric odds value.
        odds_format: The format of the odds (american/decimal/fractional).
        side: Which side this odds applies to (e.g., 'over', 'under', 'yes', 'no', team name).
        line_value: The threshold line (e.g., 24.5 points).
        market_type: Type of market this belongs to.
        market_id: Identifier for the market this line is part of.
        player_name: Name of the player (for player props).
        timestamp: When this line was last updated.
        decimal_odds: Decimal odds value (optional, used for direct decimal odds).
        event_name: Name of the event.
        event_date: Date of the event.
        sport: Sport type (e.g., NFL, NBA).
    """
    bookmaker: str
    odds_value: float = Field(alias="odds")
    odds_format: str
    side: str
    line_value: Optional[float] = None
    market_type: MarketType = MarketType.PLAYER_PROP
    market_id: str = ""
    player_name: Optional[str] = None
    timestamp: Optional[str] = None
    decimal_odds: Optional[float] = None
    event_name: Optional[str] = None
    event_date: Optional[str] = None
    sport: Optional[str] = None

    @field_validator("odds_value")
    @classmethod
    def validate_odds_value(cls, v: float) -> float:
        """Validate that odds values are positive."""
        if v <= 0:
            raise ValueError("Odds values must be positive")
        return v

    model_config = {"populate_by_name": True}

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict) -> "OddsEntry":
        """Create from dictionary."""
        if isinstance(data.get("odds_format"), str):
            data["odds_format"] = OddsFormat(data["odds_format"])
        if isinstance(data.get("market_type"), str):
            data["market_type"] = MarketType(data["market_type"])
        return cls(**data)


class PlayerProp(BaseModel):
    """A player proposition bet.

    Attributes:
        player_name: Name of the player.
        player_id: Unique player identifier.
        team: Player's team.
        position: Player's position.
        prop_type: Type of prop (points, yards, touchdowns, etc.).
        line: The threshold line for the prop.
        over_odds: Odds for the over.
        under_odds: Odds for the under.
        bookmaker: Bookmaker offering this prop.
        market_id: Identifier for the market.
    """
    player_name: str
    player_id: Optional[str] = None
    team: str
    position: str
    prop_type: MarketType = MarketType.PLAYER_POINTS
    line: float
    over_odds: OddsEntry
    under_odds: OddsEntry
    bookmaker: str
    market_id: str = ""

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict) -> "PlayerProp":
        """Create from dictionary."""
        if isinstance(data.get("prop_type"), str):
            data["prop_type"] = MarketType(data["prop_type"])
        if isinstance(data.get("over_odds"), dict):
            data["over_odds"] = OddsEntry(**data["over_odds"])
        if isinstance(data.get("under_odds"), dict):
            data["under_odds"] = OddsEntry(**data["under_odds"])
        return cls(**data)


class TeamLine(BaseModel):
    """A team-level line (spread, total, moneyline).

    Attributes:
        team_a: First team.
        team_b: Second team.
        line_type: Type of line (spread, total, moneyline).
        spread: The point spread (if applicable).
        over_odds: Odds for the over.
        under_odds: Odds for the under.
        team_a_moneyline: Moneyline for team A.
        team_b_moneyline: Moneyline for team B.
        bookmaker: Bookmaker offering this line.
        market_id: Identifier for the market.
    """
    team_a: str
    team_b: str
    line_type: str  # "spread", "total", "moneyline"
    spread: Optional[float] = None
    over_odds: Optional[OddsEntry] = None
    under_odds: Optional[OddsEntry] = None
    team_a_moneyline: Optional[OddsEntry] = None
    team_b_moneyline: Optional[OddsEntry] = None
    bookmaker: str
    market_id: str = ""

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict) -> "TeamLine":
        """Create from dictionary."""
        for field in ["over_odds", "under_odds", "team_a_moneyline", "team_b_moneyline"]:
            if isinstance(data.get(field), dict):
                data[field] = OddsEntry(**data[field])
        return cls(**data)


class MarketMetadata(BaseModel):
    """Metadata for a DFS market.

    Attributes:
        market_id: Unique identifier for the market.
        market_type: Type of market.
        event_name: Name of the event/game.
        event_date: Date of the event.
        sport: Sport type (NFL, NBA, etc.).
        status: Current status (open, closed, suspended).
        last_updated: When the market was last updated.
    """
    market_id: str
    market_type: MarketType
    event_name: str
    event_date: str
    sport: str
    status: str = "open"
    last_updated: Optional[str] = None

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict) -> "MarketMetadata":
        """Create from dictionary."""
        if isinstance(data.get("market_type"), str):
            data["market_type"] = MarketType(data["market_type"])
        return cls(**data)
