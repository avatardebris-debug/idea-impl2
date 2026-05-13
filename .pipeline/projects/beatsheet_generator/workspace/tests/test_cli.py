"""Unit tests for beatsheet_generator CLI."""

import json
import os
import tempfile
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from beatsheet_generator.cli import main


def _mock_idea_dict() -> dict:
    return {
        "title": "The Last Horizon",
        "genre": "Sci-Fi",
        "logline": "In 2087, a lone astronaut discovers a wormhole.",
        "characters": [
            {"name": "Alex", "role": "protagonist"},
            {"name": "Jordan", "role": "antagonist"},
        ],
    }


def _mock_beat_sheet() -> MagicMock:
    mock = MagicMock()
    mock.model_dump.return_value = {
        "title": "The Last Horizon",
        "genre": "Sci-Fi",
        "logline": "In 2087, a lone astronaut discovers a wormhole.",
        "beats": [
            {"beat_number": i, "beat_name": f"Beat {i}", "summary": f"Summary {i}",
             "phase": "setup", "characters_involved": []}
            for i in range(1, 16)
        ],
    }
    mock.beats = [MagicMock() for _ in range(15)]
    return mock


class TestCLIGeneration:
    def test_cli_generates_beat_sheet(self, capsys):
        """Test basic CLI invocation with title/genre/logline."""
        with patch("beatsheet_generator.cli.BeatSheetService") as MockService:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = {
                "beat_sheet": _mock_beat_sheet(),
                "beat_sheet_json": json.dumps({"beats": []}),
                "beat_sheet_dict": {"beats": []},
                "output_path": None,
                "title": "Test Movie",
                "genre": "Action",
                "num_beats": 15,
            }
            MockService.return_value = mock_instance

            main(["--title", "Test Movie", "--genre", "Action", "--logline", "A story."])

            MockService.assert_called_once_with(
                title="Test Movie",
                genre="Action",
                logline="A story.",
                tone="",
            )
            mock_instance.generate.assert_called_once()

    def test_cli_json_format(self, capsys):
        """Test JSON format output."""
        with patch("beatsheet_generator.cli.BeatSheetService") as MockService:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = {
                "beat_sheet": _mock_beat_sheet(),
                "beat_sheet_json": json.dumps({"beats": [], "title": "Test"}),
                "beat_sheet_dict": {"beats": []},
                "output_path": None,
                "title": "Test",
                "genre": "Action",
                "num_beats": 15,
            }
            MockService.return_value = mock_instance

            main(["--title", "Test", "--genre", "Action", "--logline", "A story.", "--format", "json"])

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "beats" in output
            assert output["title"] == "Test"

    def test_cli_text_format(self, capsys):
        """Test text format output."""
        with patch("beatsheet_generator.cli.BeatSheetService") as MockService:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = {
                "beat_sheet": _mock_beat_sheet(),
                "beat_sheet_json": json.dumps({"beats": []}),
                "beat_sheet_dict": {"beats": [{"beat_number": 1, "beat_name": "Opening Image", "summary": "Start", "phase": "setup", "characters_involved": []}]},
                "output_path": None,
                "title": "Test Movie",
                "genre": "Action",
                "num_beats": 15,
            }
            MockService.return_value = mock_instance

            main(["--title", "Test Movie", "--genre", "Action", "--logline", "A story.", "--format", "text"])

            captured = capsys.readouterr()
            assert "Test Movie" in captured.out
            assert "Opening Image" in captured.out

    def test_cli_source_movie_idea(self, capsys):
        """Test loading idea from a JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(_mock_idea_dict(), f)
            f.flush()
            idea_path = f.name

        try:
            with patch("beatsheet_generator.cli.BeatSheetService") as MockService:
                mock_instance = MagicMock()
                mock_instance.generate.return_value = {
                    "beat_sheet": _mock_beat_sheet(),
                    "beat_sheet_json": json.dumps({"beats": [], "title": "The Last Horizon"}),
                    "beat_sheet_dict": {"beats": []},
                    "output_path": None,
                    "title": "The Last Horizon",
                    "genre": "Sci-Fi",
                    "num_beats": 15,
                }
                MockService.return_value = mock_instance
                MockService.from_json_file.return_value = mock_instance

                main(["--source-movie-idea", idea_path, "--format", "json"])

                # Verify the service was called with from_json_file
                MockService.from_json_file.assert_called_once_with(idea_path)
                mock_instance.generate.assert_called_once()

                captured = capsys.readouterr()
                assert "The Last Horizon" in captured.out
        finally:
            os.unlink(idea_path)

    def test_cli_save_to_file(self, capsys):
        """Test saving output to a file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            with patch("beatsheet_generator.cli.BeatSheetService") as MockService:
                mock_instance = MagicMock()
                mock_instance.generate.return_value = {
                    "beat_sheet": _mock_beat_sheet(),
                    "beat_sheet_json": json.dumps({"beats": []}),
                    "beat_sheet_dict": {"beats": []},
                    "output_path": None,
                    "title": "Test",
                    "genre": "Action",
                    "num_beats": 15,
                }
                mock_instance.save_to_file.return_value = output_path
                MockService.return_value = mock_instance

                main(["--title", "Test", "--genre", "Action", "--logline", "A story.", "--output", output_path])

                mock_instance.save_to_file.assert_called_once_with(output_path)
                captured = capsys.readouterr()
                assert "Saved to" in captured.err
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_cli_missing_logline_error(self, capsys):
        """Test error when logline is missing."""
        with patch("beatsheet_generator.cli.BeatSheetService") as MockService:
            mock_instance = MagicMock()
            mock_instance.generate.side_effect = ValueError("Logline is required to generate a beat sheet.")
            MockService.return_value = mock_instance

            with pytest.raises(SystemExit) as exc_info:
                main(["--title", "Test", "--genre", "Action", "--logline", ""])

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Logline is required" in captured.err

    def test_cli_default_format_is_text(self, capsys):
        """Test that default format is text."""
        with patch("beatsheet_generator.cli.BeatSheetService") as MockService:
            mock_instance = MagicMock()
            mock_instance.generate.return_value = {
                "beat_sheet": _mock_beat_sheet(),
                "beat_sheet_json": json.dumps({"beats": []}),
                "beat_sheet_dict": {"beats": [{"beat_number": 1, "beat_name": "Opening Image", "summary": "Start", "phase": "setup", "characters_involved": []}]},
                "output_path": None,
                "title": "Test",
                "genre": "Action",
                "num_beats": 15,
            }
            MockService.return_value = mock_instance

            main(["--title", "Test", "--genre", "Action", "--logline", "A story."])

            captured = capsys.readouterr()
            assert "Test" in captured.out
            assert "Opening Image" in captured.out
