"""Player model and action system."""

from typing import Dict, Any, Optional

from agentic_mirroring_game.core.models import Resources, Building
from agentic_mirroring_game.core.empire import Empire


class Player:
    """Represents a player with resources, empire, and actions."""

    def __init__(self, name: str, resources: Resources, empire: Empire):
        self.name = name
        self.resources = resources
        self.empire = empire

    def perform_action(self, action_name: str, **kwargs) -> Dict[str, Any]:
        """Perform an action and return the result."""
        action_fn = self._get_action(action_name)
        if action_fn is None:
            return {"success": False, "error": f"Unknown action: {action_name}"}
        return action_fn(**kwargs)

    def _get_action(self, name: str):
        """Map action name to method."""
        actions = {
            "gather_resources": self._gather_resources,
            "expand_territory": self._expand_territory,
            "recruit_units": self._recruit_units,
            "build_structure": self._build_structure,
            "trade": self._trade,
        }
        return actions.get(name)

    def _gather_resources(self, amount: int) -> Dict[str, Any]:
        """Gather resources from the environment. Costs 1 food per 2 resources gathered."""
        if amount <= 0:
            return {"success": False, "error": "Amount must be greater than 0"}

        food_cost = max(1, amount // 2)
        if self.resources.food < food_cost:
            return {"success": False, "error": "Insufficient food to gather resources"}

        self.resources.food -= food_cost

        # Distribute gathered resources equally among gold, wood, stone
        per_resource = amount // 3
        self.resources.gold += per_resource
        self.resources.wood += per_resource
        self.resources.stone += per_resource

        return {
            "success": True,
            "action": "gather_resources",
            "amount_gathered": amount,
            "food_cost": food_cost,
            "new_resources": self.resources.to_dict(),
        }

    def _expand_territory(self, tiles: int = 5) -> Dict[str, Any]:
        """Expand territory by controlling more tiles. Costs gold and wood."""
        if tiles <= 0:
            return {"success": False, "error": "Tiles must be greater than 0"}

        gold_cost = tiles * 5
        wood_cost = tiles * 3
        if self.resources.gold < gold_cost:
            return {"success": False, "error": "Insufficient gold to expand territory"}
        if self.resources.wood < wood_cost:
            return {"success": False, "error": "Insufficient wood to expand territory"}

        self.resources.gold -= gold_cost
        self.resources.wood -= wood_cost
        self.empire.territory.tiles_controlled += tiles
        self.empire.territory.expansion_level += 1

        return {
            "success": True,
            "action": "expand_territory",
            "tiles_expanded": tiles,
            "new_territory": self.empire.territory.to_dict(),
        }

    def _recruit_units(self, count: int = 5) -> Dict[str, Any]:
        """Recruit population units. Costs food and gold."""
        if count <= 0:
            return {"success": False, "error": "Count must be greater than 0"}

        gold_cost = count * 10
        food_cost = count * 5
        if self.resources.gold < gold_cost:
            return {"success": False, "error": "Insufficient gold to recruit units"}
        if self.resources.food < food_cost:
            return {"success": False, "error": "Insufficient food to recruit units"}

        self.resources.gold -= gold_cost
        self.resources.food -= food_cost
        self.resources.population += count

        return {
            "success": True,
            "action": "recruit_units",
            "units_recruited": count,
            "new_population": self.resources.population,
        }

    def _build_structure(self, building: str = "farm", cost: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Build a structure in the empire. Uses predefined costs if none provided."""
        predefined_costs = {
            "farm": {"gold": 30, "wood": 20},
            "mine": {"gold": 40, "stone": 15},
            "barracks": {"gold": 50, "wood": 25, "stone": 10},
            "market": {"gold": 60, "wood": 30, "stone": 20},
        }

        if building not in predefined_costs:
            return {"success": False, "error": f"Invalid building type: {building}"}

        if cost is None:
            cost = predefined_costs[building]

        # Check if player can afford
        for res, amt in cost.items():
            if getattr(self.resources, res, 0) < amt:
                return {"success": False, "error": f"Insufficient {res} to build {building}"}

        # Deduct costs
        for res, amt in cost.items():
            setattr(self.resources, res, getattr(self.resources, res) - amt)

        # Production values for the building
        production = {
            "farm": {"food": 10, "population": 2},
            "mine": {"gold": 8, "stone": 3},
            "barracks": {"population": 5},
            "market": {"gold": 5, "wood": 3},
        }

        new_building = Building(
            name=building,
            level=1,
            resource_production=production.get(building, {}),
        )
        self.empire.buildings.append(new_building)

        return {
            "success": True,
            "action": "build_structure",
            "building_name": building,
            "cost": cost,
            "new_buildings": [b.to_dict() for b in self.empire.buildings],
        }

    def _trade(self, resource_from: str = "gold", amount: int = 10, resource_to: str = "wood") -> Dict[str, Any]:
        """Trade one resource for another at a variable ratio."""
        valid_resources = {"gold", "wood", "stone", "food"}

        if resource_from not in valid_resources:
            return {"success": False, "error": f"Invalid resource type: {resource_from}"}
        if resource_to not in valid_resources:
            return {"success": False, "error": f"Invalid resource type: {resource_to}"}
        if resource_from == resource_to:
            return {"success": False, "error": "Cannot trade a resource to itself"}
        if amount <= 0:
            return {"success": False, "error": "Amount must be greater than 0"}

        if getattr(self.resources, resource_from, 0) < amount:
            return {"success": False, "error": f"Insufficient {resource_from} to trade"}

        # Trade ratios: gold->wood=0.8, gold->stone=0.7, gold->food=0.7
        # wood->gold=0.7, wood->stone=0.7, wood->food=0.7
        # stone->gold=0.7, stone->wood=0.7, stone->food=0.7
        # food->gold=0.7, food->wood=0.7, food->stone=0.7
        trade_ratios = {
            ("gold", "wood"): 0.8,
            ("gold", "stone"): 0.7,
            ("gold", "food"): 0.7,
            ("wood", "gold"): 0.7,
            ("wood", "stone"): 0.7,
            ("wood", "food"): 0.7,
            ("stone", "gold"): 0.7,
            ("stone", "wood"): 0.7,
            ("stone", "food"): 0.7,
            ("food", "gold"): 0.7,
            ("food", "wood"): 0.7,
            ("food", "stone"): 0.7,
        }

        ratio = trade_ratios.get((resource_from, resource_to), 0.7)
        received = int(amount * ratio)

        setattr(self.resources, resource_from, getattr(self.resources, resource_from) - amount)
        setattr(self.resources, resource_to, getattr(self.resources, resource_to) + received)

        return {
            "success": True,
            "action": "trade",
            "resource_from": resource_from,
            "resource_to": resource_to,
            "amount_traded": amount,
            "amount_received": received,
            "new_resources": self.resources.to_dict(),
        }
