"""Tests for ai_movie_gen_suite stages module."""

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
from ai_movie_gen_suite.stages import (
    generate_beats,
    generate_characters,
    generate_script,
    generate_scenes,
)


class TestGenerateBeats:
    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_beats_success(self, mock_llm, tmp_path):
        mock_llm.return_value = {
            "beats": [
                {"id": "1", "act": 1, "description": "Act 1 beat"},
                {"id": "2", "act": 2, "description": "Act 2 beat"},
            ]
        }

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline", genre="drama", tone="dark")

        beats = generate_beats(project, config, tmp_path)

        assert beats is not None
        assert len(beats.beats) == 2
        assert beats.beats[0].id == "1"
        assert beats.beats[0].act == 1
        assert beats.beats[0].description == "Act 1 beat"
        assert beats.beats[1].id == "2"
        assert beats.beats[1].act == 2

    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_beats_empty(self, mock_llm, tmp_path):
        mock_llm.return_value = {"beats": []}

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")

        beats = generate_beats(project, config, tmp_path)

        assert beats is not None
        assert len(beats.beats) == 0

    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_beats_error(self, mock_llm, tmp_path):
        mock_llm.side_effect = RuntimeError("API error")

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")

        with pytest.raises(RuntimeError, match="API error"):
            generate_beats(project, config, tmp_path)


class TestGenerateCharacters:
    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_characters_success(self, mock_llm, tmp_path):
        mock_llm.return_value = {
            "characters": [
                {"id": "char1", "name": "Hero", "description": "Protagonist"},
                {"id": "char2", "name": "Villain", "description": "Antagonist"},
            ]
        }

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")

        characters = generate_characters(project, config, tmp_path)

        assert characters is not None
        assert len(characters.characters) == 2
        assert characters.characters[0].id == "char1"
        assert characters.characters[0].name == "Hero"
        assert characters.characters[1].id == "char2"
        assert characters.characters[1].name == "Villain"

    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_characters_empty(self, mock_llm, tmp_path):
        mock_llm.return_value = {"characters": []}

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")

        characters = generate_characters(project, config, tmp_path)

        assert characters is not None
        assert len(characters.characters) == 0

    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_characters_error(self, mock_llm, tmp_path):
        mock_llm.side_effect = RuntimeError("API error")

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")

        with pytest.raises(RuntimeError, match="API error"):
            generate_characters(project, config, tmp_path)


class TestGenerateScript:
    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_script_success(self, mock_llm, tmp_path):
        mock_llm.return_value = {
            "scenes": [
                {
                    "scene_id": "1",
                    "scene_heading": "INT. ROOM - DAY",
                    "action": "Action.",
                    "characters_present": ["Hero"],
                    "dialogue_lines": [],
                }
            ]
        }

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")

        script = generate_script(project, config, tmp_path)

        assert script is not None
        assert script.logline == "A test logline"
        assert len(script.scenes) == 1
        assert script.scenes[0].scene_id == "1"
        assert script.scenes[0].scene_heading == "INT. ROOM - DAY"
        assert script.scenes[0].action == "Action."
        assert script.scenes[0].characters_present == ["Hero"]
        assert script.scenes[0].dialogue_lines == []

    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_script_empty(self, mock_llm, tmp_path):
        mock_llm.return_value = {"scenes": []}

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")

        script = generate_script(project, config, tmp_path)

        assert script is not None
        assert len(script.scenes) == 0

    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_script_error(self, mock_llm, tmp_path):
        mock_llm.side_effect = RuntimeError("API error")

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")

        with pytest.raises(RuntimeError, match="API error"):
            generate_script(project, config, tmp_path)


class TestGenerateScenes:
    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_scenes_success(self, mock_llm, tmp_path):
        mock_llm.return_value = {
            "scenes": [
                {
                    "scene_id": "1",
                    "scene_heading": "INT. ROOM - DAY",
                    "action": "Updated action.",
                    "characters_present": ["Hero"],
                    "dialogue_lines": [],
                }
            ]
        }

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")
        project.script = Script(
            logline="A test logline",
            scenes=[
                Scene(
                    scene_id="1",
                    scene_heading="INT. ROOM - DAY",
                    action="Old action.",
                    characters_present=["Hero"],
                    dialogue_lines=[],
                )
            ],
        )

        script = generate_scenes(project, config, tmp_path)

        assert script is not None
        assert len(script.scenes) == 1
        assert script.scenes[0].scene_id == "1"
        assert script.scenes[0].action == "Updated action."

    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_scenes_empty(self, mock_llm, tmp_path):
        mock_llm.return_value = {"scenes": []}

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")
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

        script = generate_scenes(project, config, tmp_path)

        assert script is not None
        assert len(script.scenes) == 0

    @patch("ai_movie_gen_suite.stages.call_llm_with_template")
    def test_generate_scenes_error(self, mock_llm, tmp_path):
        mock_llm.side_effect = RuntimeError("API error")

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        project = Project(title="Test", logline="A test logline")
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

        with pytest.raises(RuntimeError, match="API error"):
            generate_scenes(project, config, tmp_path)
