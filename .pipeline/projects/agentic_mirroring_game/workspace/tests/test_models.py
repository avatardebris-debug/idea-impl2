"""Tests for data models: Resources, Territory, Building, GameState."""

import pytest
from agentic_mirroring_game.core.models import (
    Resources,
    Territory,
    Building,
    GameState,
)


# ── Resources ──────────────────────────────────────────────────────────────

class TestResources:
    def test_default_values(self):
        r = Resources()
        assert r.gold == 0
        assert r.wood == 0
        assert r.stone == 0
        assert r.food == 0
        assert r.population == 0

    def test_custom_values(self):
        r = Resources(gold=100, wood=50, stone=30, food=80, population=10)
        assert r.gold == 100
        assert r.wood == 50
        assert r.stone == 30
        assert r.food == 80
        assert r.population == 10

    def test_to_dict(self):
        r = Resources(gold=10, wood=20, stone=30, food=40, population=5)
        d = r.to_dict()
        assert d == {
            "gold": 10,
            "wood": 20,
            "stone": 30,
            "food": 40,
            "population": 5,
        }

    def test_from_dict(self):
        d = {"gold": 10, "wood": 20, "stone": 30, "food": 40, "population": 5}
        r = Resources.from_dict(d)
        assert r.gold == 10
        assert r.wood == 20
        assert r.stone == 30
        assert r.food == 40
        assert r.population == 5

    def test_from_dict_defaults(self):
        r = Resources.from_dict({})
        assert r.gold == 0
        assert r.wood == 0
        assert r.stone == 0
        assert r.food == 0
        assert r.population == 0

    def test_roundtrip(self):
        r = Resources(gold=100, wood=50, stone=30, food=80, population=10)
        d = r.to_dict()
        r2 = Resources.from_dict(d)
        assert r2.gold == r.gold
        assert r2.wood == r.wood
        assert r2.stone == r.stone
        assert r2.food == r.food
        assert r2.population == r.population


# ── Territory ──────────────────────────────────────────────────────────────

class TestTerritory:
    def test_default_values(self):
        t = Territory()
        assert t.tiles_controlled == 0
        assert t.max_tiles == 100
        assert t.expansion_level == 0

    def test_custom_values(self):
        t = Territory(tiles_controlled=10, max_tiles=200, expansion_level=3)
        assert t.tiles_controlled == 10
        assert t.max_tiles == 200
        assert t.expansion_level == 3

    def test_to_dict(self):
        t = Territory(tiles_controlled=10, max_tiles=200, expansion_level=3)
        d = t.to_dict()
        assert d == {
            "tiles_controlled": 10,
            "max_tiles": 200,
            "expansion_level": 3,
        }

    def test_from_dict(self):
        d = {"tiles_controlled": 10, "max_tiles": 200, "expansion_level": 3}
        t = Territory.from_dict(d)
        assert t.tiles_controlled == 10
        assert t.max_tiles == 200
        assert t.expansion_level == 3

    def test_from_dict_defaults(self):
        t = Territory.from_dict({})
        assert t.tiles_controlled == 0
        assert t.max_tiles == 100
        assert t.expansion_level == 0

    def test_roundtrip(self):
        t = Territory(tiles_controlled=10, max_tiles=200, expansion_level=3)
        d = t.to_dict()
        t2 = Territory.from_dict(d)
        assert t2.tiles_controlled == t.tiles_controlled
        assert t2.max_tiles == t.max_tiles
        assert t2.expansion_level == t.expansion_level


# ── Building ───────────────────────────────────────────────────────────────

class TestBuilding:
    def test_default_values(self):
        b = Building(name="farm")
        assert b.name == "farm"
        assert b.level == 1
        assert b.resource_production == {}

    def test_custom_values(self):
        b = Building(name="mine", level=3, resource_production={"gold": 8, "stone": 3})
        assert b.name == "mine"
        assert b.level == 3
        assert b.resource_production == {"gold": 8, "stone": 3}

    def test_to_dict(self):
        b = Building(name="farm", level=2, resource_production={"food": 10, "population": 2})
        d = b.to_dict()
        assert d == {
            "name": "farm",
            "level": 2,
            "resource_production": {"food": 10, "population": 2},
        }

    def test_from_dict(self):
        d = {"name": "farm", "level": 2, "resource_production": {"food": 10, "population": 2}}
        b = Building(**d)
        assert b.name == "farm"
        assert b.level == 2
        assert b.resource_production == {"food": 10, "population": 2}


# ── GameState ──────────────────────────────────────────────────────────────

class TestGameState:
    def test_default_values(self):
        gs = GameState()
        assert gs.turn == 0
        assert gs.empire_score == 0
        assert gs.player_name == ""
        assert gs.resources.gold == 0
        assert gs.territory.tiles_controlled == 0
        assert gs.buildings == []

    def test_custom_values(self):
        gs = GameState(
            turn=5,
            player_name="TestPlayer",
            empire_score=150,
        )
        gs.resources = Resources(gold=100, wood=50, stone=30, food=80, population=10)
        gs.territory = Territory(tiles_controlled=10, max_tiles=100, expansion_level=2)
        gs.buildings = [Building(name="farm", level=1, resource_production={"food": 10})]

        assert gs.turn == 5
        assert gs.player_name == "TestPlayer"
        assert gs.empire_score == 150
        assert gs.resources.gold == 100
        assert gs.territory.tiles_controlled == 10
        assert len(gs.buildings) == 1

    def test_to_dict(self):
        gs = GameState(
            turn=3,
            player_name="TestPlayer",
            empire_score=75,
        )
        gs.resources = Resources(gold=100, wood=50, stone=30, food=80, population=10)
        gs.territory = Territory(tiles_controlled=5, max_tiles=100, expansion_level=1)
        gs.buildings = [Building(name="farm", level=1, resource_production={"food": 10})]

        d = gs.to_dict()
        assert d["turn"] == 3
        assert d["player_name"] == "TestPlayer"
        assert d["empire_score"] == 75
        assert d["resources"]["gold"] == 100
        assert d["territory"]["tiles_controlled"] == 5
        assert len(d["buildings"]) == 1
        assert d["buildings"][0]["name"] == "farm"

    def test_from_dict(self):
        d = {
            "turn": 3,
            "player_name": "TestPlayer",
            "empire_score": 75,
            "resources": {"gold": 100, "wood": 50, "stone": 30, "food": 80, "population": 10},
            "territory": {"tiles_controlled": 5, "max_tiles": 100, "expansion_level": 1},
            "buildings": [{"name": "farm", "level": 1, "resource_production": {"food": 10}}],
        }
        gs = GameState.from_dict(d)
        assert gs.turn == 3
        assert gs.player_name == "TestPlayer"
        assert gs.empire_score == 75
        assert gs.resources.gold == 100
        assert gs.territory.tiles_controlled == 5
        assert len(gs.buildings) == 1
        assert gs.buildings[0].name == "farm"

    def test_from_dict_defaults(self):
        gs = GameState.from_dict({})
        assert gs.turn == 0
        assert gs.player_name == ""
        assert gs.empire_score == 0
        assert gs.resources.gold == 0
        assert gs.territory.tiles_controlled == 0
        assert gs.buildings == []

    def test_roundtrip(self):
        gs = GameState(
            turn=7,
            player_name="RoundTripPlayer",
            empire_score=200,
        )
        gs.resources = Resources(gold=200, wood=100, stone=50, food=150, population=20)
        gs.territory = Territory(tiles_controlled=20, max_tiles=100, expansion_level=4)
        gs.buildings = [
            Building(name="farm", level=2, resource_production={"food": 10, "population": 2}),
            Building(name="mine", level=1, resource_production={"gold": 8, "stone": 3}),
        ]

        d = gs.to_dict()
        gs2 = GameState.from_dict(d)

        assert gs2.turn == gs.turn
        assert gs2.player_name == gs.player_name
        assert gs2.empire_score == gs.empire_score
        assert gs2.resources.gold == gs.resources.gold
        assert gs2.resources.wood == gs.resources.wood
        assert gs2.resources.stone == gs.resources.stone
        assert gs2.resources.food == gs.resources.food
        assert gs2.resources.population == gs.resources.population
        assert gs2.territory.tiles_controlled == gs.territory.tiles_controlled
        assert gs2.territory.max_tiles == gs.territory.max_tiles
        assert gs2.territory.expansion_level == gs.territory.expansion_level
        assert len(gs2.buildings) == len(gs.buildings)
        assert gs2.buildings[0].name == gs.buildings[0].name
        assert gs2.buildings[0].level == gs.buildings[0].level
        assert gs2.buildings[0].resource_production == gs.buildings[0].resource_production
