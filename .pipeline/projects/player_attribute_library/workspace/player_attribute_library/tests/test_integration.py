"""Integration / end-to-end tests for the player attribute library."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from player_attribute_library import (
    PlayerAttribute,
    create_player,
    get_attribute,
    get_all_attributes,
    match_players,
    save_players,
    load_players,
)


# ------------------------------------------------------------------
# Full workflow integration
# ------------------------------------------------------------------

class TestFullWorkflow:
    """Test the full create → query → match workflow."""

    def test_create_query_match_roundtrip(self):
        """Create players, query attributes, and match them."""
        target = create_player("Target", speed=90, shooting=85, passing=80, defending=30, physical=60, mental=85)
        c1 = create_player("C1", speed=88, shooting=83, passing=78, defending=32, physical=58, mental=82)
        c2 = create_player("C2", speed=70, shooting=95, passing=90, defending=50, physical=80, mental=90)

        # Query
        assert get_attribute(target, "speed") == 90.0
        attrs = get_all_attributes(target)
        assert attrs["shooting"] == 85.0

        # Match
        results = match_players(target, [c1, c2], metric="cosine", top_n=2)
        assert len(results) == 2
        assert results[0]["player"].name == "C1"  # C1 is closer to Target
        assert results[1]["player"].name == "C2"

    def test_euclidean_match_order(self):
        """Euclidean match should rank closest players first (highest inverted score)."""
        target = create_player("T", speed=50, shooting=50, passing=50, defending=50, physical=50, mental=50)
        close = create_player("Close", speed=51, shooting=51, passing=51, defending=51, physical=51, mental=51)
        far = create_player("Far", speed=100, shooting=100, passing=100, defending=100, physical=100, mental=100)

        results = match_players(target, [close, far], metric="euclidean", top_n=2)
        assert results[0]["player"].name == "Close"
        assert results[1]["player"].name == "Far"


# ------------------------------------------------------------------
# CLI integration
# ------------------------------------------------------------------

class TestCLI:
    """Test CLI functionality via subprocess."""

    @pytest.fixture
    def cli_script(self) -> Path:
        """Return path to the CLI script."""
        return Path(__file__).parent.parent / "scripts" / "cli.py"

    def test_cli_help(self, cli_script: Path):
        """Test that --help works."""
        result = subprocess.run(
            [sys.executable, str(cli_script), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()

    def test_cli_create(self, cli_script: Path, tmp_path: Path):
        """Test creating a player via CLI."""
        output_file = tmp_path / "player.json"
        result = subprocess.run(
            [
                sys.executable, str(cli_script), "create",
                "--name", "TestPlayer",
                "--speed", "80",
                "--shooting", "75",
                "--output", str(output_file),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["name"] == "TestPlayer"
        assert data["speed"] == 80.0
        assert data["shooting"] == 75.0

    def test_cli_match(self, cli_script: Path, tmp_path: Path):
        """Test matching players via CLI."""
        # Create target file
        target_file = tmp_path / "target.json"
        target_file.write_text(json.dumps({
            "name": "Target",
            "speed": 90, "shooting": 85, "passing": 80,
            "defending": 30, "physical": 60, "mental": 85,
        }))

        # Create candidates file
        candidates_file = tmp_path / "candidates.json"
        candidates_file.write_text(json.dumps([
            {"name": "C1", "speed": 88, "shooting": 83, "passing": 78, "defending": 32, "physical": 58, "mental": 82},
            {"name": "C2", "speed": 70, "shooting": 95, "passing": 90, "defending": 50, "physical": 80, "mental": 90},
        ]))

        output_file = tmp_path / "matches.json"
        result = subprocess.run(
            [
                sys.executable, str(cli_script), "match",
                "--target-file", str(target_file),
                "--candidates-file", str(candidates_file),
                "--output", str(output_file),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output_file.exists()
        matches = json.loads(output_file.read_text())
        assert len(matches) == 2
        assert matches[0]["player"]["name"] == "C1"


# ------------------------------------------------------------------
# Serialization round-trip
# ------------------------------------------------------------------

class TestSerialization:
    """Test JSON serialization round-trips."""

    def test_player_to_from_json(self):
        """Test that a player can be serialized and deserialized."""
        original = create_player("RoundTrip", speed=85, shooting=90, passing=70, defending=40, physical=65, mental=80)
        json_str = original.to_json()
        restored = PlayerAttribute.from_json(json_str)

        assert restored.name == original.name
        for attr in ["speed", "shooting", "passing", "defending", "physical", "mental"]:
            assert get_attribute(restored, attr) == get_attribute(original, attr)

    def test_save_load_players(self, tmp_path: Path):
        """Test batch save and load."""
        players = [
            create_player("P1", speed=80, shooting=80, passing=80, defending=80, physical=80, mental=80),
            create_player("P2", speed=90, shooting=90, passing=90, defending=90, physical=90, mental=90),
        ]
        filepath = tmp_path / "players.json"
        save_players(players, str(filepath))

        loaded = load_players(str(filepath))
        assert len(loaded) == 2
        for orig, load in zip(players, loaded):
            assert orig.name == load.name
            for attr in DEFAULT_ATTRIBUTES:
                assert get_attribute(orig, attr) == get_attribute(load, attr)

    def test_save_load_empty_list(self, tmp_path: Path):
        """Test saving and loading an empty list."""
        filepath = tmp_path / "empty.json"
        save_players([], str(filepath))
        loaded = load_players(str(filepath))
        assert loaded == []


# ------------------------------------------------------------------
# Helper for DEFAULT_ATTRIBUTES in tests
# ------------------------------------------------------------------

from player_attribute_library.models import DEFAULT_ATTRIBUTES
