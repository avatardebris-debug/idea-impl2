"""Tests for ai_movie_gen_suite project_manager module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_movie_gen_suite.config import AppConfig, LLMConfig
from ai_movie_gen_suite.models import (
    Beat,
    BeatSheet,
    Character,
    CharacterRegistry,
    DialogueLine,
    Project,
    Scene,
    Script,
)
from ai_movie_gen_suite.project_manager import (
    create_project,
    load_project,
    save_project,
    run_full_pipeline,
    regenerate_downstream,
)


class TestCreateProject:
    def test_create_project_defaults(self):
        p = create_project(title="Test", logline="A test logline")
        assert p.title == "Test"
        assert p.logline == "A test logline"
        assert p.genre == "drama"
        assert p.tone == ""
        assert p.project_id is not None
        assert p.beats is None
        assert p.characters is None
        assert p.script is None

    def test_create_project_with_genre_tone(self):
        p = create_project(title="Test", logline="A test logline", genre="sci-fi", tone="dark")
        assert p.genre == "sci-fi"
        assert p.tone == "dark"

    def test_create_project_id_uniqueness(self):
        p1 = create_project(title="Test1", logline="Logline1")
        p2 = create_project(title="Test2", logline="Logline2")
        assert p1.project_id != p2.project_id


class TestSaveLoadProject:
    def test_save_and_load_project(self, tmp_path):
        project = create_project(title="Test", logline="A test logline", genre="sci-fi", tone="dark")
        project.beats = BeatSheet(
            beats=[
                Beat(id="1", act=1, description="Start"),
                Beat(id="2", act=1, description="Middle"),
            ]
        )
        project.characters = CharacterRegistry(
            characters=[
                Character(id="char1", name="Hero", description="The protagonist"),
            ]
        )

        save_project(project, tmp_path)

        # Verify files exist
        assert (tmp_path / "project.json").exists()
        assert (tmp_path / "beats.json").exists()
        assert (tmp_path / "characters.json").exists()

        # Load and verify
        loaded_project, _ = load_project(tmp_path)
        assert loaded_project.title == "Test"
        assert loaded_project.logline == "A test logline"
        assert loaded_project.genre == "sci-fi"
        assert loaded_project.tone == "dark"
        assert loaded_project.beats is not None
        assert len(loaded_project.beats.beats) == 2
        assert loaded_project.characters is not None
        assert len(loaded_project.characters.characters) == 1

    def test_save_and_load_with_script(self, tmp_path):
        project = create_project(title="Test", logline="A test logline")
        project.script = Script(
            logline="A test logline",
            scenes=[
                Scene(
                    scene_id="1",
                    scene_heading="INT. ROOM - DAY",
                    action="Action here.",
                    characters_present=["Hero"],
                    dialogue_lines=[
                        DialogueLine(
                            character_id="char1",
                            character_name="Hero",
                            text="Hello!",
                            parenthetical="smiling",
                        )
                    ],
                )
            ],
        )

        save_project(project, tmp_path)
        loaded_project, _ = load_project(tmp_path)
        assert loaded_project.script is not None
        assert len(loaded_project.script.scenes) == 1
        assert loaded_project.script.scenes[0].action == "Action here."

    def test_load_project_missing_files(self, tmp_path):
        # Create empty directory
        project, _ = load_project(tmp_path)
        assert project.title == "Untitled"
        assert project.beats is None
        assert project.characters is None
        assert project.script is None

    def test_load_project_partial_files(self, tmp_path):
        # Save only beats
        project = create_project(title="Test", logline="A test logline")
        project.beats = BeatSheet(beats=[Beat(id="1", act=1, description="Start")])
        save_project(project, tmp_path)

        loaded_project, _ = load_project(tmp_path)
        assert loaded_project.beats is not None
        assert loaded_project.characters is None
        assert loaded_project.script is None

    def test_save_project_creates_subdirectories(self, tmp_path):
        project = create_project(title="Test", logline="A test logline")
        save_project(project, tmp_path)
        assert (tmp_path / "scenes").is_dir()

    def test_save_project_overwrites_existing(self, tmp_path):
        project1 = create_project(title="Test", logline="Logline1")
        save_project(project1, tmp_path)

        project2 = create_project(title="Test2", logline="Logline2")
        save_project(project2, tmp_path)

        loaded_project, _ = load_project(tmp_path)
        assert loaded_project.title == "Test2"
        assert loaded_project.logline == "Logline2"


class TestRunFullPipeline:
    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_run_full_pipeline_all_stages(self, mock_llm, tmp_path):
        mock_llm.side_effect = [
            {"beats": [{"id": "1", "act": 1, "description": "Act 1 beat"}]},
            {"characters": [{"id": "char1", "name": "Hero", "description": "Protagonist"}]},
            {
                "scenes": [
                    {
                        "scene_id": "1",
                        "scene_heading": "INT. ROOM - DAY",
                        "action": "Action.",
                        "characters_present": ["Hero"],
                        "dialogue_lines": [
                            {
                                "character_id": "char1",
                                "character_name": "Hero",
                                "text": "Hello",
                                "parenthetical": None,
                            }
                        ],
                    }
                ]
            },
        ]

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = create_project(title="Test", logline="A test logline", genre="drama", tone="dark")

        paths = run_full_pipeline(project, config, tmp_path)

        assert "beats" in paths
        assert "characters" in paths
        assert "script" in paths
        assert "scenes" in paths

        # Verify project state
        assert project.beats is not None
        assert project.characters is not None
        assert project.script is not None
        assert len(project.script.scenes) == 1

        # Verify files saved
        assert (tmp_path / "beats.json").exists()
        assert (tmp_path / "characters.json").exists()
        assert (tmp_path / "script.json").exists()
        assert (tmp_path / "scenes").is_dir()

    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_run_full_pipeline_partial_existing(self, mock_llm, tmp_path):
        """Pipeline should skip stages that already have data."""
        project = create_project(title="Test", logline="A test logline")
        project.beats = BeatSheet(beats=[Beat(id="1", act=1, description="Existing beat")])
        save_project(project, tmp_path)

        mock_llm.side_effect = [
            {"characters": [{"id": "char1", "name": "Hero", "description": "Protagonist"}]},
            {
                "scenes": [
                    {
                        "scene_id": "1",
                        "scene_heading": "INT. ROOM - DAY",
                        "action": "Action.",
                        "characters_present": ["Hero"],
                        "dialogue_lines": [],
                    }
                ]
            },
        ]

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        paths = run_full_pipeline(project, config, tmp_path)

        # Beats should not be regenerated
        assert mock_llm.call_count == 2  # Only characters and script
        assert project.beats is not None
        assert len(project.beats.beats) == 1

    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_run_full_pipeline_empty_beats(self, mock_llm, tmp_path):
        """Pipeline should handle empty beat sheet."""
        mock_llm.side_effect = [
            {"beats": []},
            {"characters": []},
            {"scenes": []},
        ]

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = create_project(title="Test", logline="A test logline")

        paths = run_full_pipeline(project, config, tmp_path)
        assert project.beats is not None
        assert len(project.beats.beats) == 0

    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_run_full_pipeline_handles_llm_error(self, mock_llm, tmp_path):
        """Pipeline should handle LLM errors gracefully."""
        mock_llm.side_effect = RuntimeError("API error")

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = create_project(title="Test", logline="A test logline")

        with pytest.raises(RuntimeError, match="API error"):
            run_full_pipeline(project, config, tmp_path)


class TestRegenerateDownstream:
    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_regenerate_from_beats(self, mock_llm, tmp_path):
        """Regenerating from beats should regenerate characters, script, and scenes."""
        # Set up initial project with beats
        project = create_project(title="Test", logline="A test logline")
        project.beats = BeatSheet(beats=[Beat(id="1", act=1, description="Beat 1")])
        save_project(project, tmp_path)

        mock_llm.side_effect = [
            {"characters": [{"id": "char1", "name": "Hero", "description": "Protagonist"}]},
            {
                "scenes": [
                    {
                        "scene_id": "1",
                        "scene_heading": "INT. ROOM - DAY",
                        "action": "Action.",
                        "characters_present": ["Hero"],
                        "dialogue_lines": [],
                    }
                ]
            },
        ]

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        paths = regenerate_downstream(project, config, tmp_path, "beats")

        assert "characters" in paths
        assert "script" in paths
        assert "scenes" in paths
        assert project.characters is not None
        assert project.script is not None

    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_regenerate_from_characters(self, mock_llm, tmp_path):
        """Regenerating from characters should regenerate script and scenes."""
        project = create_project(title="Test", logline="A test logline")
        project.beats = BeatSheet(beats=[Beat(id="1", act=1, description="Beat 1")])
        project.characters = CharacterRegistry(characters=[Character(id="char1", name="Hero", description="Protagonist")])
        save_project(project, tmp_path)

        mock_llm.side_effect = [
            {
                "scenes": [
                    {
                        "scene_id": "1",
                        "scene_heading": "INT. ROOM - DAY",
                        "action": "Action.",
                        "characters_present": ["Hero"],
                        "dialogue_lines": [],
                    }
                ]
            },
        ]

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        paths = regenerate_downstream(project, config, tmp_path, "characters")

        assert "script" in paths
        assert "scenes" in paths
        assert project.script is not None

    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_regenerate_from_script(self, mock_llm, tmp_path):
        """Regenerating from script should only regenerate scenes."""
        project = create_project(title="Test", logline="A test logline")
        project.beats = BeatSheet(beats=[Beat(id="1", act=1, description="Beat 1")])
        project.characters = CharacterRegistry(characters=[Character(id="char1", name="Hero", description="Protagonist")])
        project.script = Script(
            logline="A test logline",
            scenes=[
                Scene(
                    scene_id="1",
                    scene_heading="INT. ROOM - DAY",
                    action="Action.",
                    characters_present=["Hero"],
                    dialogue_lines=[],
                )
            ],
        )
        save_project(project, tmp_path)

        mock_llm.side_effect = [
            {
                "scenes": [
                    {
                        "scene_id": "1",
                        "scene_heading": "INT. ROOM - DAY",
                        "action": "Updated action.",
                        "characters_present": ["Hero"],
                        "dialogue_lines": [],
                    }
                ]
            },
        ]

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        paths = regenerate_downstream(project, config, tmp_path, "script")

        assert "scenes" in paths
        assert project.script.scenes[0].action == "Updated action."

    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_regenerate_from_scenes(self, mock_llm, tmp_path):
        """Regenerating from scenes should do nothing."""
        project = create_project(title="Test", logline="A test logline")
        save_project(project, tmp_path)

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        paths = regenerate_downstream(project, config, tmp_path, "scenes")

        assert paths == {}
        mock_llm.assert_not_called()

    def test_regenerate_downstream_invalid_element(self, tmp_path):
        project = create_project(title="Test", logline="A test logline")
        save_project(project, tmp_path)

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        with pytest.raises(ValueError, match="Unknown element: invalid"):
            regenerate_downstream(project, config, tmp_path, "invalid")

    @patch("ai_movie_gen_suite.project_manager.call_llm_with_template")
    def test_regenerate_downstream_from_characters_no_beats(self, mock_llm, tmp_path):
        """Regenerating from characters without beats should still work (characters don't depend on beats)."""
        project = create_project(title="Test", logline="A test logline")
        save_project(project, tmp_path)

        mock_llm.side_effect = [
            {"characters": [{"id": "char1", "name": "Hero", "description": "Protagonist"}]},
            {
                "scenes": [
                    {
                        "scene_id": "1",
                        "scene_heading": "INT. ROOM - DAY",
                        "action": "Action.",
                        "characters_present": ["Hero"],
                        "dialogue_lines": [],
                    }
                ]
            },
        ]

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        paths = regenerate_downstream(project, config, tmp_path, "characters")

        assert "characters" in paths
        assert "script" in paths
