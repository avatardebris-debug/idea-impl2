"""Unit tests for BeatSheetService."""

import json
import os
import tempfile
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from beatsheet_generator.service import BeatSheetService


# ── Fixtures ──────────────────────────────────────────────────────────────

def _mock_idea_dict() -> Dict[str, Any]:
    return {
        "title": "The Last Horizon",
        "genre": "Sci-Fi",
        "logline": "In 2087, a lone astronaut discovers a wormhole that changes everything.",
        "characters": [
            {"name": "Alex Mercer", "role": "protagonist", "description": "A brave astronaut."},
            {"name": "Jordan Blake", "role": "antagonist", "description": "A rogue AI."},
            {"name": "Sam Rivera", "role": "ally", "description": "A scientist."},
        ],
    }


@pytest.fixture
def mock_beat_sheet():
    """Create a mock BeatSheet with 15 beats."""
    mock = MagicMock()
    mock.model_dump.return_value = {
        "title": "The Last Horizon",
        "genre": "Sci-Fi",
        "logline": "In 2087, a lone astronaut discovers a wormhole that changes everything.",
        "beats": [
            {"beat_number": i, "beat_name": f"Beat {i}", "summary": f"Summary {i}",
             "phase": "setup", "characters_involved": []}
            for i in range(1, 16)
        ],
    }
    mock.beats = [MagicMock() for _ in range(15)]
    return mock


@pytest.fixture
def mock_generator(mock_beat_sheet):
    """Mock BeatGenerator to return a BeatSheet."""
    with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
        MockGen.return_value.generate_beat_sheet.return_value = mock_beat_sheet
        yield MockGen


# ── Tests ──────────────────────────────────────────────────────────

class TestBeatSheetServiceInit:
    def test_init_with_strings(self):
        service = BeatSheetService(
            title="Test",
            genre="Action",
            logline="A hero fights.",
        )
        assert service.title == "Test"
        assert service.genre == "Action"
        assert service.logline == "A hero fights."
        assert service.characters == []

    def test_from_idea_dict(self):
        service = BeatSheetService.from_idea_dict(_mock_idea_dict())
        assert service.title == "The Last Horizon"
        assert service.genre == "Sci-Fi"
        assert len(service.characters) == 3

    def test_from_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(_mock_idea_dict(), f)
            f.flush()
            path = f.name
        try:
            service = BeatSheetService.from_json_file(path)
            assert service.title == "The Last Horizon"
            assert service.genre == "Sci-Fi"
        finally:
            os.unlink(path)


class TestBeatSheetServiceGenerate:
    def test_generate_from_strings(self, mock_generator, mock_beat_sheet):
        service = BeatSheetService(
            title="Test",
            genre="Drama",
            logline="A story about loss.",
        )
        result = service.generate()

        assert result["title"] == "Test"
        assert result["genre"] == "Drama"
        assert result["num_beats"] == 15
        assert "beat_sheet_json" in result
        assert "beat_sheet_dict" in result
        assert result["beat_sheet"] is mock_beat_sheet

    def test_generate_from_idea_dict(self, mock_generator, mock_beat_sheet):
        service = BeatSheetService.from_idea_dict(_mock_idea_dict())
        result = service.generate()

        assert result["title"] == "The Last Horizon"
        assert result["genre"] == "Sci-Fi"
        assert result["num_beats"] == 15

    def test_generate_missing_logline_raises(self):
        service = BeatSheetService(title="Test", genre="Action", logline="")
        with pytest.raises(ValueError, match="Logline is required"):
            service.generate()

    def test_generate_missing_genre_raises(self):
        service = BeatSheetService(title="Test", genre="", logline="A story.")
        with pytest.raises(ValueError, match="Genre is required"):
            service.generate()


class TestBeatSheetServiceSave:
    def test_save_to_file(self, mock_generator, mock_beat_sheet):
        service = BeatSheetService(title="Test", genre="Action", logline="A story.")
        service.generate()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            saved_path = service.save_to_file(path)
            assert os.path.exists(saved_path)
            with open(saved_path) as f:
                data = json.load(f)
            assert "beat_sheet" in data
        finally:
            os.unlink(path)

    def test_save_without_generate_raises(self):
        service = BeatSheetService(title="Test", genre="Action", logline="A story.")
        with pytest.raises(RuntimeError, match="No beat sheet generated"):
            service.save_to_file("/tmp/test.json")


class TestBeatSheetServiceCharacterEnrichment:
    def test_enrich_beats_with_characters(self, mock_generator, mock_beat_sheet):
        service = BeatSheetService.from_idea_dict(_mock_idea_dict())
        service.generate()

        # Check that protagonist appears in key beats
        # The mock beats are MagicMock objects; their characters_involved
        # attribute is set by _enrich_beats_with_characters.
        mock_beats = mock_beat_sheet.beats
        assert "Alex Mercer" in mock_beats[0].characters_involved  # Opening image
        assert "Alex Mercer" in mock_beats[4].characters_involved  # Catalyst
        assert "Jordan Blake" in mock_beats[7].characters_involved  # Fun and games
        assert "Alex Mercer" in mock_beats[14].characters_involved  # Finale


class TestBeatSheetServiceGet:
    def test_get_beat_sheet_returns_none_before_generate(self):
        service = BeatSheetService(title="Test", genre="Action", logline="A story.")
        assert service.get_beat_sheet() is None

    def test_get_beat_sheet_returns_sheet_after_generate(self, mock_generator, mock_beat_sheet):
        service = BeatSheetService(title="Test", genre="Action", logline="A story.")
        service.generate()
        assert service.get_beat_sheet() is mock_beat_sheet


class TestBeatSheetServiceRepr:
    def test_repr_before_generate(self):
        service = BeatSheetService(title="Test", genre="Action", logline="A story.")
        assert "num_beats=0" in repr(service)

    def test_repr_after_generate(self, mock_generator, mock_beat_sheet):
        service = BeatSheetService(title="Test", genre="Action", logline="A story.")
        service.generate()
        assert "num_beats=15" in repr(service)
