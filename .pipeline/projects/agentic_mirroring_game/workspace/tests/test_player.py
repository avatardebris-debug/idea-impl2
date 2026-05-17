"""Tests for Player actions: gather_resources, expand_territory, recruit_units, build_structure, trade."""

import pytest
from agentic_mirroring_game.core.player import Player
from agentic_mirroring_game.core.empire import Empire
from agentic_mirroring_game.core.models import Resources


@pytest.fixture
def player():
    return Player(
        name="TestPlayer",
        resources=Resources(gold=100, wood=50, stone=30, food=80, population=10),
        empire=Empire(),
    )


# ── gather_resources ─────────────────────────────────────────────────

class TestGatherResources:
    def test_gather_success(self, player):
        result = player.perform_action("gather_resources", amount=50)
        assert result["success"] is True
        assert result["action"] == "gather_resources"
        assert result["amount_gathered"] == 50
        # food_cost = max(1, 50 // 2) = 25
        assert result["food_cost"] == 25
        # gold += 50//3 = 16, wood += 16, stone += 16
        assert player.resources.gold == 100 + 16
        assert player.resources.wood == 50 + 16
        assert player.resources.stone == 30 + 16
        assert player.resources.food == 80 - 25

    def test_gather_small_amount(self, player):
        result = player.perform_action("gather_resources", amount=1)
        assert result["success"] is True
        # food_cost = max(1, 1 // 2) = 1
        assert result["food_cost"] == 1
        # gold += 0, wood += 0, stone += 0
        assert player.resources.gold == 100
        assert player.resources.wood == 50
        assert player.resources.stone == 30
        assert player.resources.food == 79

    def test_gather_zero_amount(self, player):
        result = player.perform_action("gather_resources", amount=0)
        assert result["success"] is False
        assert result["error"] == "Amount must be greater than 0"

    def test_gather_negative_amount(self, player):
        result = player.perform_action("gather_resources", amount=-10)
        assert result["success"] is False
        assert result["error"] == "Amount must be greater than 0"

    def test_gather_insufficient_food(self, player):
        # Set food to 0 so we can't afford any gathering
        player.resources.food = 0
        result = player.perform_action("gather_resources", amount=50)
        assert result["success"] is False
        assert result["error"] == "Insufficient food to gather resources"

    def test_gather_exactly_affordable(self, player):
        # food_cost for 50 = 25, so set food to 25
        player.resources.food = 25
        result = player.perform_action("gather_resources", amount=50)
        assert result["success"] is True
        assert player.resources.food == 0


# ── expand_territory ─────────────────────────────────────────────────

class TestExpandTerritory:
    def test_expand_success(self, player):
        result = player.perform_action("expand_territory", tiles=10)
        assert result["success"] is True
        assert result["action"] == "expand_territory"
        assert result["tiles_expanded"] == 10
        # cost = 10 * 5 = 50 gold, 10 * 3 = 30 wood
        assert player.resources.gold == 100 - 50
        assert player.resources.wood == 50 - 30

    def test_expand_zero_tiles(self, player):
        result = player.perform_action("expand_territory", tiles=0)
        assert result["success"] is False
        assert result["error"] == "Tiles must be greater than 0"

    def test_expand_negative_tiles(self, player):
        result = player.perform_action("expand_territory", tiles=-5)
        assert result["success"] is False
        assert result["error"] == "Tiles must be greater than 0"

    def test_expand_insufficient_gold(self, player):
        player.resources.gold = 10
        result = player.perform_action("expand_territory", tiles=10)
        assert result["success"] is False
        assert result["error"] == "Insufficient gold to expand territory"

    def test_expand_insufficient_wood(self, player):
        player.resources.wood = 10
        result = player.perform_action("expand_territory", tiles=10)
        assert result["success"] is False
        assert result["error"] == "Insufficient wood to expand territory"

    def test_expand_exactly_affordable(self, player):
        # cost for 10 tiles = 50 gold, 30 wood
        player.resources.gold = 50
        player.resources.wood = 30
        result = player.perform_action("expand_territory", tiles=10)
        assert result["success"] is True
        assert player.resources.gold == 0
        assert player.resources.wood == 0


# ── recruit_units ────────────────────────────────────────────────────

class TestRecruitUnits:
    def test_recruit_success(self, player):
        result = player.perform_action("recruit_units", count=5)
        assert result["success"] is True
        assert result["action"] == "recruit_units"
        assert result["units_recruited"] == 5
        # cost = 5 * 10 = 50 gold, 5 * 5 = 25 food
        assert player.resources.gold == 100 - 50
        assert player.resources.food == 80 - 25
        assert player.resources.population == 10 + 5

    def test_recruit_zero_units(self, player):
        result = player.perform_action("recruit_units", count=0)
        assert result["success"] is False
        assert result["error"] == "Count must be greater than 0"

    def test_recruit_negative_units(self, player):
        result = player.perform_action("recruit_units", count=-5)
        assert result["success"] is False
        assert result["error"] == "Count must be greater than 0"

    def test_recruit_insufficient_gold(self, player):
        player.resources.gold = 10
        result = player.perform_action("recruit_units", count=5)
        assert result["success"] is False
        assert result["error"] == "Insufficient gold to recruit units"

    def test_recruit_insufficient_food(self, player):
        player.resources.food = 10
        result = player.perform_action("recruit_units", count=5)
        assert result["success"] is False
        assert result["error"] == "Insufficient food to recruit units"

    def test_recruit_exactly_affordable(self, player):
        # cost for 5 units = 50 gold, 25 food
        player.resources.gold = 50
        player.resources.food = 25
        result = player.perform_action("recruit_units", count=5)
        assert result["success"] is True
        assert player.resources.gold == 0
        assert player.resources.food == 0
        assert player.resources.population == 15


# ── build_structure ──────────────────────────────────────────────────

class TestBuildStructure:
    def test_build_farm_success(self, player):
        result = player.perform_action("build_structure", building="farm")
        assert result["success"] is True
        assert result["action"] == "build_structure"
        assert result["building_name"] == "farm"
        # cost = 30 gold, 20 wood
        assert player.resources.gold == 100 - 30
        assert player.resources.wood == 50 - 20

    def test_build_mine_success(self, player):
        result = player.perform_action("build_structure", building="mine")
        assert result["success"] is True
        assert result["building_name"] == "mine"
        # cost = 40 gold, 15 stone
        assert player.resources.gold == 100 - 40
        assert player.resources.stone == 30 - 15

    def test_build_barracks_success(self, player):
        result = player.perform_action("build_structure", building="barracks")
        assert result["success"] is True
        assert result["building_name"] == "barracks"
        # cost = 50 gold, 25 wood, 10 stone
        assert player.resources.gold == 100 - 50
        assert player.resources.wood == 50 - 25
        assert player.resources.stone == 30 - 10

    def test_build_market_success(self, player):
        result = player.perform_action("build_structure", building="market")
        assert result["success"] is True
        assert result["building_name"] == "market"
        # cost = 60 gold, 30 wood, 20 stone
        assert player.resources.gold == 100 - 60
        assert player.resources.wood == 50 - 30
        assert player.resources.stone == 30 - 20

    def test_build_invalid_building(self, player):
        result = player.perform_action("build_structure", building="castle")
        assert result["success"] is False
        assert result["error"] == "Invalid building type: castle"

    def test_build_insufficient_gold(self, player):
        player.resources.gold = 10
        result = player.perform_action("build_structure", building="farm")
        assert result["success"] is False
        assert result["error"] == "Insufficient gold to build farm"

    def test_build_insufficient_wood(self, player):
        player.resources.wood = 10
        result = player.perform_action("build_structure", building="farm")
        assert result["success"] is False
        assert result["error"] == "Insufficient wood to build farm"

    def test_build_exactly_affordable(self, player):
        player.resources.gold = 30
        player.resources.wood = 20
        result = player.perform_action("build_structure", building="farm")
        assert result["success"] is True
        assert player.resources.gold == 0
        assert player.resources.wood == 0


# ── trade ────────────────────────────────────────────────────────────

class TestTrade:
    def test_trade_gold_to_wood(self, player):
        result = player.perform_action(
            "trade", resource_from="gold", amount=20, resource_to="wood"
        )
        assert result["success"] is True
        assert result["action"] == "trade"
        assert result["resource_from"] == "gold"
        assert result["resource_to"] == "wood"
        assert result["amount_traded"] == 20
        assert player.resources.gold == 100 - 20
        assert player.resources.wood == 50 + 16  # 20 * 0.8

    def test_trade_gold_to_stone(self, player):
        result = player.perform_action(
            "trade", resource_from="gold", amount=30, resource_to="stone"
        )
        assert result["success"] is True
        assert player.resources.gold == 100 - 30
        assert player.resources.stone == 30 + 21  # 30 * 0.7

    def test_trade_gold_to_food(self, player):
        result = player.perform_action(
            "trade", resource_from="gold", amount=40, resource_to="food"
        )
        assert result["success"] is True
        assert player.resources.gold == 100 - 40
        assert player.resources.food == 80 + 28  # 40 * 0.7

    def test_trade_wood_to_gold(self, player):
        result = player.perform_action(
            "trade", resource_from="wood", amount=20, resource_to="gold"
        )
        assert result["success"] is True
        assert player.resources.wood == 50 - 20
        assert player.resources.gold == 100 + 14  # 20 * 0.7

    def test_trade_wood_to_stone(self, player):
        result = player.perform_action(
            "trade", resource_from="wood", amount=20, resource_to="stone"
        )
        assert result["success"] is True
        assert player.resources.wood == 50 - 20
        assert player.resources.stone == 30 + 14  # 20 * 0.7

    def test_trade_wood_to_food(self, player):
        result = player.perform_action(
            "trade", resource_from="wood", amount=20, resource_to="food"
        )
        assert result["success"] is True
        assert player.resources.wood == 50 - 20
        assert player.resources.food == 80 + 14  # 20 * 0.7

    def test_trade_stone_to_gold(self, player):
        result = player.perform_action(
            "trade", resource_from="stone", amount=10, resource_to="gold"
        )
        assert result["success"] is True
        assert player.resources.stone == 30 - 10
        assert player.resources.gold == 100 + 7  # 10 * 0.7

    def test_trade_stone_to_wood(self, player):
        result = player.perform_action(
            "trade", resource_from="stone", amount=10, resource_to="wood"
        )
        assert result["success"] is True
        assert player.resources.stone == 30 - 10
        assert player.resources.wood == 50 + 7  # 10 * 0.7

    def test_trade_stone_to_food(self, player):
        result = player.perform_action(
            "trade", resource_from="stone", amount=10, resource_to="food"
        )
        assert result["success"] is True
        assert player.resources.stone == 30 - 10
        assert player.resources.food == 80 + 7  # 10 * 0.7

    def test_trade_food_to_gold(self, player):
        result = player.perform_action(
            "trade", resource_from="food", amount=20, resource_to="gold"
        )
        assert result["success"] is True
        assert player.resources.food == 80 - 20
        assert player.resources.gold == 100 + 14  # 20 * 0.7

    def test_trade_food_to_wood(self, player):
        result = player.perform_action(
            "trade", resource_from="food", amount=20, resource_to="wood"
        )
        assert result["success"] is True
        assert player.resources.food == 80 - 20
        assert player.resources.wood == 50 + 14  # 20 * 0.7

    def test_trade_food_to_stone(self, player):
        result = player.perform_action(
            "trade", resource_from="food", amount=20, resource_to="stone"
        )
        assert result["success"] is True
        assert player.resources.food == 80 - 20
        assert player.resources.stone == 30 + 14  # 20 * 0.7

    def test_trade_zero_amount(self, player):
        result = player.perform_action(
            "trade", resource_from="gold", amount=0, resource_to="wood"
        )
        assert result["success"] is False
        assert result["error"] == "Amount must be greater than 0"

    def test_trade_negative_amount(self, player):
        result = player.perform_action(
            "trade", resource_from="gold", amount=-10, resource_to="wood"
        )
        assert result["success"] is False
        assert result["error"] == "Amount must be greater than 0"

    def test_trade_insufficient_resource(self, player):
        player.resources.gold = 5
        result = player.perform_action(
            "trade", resource_from="gold", amount=10, resource_to="wood"
        )
        assert result["success"] is False
        assert result["error"] == "Insufficient gold to trade"

    def test_trade_invalid_from_resource(self, player):
        result = player.perform_action(
            "trade", resource_from="mana", amount=10, resource_to="wood"
        )
        assert result["success"] is False
        assert result["error"] == "Invalid resource type: mana"

    def test_trade_invalid_to_resource(self, player):
        result = player.perform_action(
            "trade", resource_from="gold", amount=10, resource_to="mana"
        )
        assert result["success"] is False
        assert result["error"] == "Invalid resource type: mana"

    def test_trade_same_resource(self, player):
        result = player.perform_action(
            "trade", resource_from="gold", amount=10, resource_to="gold"
        )
        assert result["success"] is False
        assert result["error"] == "Cannot trade a resource to itself"

    def test_trade_exactly_affordable(self, player):
        player.resources.gold = 20
        result = player.perform_action(
            "trade", resource_from="gold", amount=20, resource_to="wood"
        )
        assert result["success"] is True
        assert player.resources.gold == 0
        assert player.resources.wood == 50 + 16


# ── Unknown action ───────────────────────────────────────────────────

class TestUnknownAction:
    def test_unknown_action(self, player):
        result = player.perform_action("unknown_action", amount=10)
        assert result["success"] is False
        assert result["error"] == "Unknown action: unknown_action"
