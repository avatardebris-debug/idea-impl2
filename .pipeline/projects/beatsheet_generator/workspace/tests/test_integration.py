"""Integration tests for beatsheet_generator."""

import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from beatsheet_generator.service import BeatSheetService


def _mock_idea_dict() -> Dict[str, Any]:
    return {
        "title": "The Last Horizon",
        "genre": "Sci-Fi",
        "logline": "In 2087, a lone astronaut discovers a wormhole that changes everything.",
        "characters": [
            {"name": "Alex Mercer", "role": "protagonist", "description": "A brave astronaut."},
            {"name": "Jordan Blake", "role": "antagonist", "description": "A rogue AI."},
            {"name": "Sam Rivera", "role": "ally", "description": "A scientist."},
            {"name": "Dr. Chen", "role": "mentor", "description": "A retired space physicist."},
        ],
    }


def _create_mock_beat_sheet() -> MagicMock:
    """Create a mock BeatSheet with 15 beats and proper structure."""
    mock = MagicMock()
    mock.model_dump.return_value = {
        "title": "The Last Horizon",
        "genre": "Sci-Fi",
        "logline": "In 2087, a lone astronaut discovers a wormhole that changes everything.",
        "beats": [
            {
                "beat_number": i,
                "beat_name": f"Beat {i}",
                "summary": f"Summary for beat {i}",
                "description": f"Description for beat {i}",
                "phase": ["setup", "setup", "setup", "setup", "setup", "setup", "confrontation", "confrontation", "confrontation", "confrontation", "confrontation", "confrontation", "confrontation", "resolution", "resolution"][i - 1],
                "characters_involved": [],
            }
            for i in range(1, 16)
        ],
    }
    # Create mock Beat objects
    mock.beats = [MagicMock() for _ in range(15)]
    return mock


class TestEndToEndMovieIdeaToBeatSheet:
    """Test the full flow: movie idea → beat sheet."""

    def test_generate_beat_sheet_from_movie_idea(self):
        """Generate a beat sheet from a movie idea dict."""
        with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
            mock_sheet = _create_mock_beat_sheet()
            MockGen.return_value.generate_beat_sheet.return_value = mock_sheet

            service = BeatSheetService.from_idea_dict(_mock_idea_dict())
            result = service.generate()

            # Verify result structure
            assert result["title"] == "The Last Horizon"
            assert result["genre"] == "Sci-Fi"
            assert result["num_beats"] == 15
            assert "beat_sheet_json" in result
            assert "beat_sheet_dict" in result

            # Verify JSON is valid
            json_data = json.loads(result["beat_sheet_json"])
            assert "beats" in json_data
            assert len(json_data["beats"]) == 15

    def test_generate_beat_sheet_from_json_file(self):
        """Generate a beat sheet from a JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(_mock_idea_dict(), f)
            f.flush()
            path = f.name

        try:
            with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
                mock_sheet = _create_mock_beat_sheet()
                MockGen.return_value.generate_beat_sheet.return_value = mock_sheet

                service = BeatSheetService.from_json_file(path)
                result = service.generate()

                assert result["title"] == "The Last Horizon"
                assert result["genre"] == "Sci-Fi"
                assert result["num_beats"] == 15
        finally:
            os.unlink(path)

    def test_generate_beat_sheet_from_strings(self):
        """Generate a beat sheet from raw strings."""
        with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
            mock_sheet = _create_mock_beat_sheet()
            MockGen.return_value.generate_beat_sheet.return_value = mock_sheet

            service = BeatSheetService(
                title="Test Movie",
                genre="Drama",
                logline="A story about a family.",
            )
            result = service.generate()

            assert result["title"] == "Test Movie"
            assert result["genre"] == "Drama"
            assert result["num_beats"] == 15


class TestPipelineIntegration:
    """Test integration with ai_movie_gen_suite models."""

    def test_beat_sheet_serialization(self):
        """Test that beat sheets serialize correctly."""
        with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
            mock_sheet = _create_mock_beat_sheet()
            MockGen.return_value.generate_beat_sheet.return_value = mock_sheet

            service = BeatSheetService.from_idea_dict(_mock_idea_dict())
            result = service.generate()

            # Verify dict serialization
            beat_sheet_dict = result["beat_sheet_dict"]
            assert "beats" in beat_sheet_dict
            assert len(beat_sheet_dict["beats"]) == 15

            # Verify JSON serialization
            json_data = json.loads(result["beat_sheet_json"])
            assert "beats" in json_data
            assert len(json_data["beats"]) == 15

    def test_save_and_load_beat_sheet(self):
        """Test saving and loading a beat sheet."""
        with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
            mock_sheet = _create_mock_beat_sheet()
            MockGen.return_value.generate_beat_sheet.return_value = mock_sheet

            service = BeatSheetService.from_idea_dict(_mock_idea_dict())
            service.generate()

            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                path = f.name

            try:
                saved_path = service.save_to_file(path)
                assert os.path.exists(saved_path)

                # Load and verify
                with open(saved_path) as f:
                    data = json.load(f)
                assert "beat_sheet" in data
                assert "beats" in data["beat_sheet"]
                assert len(data["beat_sheet"]["beats"]) == 15
            finally:
                os.unlink(path)


class TestCharacterEnrichment:
    """Test character enrichment logic."""

    def test_enrich_beats_with_characters(self):
        """Test that characters are enriched in beats."""
        with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
            mock_sheet = _create_mock_beat_sheet()
            MockGen.return_value.generate_beat_sheet.return_value = mock_sheet

            service = BeatSheetService.from_idea_dict(_mock_idea_dict())
            service.generate()

            # Get the enriched beats
            enriched_beats = mock_sheet.model_dump()["beats"]

            # Check key beats have correct characters
            assert "Alex Mercer" in enriched_beats[0]["characters_involved"]  # Opening image
            assert "Alex Mercer" in enriched_beats[4]["characters_involved"]  # Catalyst
            assert "Jordan Blake" in enriched_beats[7]["characters_involved"]  # Fun and games
            assert "Alex Mercer" in enriched_beats[14]["characters_involved"]  # Finale

    def test_enrich_beats_with_no_characters(self):
        """Test that beats are not enriched when no characters are provided."""
        with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
            mock_sheet = _create_mock_beat_sheet()
            MockGen.return_value.generate_beat_sheet.return_value = mock_sheet

            service = BeatSheetService(
                title="Test",
                genre="Action",
                logline="A story.",
            )
            service.generate()

            # Get the beats
            enriched_beats = mock_sheet.model_dump()["beats"]

            # All characters_involved should be empty
            for beat in enriched_beats:
                assert beat["characters_involved"] == []


class TestErrorHandling:
    """Test error handling."""

    def test_missing_logline_raises(self):
        """Test that missing logline raises ValueError."""
        service = BeatSheetService(title="Test", genre="Action", logline="")
        with pytest.raises(ValueError, match="Logline is required"):
            service.generate()

    def test_missing_genre_raises(self):
        """Test that missing genre raises ValueError."""
        service = BeatSheetService(title="Test", genre="", logline="A story.")
        with pytest.raises(ValueError, match="Genre is required"):
            service.generate()

    def test_save_without_generate_raises(self):
        """Test that saving without generating raises RuntimeError."""
        service = BeatSheetService(title="Test", genre="Action", logline="A story.")
        with pytest.raises(RuntimeError, match="No beat sheet generated"):
            service.save_to_file("/tmp/test.json")

    def test_invalid_json_file_raises(self):
        """Test that invalid JSON file raises error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json")
            f.flush()
            path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                BeatSheetService.from_json_file(path)
        finally:
            os.unlink(path)


class TestCLIIntegration:
    """Test CLI integration."""

    def test_cli_integration(self, capsys):
        """Test CLI integration with movie_idea_generator."""
        with patch("beatsheet_generator.cli.BeatSheetService") as MockService:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = {
                "beat_sheet": _create_mock_beat_sheet(),
                "beat_sheet_json": json.dumps({"beats": []}),
                "beat_sheet_dict": {"beats": []},
                "output_path": None,
                "title": "Test Movie",
                "genre": "Action",
                "num_beats": 15,
            }
            MockService.return_value = mock_instance

            from beatsheet_generator.cli import main

            main(["--title", "Test Movie", "--genre", "Action", "--logline", "A story.", "--format", "text"])

            captured = capsys.readouterr()
            assert "Test Movie" in captured.out
            assert "Action" in captured.out


class TestBeatSheetServiceRepr:
    """Test BeatSheetService repr."""

    def test_repr_before_generate(self):
        """Test repr before generate."""
        service = BeatSheetService(title="Test", genre="Action", logline="A story.")
        assert "num_beats=0" in repr(service)

    def test_repr_after_generate(self):
        """Test repr after generate."""
        with patch("beatsheet_generator.service.BeatGenerator") as MockGen:
            mock_sheet = _create_mock_beat_sheet()
            MockGen.return_value.generate_beat_sheet.return_value = mock_sheet

            service = BeatSheetService(title="Test", genre="Action", logline="A story.")
            service.generate()
            assert "num_beats=15" in repr(service)
