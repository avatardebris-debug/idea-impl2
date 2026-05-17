"""Tests for MirroringBridge and EventLog."""

import json
import os
import tempfile
import pytest
from agentic_mirroring_game.core.mirroring import MirroringBridge
from agentic_mirroring_game.core.events import GameEvent, EventLog


class TestGameEvent:
    def test_default_values(self):
        e = GameEvent(event_type="test")
        assert e.event_type == "test"
        assert isinstance(e.timestamp, float)
        assert e.turn == 0
        assert e.data == {}

    def test_custom_values(self):
        e = GameEvent(event_type="test", turn=5, data={"key": "value"})
        assert e.event_type == "test"
        assert e.turn == 5
        assert e.data == {"key": "value"}

    def test_to_dict(self):
        e = GameEvent(event_type="test", turn=3, data={"a": 1})
        d = e.to_dict()
        assert d["event_type"] == "test"
        assert d["turn"] == 3
        assert d["data"] == {"a": 1}
        assert "timestamp" in d

    def test_from_dict(self):
        d = {"event_type": "test", "turn": 3, "data": {"a": 1}}
        e = GameEvent.from_dict(d)
        assert e.event_type == "test"
        assert e.turn == 3
        assert e.data == {"a": 1}


class TestEventLog:
    def test_default_values(self):
        log = EventLog()
        assert log.events == []

    def test_add_event(self):
        log = EventLog()
        log.add_event(GameEvent(event_type="test", turn=1))
        assert len(log.events) == 1
        assert log.events[0].event_type == "test"

    def test_add_multiple_events(self):
        log = EventLog()
        log.add_event(GameEvent(event_type="test1", turn=1))
        log.add_event(GameEvent(event_type="test2", turn=2))
        assert len(log.events) == 2
        assert log.events[0].event_type == "test1"
        assert log.events[1].event_type == "test2"

    def test_to_dict(self):
        log = EventLog()
        log.add_event(GameEvent(event_type="test", turn=1))
        d = log.to_dict()
        assert "events" in d
        assert len(d["events"]) == 1
        assert d["events"][0]["event_type"] == "test"

    def test_from_dict(self):
        d = {"events": [{"event_type": "test", "turn": 1, "data": {}}]}
        log = EventLog.from_dict(d)
        assert len(log.events) == 1
        assert log.events[0].event_type == "test"

    def test_from_dict_defaults(self):
        log = EventLog.from_dict({})
        assert log.events == []

    def test_roundtrip(self):
        log = EventLog()
        log.add_event(GameEvent(event_type="test1", turn=1, data={"a": 1}))
        log.add_event(GameEvent(event_type="test2", turn=2, data={"b": 2}))
        d = log.to_dict()
        log2 = EventLog.from_dict(d)
        assert len(log2.events) == 2
        assert log2.events[0].event_type == "test1"
        assert log2.events[0].turn == 1
        assert log2.events[0].data == {"a": 1}
        assert log2.events[1].event_type == "test2"
        assert log2.events[1].turn == 2
        assert log2.events[1].data == {"b": 2}


class TestMirroringBridge:
    def test_default_values(self):
        bridge = MirroringBridge()
        assert bridge.event_log.events == []
        assert bridge.turn == 0
        assert bridge.player_name == ""
        assert bridge.empire_score == 0
        assert bridge.resources == {}
        assert bridge.territory == {}
        assert bridge.buildings == []
        assert bridge.production == {}

    def test_from_dict(self):
        d = {
            "event_log": {"events": []},
            "turn": 5,
            "player_name": "TestPlayer",
            "empire_score": 100,
            "resources": {"gold": 50},
            "territory": {"tiles_controlled": 10},
            "buildings": [{"name": "farm", "level": 1}],
            "production": {"food": 10},
        }
        bridge = MirroringBridge.from_dict(d)
        assert bridge.turn == 5
        assert bridge.player_name == "TestPlayer"
        assert bridge.empire_score == 100
        assert bridge.resources["gold"] == 50
        assert bridge.territory["tiles_controlled"] == 10
        assert len(bridge.buildings) == 1
        assert bridge.buildings[0]["name"] == "farm"
        assert bridge.production["food"] == 10

    def test_from_dict_defaults(self):
        bridge = MirroringBridge.from_dict({})
        assert bridge.turn == 0
        assert bridge.player_name == ""
        assert bridge.empire_score == 0
        assert bridge.resources == {}
        assert bridge.territory == {}
        assert bridge.buildings == []
        assert bridge.production == {}

    def test_to_dict(self):
        bridge = MirroringBridge(
            turn=3,
            player_name="TestPlayer",
            empire_score=50,
            resources={"gold": 20},
            territory={"tiles_controlled": 5},
            buildings=[{"name": "farm", "level": 1}],
            production={"food": 10},
        )
        d = bridge.to_dict()
        assert d["turn"] == 3
        assert d["player_name"] == "TestPlayer"
        assert d["empire_score"] == 50
        assert d["resources"]["gold"] == 20
        assert d["territory"]["tiles_controlled"] == 5
        assert len(d["buildings"]) == 1
        assert d["production"]["food"] == 10

    def test_roundtrip(self):
        bridge = MirroringBridge(
            turn=7,
            player_name="RoundTripPlayer",
            empire_score=200,
            resources={"gold": 100, "wood": 50},
            territory={"tiles_controlled": 20, "max_tiles": 100},
            buildings=[{"name": "farm", "level": 2}],
            production={"food": 10, "population": 2},
        )
        d = bridge.to_dict()
        bridge2 = MirroringBridge.from_dict(d)
        assert bridge2.turn == bridge.turn
        assert bridge2.player_name == bridge.player_name
        assert bridge2.empire_score == bridge.empire_score
        assert bridge2.resources["gold"] == bridge.resources["gold"]
        assert bridge2.resources["wood"] == bridge.resources["wood"]
        assert bridge2.territory["tiles_controlled"] == bridge.territory["tiles_controlled"]
        assert bridge2.territory["max_tiles"] == bridge.territory["max_tiles"]
        assert len(bridge2.buildings) == len(bridge.buildings)
        assert bridge2.buildings[0]["name"] == bridge.buildings[0]["name"]
        assert bridge2.production["food"] == bridge.production["food"]
        assert bridge2.production["population"] == bridge.production["population"]

    def test_save_and_load(self):
        bridge = MirroringBridge(
            turn=5,
            player_name="SaveLoadPlayer",
            empire_score=150,
            resources={"gold": 80},
            territory={"tiles_controlled": 15},
            buildings=[{"name": "mine", "level": 1}],
            production={"gold": 8},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_bridge.json")
            bridge.save_to_file(filepath)
            assert os.path.exists(filepath)
            with open(filepath, "r") as f:
                content = f.read()
                loaded = json.loads(content)
                assert loaded["turn"] == 5
                assert loaded["player_name"] == "SaveLoadPlayer"
            bridge2 = MirroringBridge.load_from_file(filepath)
            assert bridge2.turn == bridge.turn
            assert bridge2.player_name == bridge.player_name
            assert bridge2.empire_score == bridge.empire_score
            assert bridge2.resources["gold"] == bridge.resources["gold"]
            assert bridge2.territory["tiles_controlled"] == bridge.territory["tiles_controlled"]
            assert len(bridge2.buildings) == len(bridge.buildings)
            assert bridge2.production["gold"] == bridge.production["gold"]

    def test_save_load_roundtrip(self):
        bridge = MirroringBridge(
            turn=10,
            player_name="RoundTripSavePlayer",
            empire_score=300,
            resources={"gold": 200, "wood": 100, "stone": 50, "food": 150, "population": 20},
            territory={"tiles_controlled": 30, "max_tiles": 100, "expansion_level": 3},
            buildings=[
                {"name": "farm", "level": 2, "resource_production": {"food": 10}},
                {"name": "mine", "level": 1, "resource_production": {"gold": 8}},
            ],
            production={"food": 10, "gold": 8},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_bridge.json")
            bridge.save_to_file(filepath)
            bridge2 = MirroringBridge.load_from_file(filepath)
            assert bridge2.turn == bridge.turn
            assert bridge2.player_name == bridge.player_name
            assert bridge2.empire_score == bridge.empire_score
            assert bridge2.resources["gold"] == bridge.resources["gold"]
            assert bridge2.resources["wood"] == bridge.resources["wood"]
            assert bridge2.resources["stone"] == bridge.resources["stone"]
            assert bridge2.resources["food"] == bridge.resources["food"]
            assert bridge2.resources["population"] == bridge.resources["population"]
            assert bridge2.territory["tiles_controlled"] == bridge.territory["tiles_controlled"]
            assert bridge2.territory["max_tiles"] == bridge.territory["max_tiles"]
            assert bridge2.territory["expansion_level"] == bridge.territory["expansion_level"]
            assert len(bridge2.buildings) == len(bridge.buildings)
            assert bridge2.buildings[0]["name"] == bridge.buildings[0]["name"]
            assert bridge2.buildings[0]["level"] == bridge.buildings[0]["level"]
            assert bridge2.production["food"] == bridge.production["food"]
            assert bridge2.production["gold"] == bridge.production["gold"]
