"""Empire building mechanics — territory, buildings, population, scoring."""

from typing import Dict, List, Optional

from agentic_mirroring_game.core.models import Territory, Building


class Empire:
    """Tracks territory, buildings, population growth, and resource production."""

    def __init__(
        self,
        territory: Optional[Territory] = None,
        buildings: Optional[List[Building]] = None,
    ):
        self.territory = territory or Territory()
        self.buildings = buildings or []

    @property
    def empire_score(self) -> int:
        """Calculate overall empire progress score."""
        score = 0

        # Territory contribution
        score += self.territory.tiles_controlled * 5
        score += self.territory.expansion_level * 10

        # Building contribution
        for building in self.buildings:
            score += building.level * 15
            for res, amount in building.resource_production.items():
                if res == "population":
                    score += amount * (building.level + 1) * 3
                else:
                    score += amount * 3

        # Population contribution (from tiles controlled)
        score += self.territory.tiles_controlled

        return score

    def calculate_score(self) -> int:
        """Recalculate and return the empire score."""
        return self.empire_score

    def construct_building(self, building: Building) -> bool:
        """Add a building to the empire."""
        # Check for duplicate building names
        for existing in self.buildings:
            if existing.name == building.name:
                # Upgrade existing building
                existing.level += 1
                for res, amount in building.resource_production.items():
                    existing.resource_production[res] = existing.resource_production.get(res, 0) + amount
                return True
        # Create new building
        new_building = Building(name=building.name, level=building.level, resource_production=dict(building.resource_production))
        self.buildings.append(new_building)
        return True

    def expand_territory(self, tiles: int) -> bool:
        """Expand territory by the given number of tiles."""
        if self.territory.tiles_controlled + tiles > self.territory.max_tiles:
            tiles = self.territory.max_tiles - self.territory.tiles_controlled
        if tiles <= 0:
            return False
        self.territory.tiles_controlled += tiles
        self.territory.expansion_level += 1
        return True

    def get_production_summary(self) -> Dict[str, int]:
        """Get total resource production per turn from all buildings."""
        production = {}
        for building in self.buildings:
            for res, amount in building.resource_production.items():
                production[res] = production.get(res, 0) + amount
        return production

    def to_dict(self) -> Dict:
        """Serialize empire state."""
        return {
            "territory": self.territory.to_dict(),
            "buildings": [b.to_dict() for b in self.buildings],
            "empire_score": self.empire_score,
            "production": self.get_production_summary(),
        }
