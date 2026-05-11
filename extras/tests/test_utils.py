"""Tests for ai_movie_gen_suite utils module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_movie_gen_suite.models import Project
from ai_movie_gen_suite.utils import (
    load_json,
    save_json,
    load_jsonl,
    save_jsonl,
    load_yaml,
    save_yaml,
    load_project,
    save_project,
)


class TestLoadJson:
    def test_load_json_valid_file(self, tmp_path):
        data_file = tmp_path / "data.json"
        data_file.write_text('{"key": "value"}')

        data = load_json(str(data_file))
        assert data == {"key": "value"}

    def test_load_json_nonexistent_file(self, tmp_path):
        data_file = tmp_path / "nonexistent.json"
        data = load_json(str(data_file))
        assert data == {}

    def test_load_json_invalid_json(self, tmp_path):
        data_file = tmp_path / "invalid.json"
        data_file.write_text("not valid json")

        with pytest.raises(ValueError):
            load_json(str(data_file))

    def test_load_json_empty_file(self, tmp_path):
        data_file = tmp_path / "empty.json"
        data_file.write_text("")

        data = load_json(str(data_file))
        assert data == {}


class TestSaveJson:
    def test_save_json_creates_file(self, tmp_path):
        data_file = tmp_path / "data.json"
        save_json({"key": "value"}, str(data_file))

        assert data_file.exists()

    def test_save_json_writes_correct_content(self, tmp_path):
        data_file = tmp_path / "data.json"
        save_json({"key": "value"}, str(data_file))

        content = json.loads(data_file.read_text())
        assert content == {"key": "value"}

    def test_save_json_creates_parent_directory(self, tmp_path):
        data_file = tmp_path / "subdir" / "data.json"
        save_json({"key": "value"}, str(data_file))

        assert data_file.exists()

    def test_save_json_overwrites_existing(self, tmp_path):
        data_file = tmp_path / "data.json"
        save_json({"key": "value1"}, str(data_file))
        save_json({"key": "value2"}, str(data_file))

        content = json.loads(data_file.read_text())
        assert content == {"key": "value2"}


class TestLoadJsonl:
    def test_load_jsonl_valid_file(self, tmp_path):
        data_file = tmp_path / "data.jsonl"
        data_file.write_text('{"key": "value1"}\n{"key": "value2"}\n')

        data = load_jsonl(str(data_file))
        assert len(data) == 2
        assert data[0] == {"key": "value1"}
        assert data[1] == {"key": "value2"}

    def test_load_jsonl_nonexistent_file(self, tmp_path):
        data_file = tmp_path / "nonexistent.jsonl"
        data = load_jsonl(str(data_file))
        assert data == []

    def test_load_jsonl_invalid_json(self, tmp_path):
        data_file = tmp_path / "invalid.jsonl"
        data_file.write_text('{"key": "value1"}\nnot valid json\n')

        with pytest.raises(ValueError):
            load_jsonl(str(data_file))

    def test_load_jsonl_empty_file(self, tmp_path):
        data_file = tmp_path / "empty.jsonl"
        data_file.write_text("")

        data = load_jsonl(str(data_file))
        assert data == []


class TestSaveJsonl:
    def test_save_jsonl_creates_file(self, tmp_path):
        data_file = tmp_path / "data.jsonl"
        save_jsonl([{"key": "value1"}, {"key": "value2"}], str(data_file))

        assert data_file.exists()

    def test_save_jsonl_writes_correct_content(self, tmp_path):
        data_file = tmp_path / "data.jsonl"
        save_jsonl([{"key": "value1"}, {"key": "value2"}], str(data_file))

        lines = data_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"key": "value1"}
        assert json.loads(lines[1]) == {"key": "value2"}

    def test_save_jsonl_creates_parent_directory(self, tmp_path):
        data_file = tmp_path / "subdir" / "data.jsonl"
        save_jsonl([{"key": "value"}], str(data_file))

        assert data_file.exists()

    def test_save_jsonl_overwrites_existing(self, tmp_path):
        data_file = tmp_path / "data.jsonl"
        save_jsonl([{"key": "value1"}], str(data_file))
        save_jsonl([{"key": "value2"}], str(data_file))

        lines = data_file.read_text().strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0]) == {"key": "value2"}


class TestLoadYaml:
    def test_load_yaml_valid_file(self, tmp_path):
        data_file = tmp_path / "data.yaml"
        data_file.write_text("key: value\n")

        data = load_yaml(str(data_file))
        assert data == {"key": "value"}

    def test_load_yaml_nonexistent_file(self, tmp_path):
        data_file = tmp_path / "nonexistent.yaml"
        data = load_yaml(str(data_file))
        assert data == {}

    def test_load_yaml_invalid_yaml(self, tmp_path):
        data_file = tmp_path / "invalid.yaml"
        data_file.write_text(": invalid: yaml: [")

        with pytest.raises(ValueError):
            load_yaml(str(data_file))

    def test_load_yaml_empty_file(self, tmp_path):
        data_file = tmp_path / "empty.yaml"
        data_file.write_text("")

        data = load_yaml(str(data_file))
        assert data == {}


class TestSaveYaml:
    def test_save_yaml_creates_file(self, tmp_path):
        data_file = tmp_path / "data.yaml"
        save_yaml({"key": "value"}, str(data_file))

        assert data_file.exists()

    def test_save_yaml_writes_correct_content(self, tmp_path):
        data_file = tmp_path / "data.yaml"
        save_yaml({"key": "value"}, str(data_file))

        content = data_file.read_text()
        assert "key: value" in content

    def test_save_yaml_creates_parent_directory(self, tmp_path):
        data_file = tmp_path / "subdir" / "data.yaml"
        save_yaml({"key": "value"}, str(data_file))

        assert data_file.exists()

    def test_save_yaml_overwrites_existing(self, tmp_path):
        data_file = tmp_path / "data.yaml"
        save_yaml({"key": "value1"}, str(data_file))
        save_yaml({"key": "value2"}, str(data_file))

        content = data_file.read_text()
        assert "key: value2" in content


class TestLoadProject:
    @patch("ai_movie_gen_suite.utils.load_json")
    def test_load_project_from_file(self, mock_load_json, tmp_path):
        mock_load_json.return_value = {
            "title": "Test Movie",
            "logline": "A test logline",
            "genre": "drama",
            "tone": "dark",
            "project_id": "test-id",
        }

        project, project_dir = load_project(str(tmp_path))

        assert project.title == "Test Movie"
        assert project.logline == "A test logline"
        assert project.genre == "drama"
        assert project.tone == "dark"
        assert project.project_id == "test-id"
        assert project_dir == tmp_path

    @patch("ai_movie_gen_suite.utils.load_json")
    def test_load_project_nonexistent_file(self, mock_load_json, tmp_path):
        mock_load_json.return_value = {}

        project, project_dir = load_project(str(tmp_path))

        assert project.title == ""
        assert project.logline == ""
        assert project.genre == ""
        assert project.tone == ""
        assert project.project_id == ""
        assert project_dir == tmp_path


class TestSaveProject:
    @patch("ai_movie_gen_suite.utils.save_json")
    def test_save_project(self, mock_save_json, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        save_project(project, str(tmp_path))

        mock_save_json.assert_called_once()
        call_args = mock_save_json.call_args
        assert call_args[0][0]["title"] == "Test Movie"
        assert call_args[0][0]["logline"] == "A test logline"
        assert call_args[0][0]["genre"] == "drama"
        assert call_args[0][0]["tone"] == "dark"
        assert call_args[0][0]["project_id"] == "test-id"
        assert call_args[0][1] == str(tmp_path / "project.json")
