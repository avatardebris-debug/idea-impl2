"""Tests for Empire mechanics: scoring, construction, territory expansion, production."""

import pytest
from agentic_mirroring_game.core.empire import Empire
from agentic_mirroring_game.core.models import Territory, Building


class TestEmpireScore:
    def test_empty_empire_score(self):
        e = Empire()
        assert e.empire_score == 0

    def test_territory_contribution(self):
        e = Empire(territory=Territory(tiles_controlled=10, expansion_level=2))
        # tiles: 10 * 5 = 50, expansion: 2 * 10 = 20
        assert e.empire_score == 70

    def test_building_contribution(self):
        e = Empire(
            territory=Territory(tiles_controlled=0, expansion_level=0),
            buildings=[
                Building(name="farm", level=1, resource_production={"food": 10, "population": 2}),
                Building(name="mine", level=2, resource_production={"gold": 8, "stone": 3}),
            ],
        )
        # buildings: (1*15 + 10*3 + 2*2*3) + (2*15 + 8*3 + 3*3)
        # = (15 + 30 + 12) + (30 + 24 + 9) = 57 + 63 = 120
        assert e.empire_score == 120

    def test_combined_score(self):
        e = Empire(
            territory=Territory(tiles_controlled=5, expansion_level=1),
            buildings=[
                Building(name="farm", level=1, resource_production={"food": 10}),
            ],
        )
        # territory: 5*5 + 1*10 = 35
        # building: 1*15 + 10*3 = 45
        # population: 5 (from tiles_controlled)
        assert e.empire_score == 35 + 45 + 5

    def test_calculate_score_returns_same(self):
        e = Empire(
            territory=Territory(tiles_controlled=10, expansion_level=3),
            buildings=[
                Building(name="farm", level=2, resource_production={"food": 10}),
            ],
        )
        assert e.calculate_score() == e.empire_score


class TestConstructBuilding:
    def test_add_new_building(self):
        e = Empire()
        b = Building(name="farm", level=1, resource_production={"food": 10})
        result = e.construct_building(b)
        assert result is True
        assert len(e.buildings) == 1
        assert e.buildings[0].name == "farm"

    def test_upgrade_existing_building(self):
        e = Empire()
        b1 = Building(name="farm", level=1, resource_production={"food": 10})
        e.construct_building(b1)

        b2 = Building(name="farm", level=1, resource_production={"food": 5, "population": 2})
        result = e.construct_building(b2)
        assert result is True
        assert len(e.buildings) == 1
        assert e.buildings[0].level == 2
        assert e.buildings[0].resource_production["food"] == 15
        assert e.buildings[0].resource_production["population"] == 2

    def test_multiple_buildings(self):
        e = Empire()
        for name, prod in [("farm", {"food": 10}), ("mine", {"gold": 8}), ("barracks", {"population": 5})]:
            e.construct_building(Building(name=name, level=1, resource_production=prod))
        assert len(e.buildings) == 3

    def test_duplicate_building_upgrades_only(self):
        e = Empire()
        e.construct_building(Building(name="farm", level=1, resource_production={"food": 10}))
        e.construct_building(Building(name="farm", level=1, resource_production={"food": 5}))
        e.construct_building(Building(name="farm", level=1, resource_production={"food": 3}))
        assert len(e.buildings) == 1
        assert e.buildings[0].level == 4
        assert e.buildings[0].resource_production["food"] == 18


class TestExpandTerritory:
    def test_expand_success(self):
        e = Empire(territory=Territory(tiles_controlled=0, max_tiles=100, expansion_level=0))
        result = e.expand_territory(10)
        assert result is True
        assert e.territory.tiles_controlled == 10
        assert e.territory.expansion_level == 1

    def test_expand_partial_when_near_max(self):
        e = Empire(territory=Territory(tiles_controlled=95, max_tiles=100, expansion_level=2))
        result = e.expand_territory(10)
        assert result is True
        assert e.territory.tiles_controlled == 100
        assert e.territory.expansion_level == 3

    def test_expand_fail_at_max(self):
        e = Empire(territory=Territory(tiles_controlled=100, max_tiles=100, expansion_level=5))
        result = e.expand_territory(5)
        assert result is False
        assert e.territory.tiles_controlled == 100

    def test_expand_zero_tiles(self):
        e = Empire(territory=Territory(tiles_controlled=0, max_tiles=100, expansion_level=0))
        result = e.expand_territory(0)
        assert result is False
        assert e.territory.tiles_controlled == 0

    def test_expand_negative_tiles(self):
        e = Empire(territory=Territory(tiles_controlled=0, max_tiles=100, expansion_level=0))
        result = e.expand_territory(-5)
        assert result is False


class TestGetProductionSummary:
    def test_empty_empire(self):
        e = Empire()
        assert e.get_production_summary() == {}

    def test_single_building(self):
        e = Empire(
            buildings=[
                Building(name="farm", level=1, resource_production={"food": 10, "population": 2}),
            ]
        )
        assert e.get_production_summary() == {"food": 10, "population": 2}

    def test_multiple_buildings(self):
        e = Empire(
            buildings=[
                Building(name="farm", level=1, resource_production={"food": 10, "population": 2}),
                Building(name="mine", level=1, resource_production={"gold": 8, "stone": 3}),
                Building(name="farm", level=1, resource_production={"food": 5}),
            ]
        )
        prod = e.get_production_summary()
        assert prod["food"] == 15
        assert prod["population"] == 2
        assert prod["gold"] == 8
        assert prod["stone"] == 3

    def test_overlapping_resources(self):
        e = Empire(
            buildings=[
                Building(name="farm1", level=1, resource_production={"food": 10}),
                Building(name="farm2", level=1, resource_production={"food": 5}),
            ]
        )
        assert e.get_production_summary()["food"] == 15


class TestEmpireToDict:
    def test_to_dict_structure(self):
        e = Empire(
            territory=Territory(tiles_controlled=5, max_tiles=100, expansion_level=1),
            buildings=[
                Building(name="farm", level=1, resource_production={"food": 10}),
            ],
        )
        d = e.to_dict()
        assert "territory" in d
        assert "buildings" in d
        assert "empire_score" in d
        assert "production" in d
        assert d["territory"]["tiles_controlled"] == 5
        assert len(d["buildings"]) == 1
        assert d["buildings"][0]["name"] == "farm"
        assert d["production"]["food"] == 10

    def test_empty_empire_to_dict(self):
        e = Empire()
        d = e.to_dict()
        assert d["territory"]["tiles_controlled"] == 0
        assert d["buildings"] == []
        assert d["empire_score"] == 0
        assert d["production"] == {}
