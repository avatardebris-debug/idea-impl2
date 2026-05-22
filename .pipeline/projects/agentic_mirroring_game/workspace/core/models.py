"""Data models for the game world."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Resources:
    """Resource pool for the game world."""
    gold: int = 0
    wood: int = 0
    stone: int = 0
    food: int = 0
    population: int = 0

    def to_dict(self) -> Dict:
        return {
            "gold": self.gold,
            "wood": self.wood,
            "stone": self.stone,
            "food": self.food,
            "population": self.population,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Resources":
        return cls(
            gold=d.get("gold", 0),
            wood=d.get("wood", 0),
            stone=d.get("stone", 0),
            food=d.get("food", 0),
            population=d.get("population", 0),
        )


@dataclass
class Territory:
    """Territory tracking for the empire."""
    tiles_controlled: int = 0
    max_tiles: int = 100
    expansion_level: int = 0

    def to_dict(self) -> Dict:
        return {
            "tiles_controlled": self.tiles_controlled,
            "max_tiles": self.max_tiles,
            "expansion_level": self.expansion_level,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Territory":
        return cls(
            tiles_controlled=d.get("tiles_controlled", 0),
            max_tiles=d.get("max_tiles", 100),
            expansion_level=d.get("expansion_level", 0),
        )


@dataclass
class Building:
    """A building in the empire."""
    name: str
    level: int = 1
    resource_production: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "level": self.level,
            "resource_production": self.resource_production,
        }


@dataclass
class GameState:
    """Full serializable game state."""
    turn: int = 0
    resources: Resources = field(default_factory=Resources)
    territory: Territory = field(default_factory=Territory)
    buildings: List[Building] = field(default_factory=list)
    empire_score: int = 0
    player_name: str = ""

    def to_dict(self) -> Dict:
        return {
            "turn": self.turn,
            "player_name": self.player_name,
            "empire_score": self.empire_score,
            "resources": self.resources.to_dict(),
            "territory": self.territory.to_dict(),
            "buildings": [b.to_dict() for b in self.buildings],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "GameState":
        return cls(
            turn=d.get("turn", 0),
            player_name=d.get("player_name", ""),
            empire_score=d.get("empire_score", 0),
            resources=Resources.from_dict(d.get("resources", {})),
            territory=Territory.from_dict(d.get("territory", {})),
            buildings=[Building(**b) for b in d.get("buildings", [])],
        )
