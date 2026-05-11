"""Tests for ai_movie_gen_suite CLI module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from ai_movie_gen_suite.cli import app
from ai_movie_gen_suite.models import Beat, BeatSheet, Character, CharacterRegistry, Project, Scene, Script


class TestCLIInit:
    @patch("ai_movie_gen_suite.cli.create_project")
    @patch("ai_movie_gen_suite.cli.save_project")
    def test_init_creates_project(self, mock_save, mock_create, tmp_path):
        mock_create.return_value = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        runner = CliRunner()
        result = runner.invoke(app, ["init", str(tmp_path), "--title", "Test Movie", "--logline", "A test logline", "--genre", "drama", "--tone", "dark"])
        assert result.exit_code == 0
        mock_create.assert_called_once()
        mock_save.assert_called_once()

    @patch("ai_movie_gen_suite.cli.create_project")
    @patch("ai_movie_gen_suite.cli.save_project")
    def test_init_with_all_options(self, mock_save, mock_create, tmp_path):
        mock_create.return_value = Project(
            title="Test Movie",
            logline="A test logline",
            genre="sci-fi",
            tone="dark",
            project_id="test-id",
        )
        runner = CliRunner()
        result = runner.invoke(app, [
            "init",
            str(tmp_path),
            "--title", "Test Movie",
            "--logline", "A test logline",
            "--genre", "sci-fi",
            "--tone", "dark",
            "--output-format", "fdx",
        ])
        assert result.exit_code == 0

    @patch("ai_movie_gen_suite.cli.create_project")
    @patch("ai_movie_gen_suite.cli.save_project")
    def test_init_with_output_format(self, mock_save, mock_create, tmp_path):
        mock_create.return_value = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        runner = CliRunner()
        result = runner.invoke(app, [
            "init",
            str(tmp_path),
            "--title", "Test Movie",
            "--logline", "A test logline",
            "--output-format", "fdx",
        ])
        assert result.exit_code == 0


class TestCLIPipeline:
    @patch("ai_movie_gen_suite.cli.run_full_pipeline")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_pipeline_runs_full_pipeline(self, mock_load, mock_pipeline, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)
        mock_pipeline.return_value = {"beats": tmp_path / "beats.json"}

        runner = CliRunner()
        result = runner.invoke(app, ["pipeline", str(tmp_path)])
        assert result.exit_code == 0
        mock_pipeline.assert_called_once()

    @patch("ai_movie_gen_suite.cli.run_full_pipeline")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_pipeline_with_llm_config(self, mock_load, mock_pipeline, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)
        mock_pipeline.return_value = {"beats": tmp_path / "beats.json"}

        runner = CliRunner()
        result = runner.invoke(app, [
            "pipeline",
            str(tmp_path),
            "--llm-provider", "anthropic",
            "--llm-model", "claude-3",
        ])
        assert result.exit_code == 0

    @patch("ai_movie_gen_suite.cli.run_full_pipeline")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_pipeline_with_llm_config_from_env(self, mock_load, mock_pipeline, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)
        mock_pipeline.return_value = {"beats": tmp_path / "beats.json"}

        runner = CliRunner()
        result = runner.invoke(app, [
            "pipeline",
            str(tmp_path),
            "--llm-provider", "anthropic",
            "--llm-model", "claude-3",
            "--llm-config", str(tmp_path / "config.json"),
        ])
        assert result.exit_code == 0


class TestCLIRegenerate:
    @patch("ai_movie_gen_suite.cli.regenerate_downstream")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_regenerate_from_beats(self, mock_load, mock_regenerate, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)
        mock_regenerate.return_value = {"characters": tmp_path / "characters.json"}

        runner = CliRunner()
        result = runner.invoke(app, ["regenerate", str(tmp_path), "beats"])
        assert result.exit_code == 0
        mock_regenerate.assert_called_once()

    @patch("ai_movie_gen_suite.cli.regenerate_downstream")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_regenerate_from_characters(self, mock_load, mock_regenerate, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)
        mock_regenerate.return_value = {"script": tmp_path / "script.json"}

        runner = CliRunner()
        result = runner.invoke(app, ["regenerate", str(tmp_path), "characters"])
        assert result.exit_code == 0

    @patch("ai_movie_gen_suite.cli.regenerate_downstream")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_regenerate_from_script(self, mock_load, mock_regenerate, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)
        mock_regenerate.return_value = {"scenes": tmp_path / "scenes"}

        runner = CliRunner()
        result = runner.invoke(app, ["regenerate", str(tmp_path), "script"])
        assert result.exit_code == 0

    @patch("ai_movie_gen_suite.cli.regenerate_downstream")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_regenerate_from_scenes(self, mock_load, mock_regenerate, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)
        mock_regenerate.return_value = {}

        runner = CliRunner()
        result = runner.invoke(app, ["regenerate", str(tmp_path), "scenes"])
        assert result.exit_code == 0

    @patch("ai_movie_gen_suite.cli.regenerate_downstream")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_regenerate_invalid_element(self, mock_load, mock_regenerate, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)

        runner = CliRunner()
        result = runner.invoke(app, ["regenerate", str(tmp_path), "invalid"])
        assert result.exit_code != 0


class TestCLIExport:
    @patch("ai_movie_gen_suite.cli.save_screenplay_text")
    @patch("ai_movie_gen_suite.cli.save_fdx")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_export_fdx(self, mock_load, mock_save_fdx, mock_save_text, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
            script=Script(
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
            ),
        )
        mock_load.return_value = (project, tmp_path)

        runner = CliRunner()
        result = runner.invoke(app, ["export", str(tmp_path), "fdx", str(tmp_path / "output.fdx")])
        assert result.exit_code == 0
        mock_save_fdx.assert_called_once()

    @patch("ai_movie_gen_suite.cli.save_screenplay_text")
    @patch("ai_movie_gen_suite.cli.save_fdx")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_export_text(self, mock_load, mock_save_fdx, mock_save_text, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
            script=Script(
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
            ),
        )
        mock_load.return_value = (project, tmp_path)

        runner = CliRunner()
        result = runner.invoke(app, ["export", str(tmp_path), "text", str(tmp_path / "output.txt")])
        assert result.exit_code == 0
        mock_save_text.assert_called_once()

    @patch("ai_movie_gen_suite.cli.save_screenplay_text")
    @patch("ai_movie_gen_suite.cli.save_fdx")
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_export_invalid_format(self, mock_load, mock_save_fdx, mock_save_text, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)

        runner = CliRunner()
        result = runner.invoke(app, ["export", str(tmp_path), "invalid", str(tmp_path / "output.txt")])
        assert result.exit_code != 0


class TestCLIStatus:
    @patch("ai_movie_gen_suite.cli.load_project")
    def test_status_with_all_data(self, mock_load, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
            beats=BeatSheet(beats=[Beat(id="1", act=1, description="Beat 1")]),
            characters=CharacterRegistry(characters=[Character(id="char1", name="Hero", description="Protagonist")]),
            script=Script(
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
            ),
        )
        mock_load.return_value = (project, tmp_path)

        runner = CliRunner()
        result = runner.invoke(app, ["status", str(tmp_path)])
        assert result.exit_code == 0
        assert "beats" in result.output
        assert "characters" in result.output
        assert "scenes" in result.output

    @patch("ai_movie_gen_suite.cli.load_project")
    def test_status_with_no_data(self, mock_load, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
        )
        mock_load.return_value = (project, tmp_path)

        runner = CliRunner()
        result = runner.invoke(app, ["status", str(tmp_path)])
        assert result.exit_code == 0
        assert "beats" in result.output
        assert "characters" in result.output
        assert "scenes" in result.output

    @patch("ai_movie_gen_suite.cli.load_project")
    def test_status_with_partial_data(self, mock_load, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            project_id="test-id",
            beats=BeatSheet(beats=[Beat(id="1", act=1, description="Beat 1")]),
        )
        mock_load.return_value = (project, tmp_path)

        runner = CliRunner()
        result = runner.invoke(app, ["status", str(tmp_path)])
        assert result.exit_code == 0
        assert "beats" in result.output
        assert "characters" in result.output
        assert "scenes" in result.output


class TestCLIHelp:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "pipeline" in result.output
        assert "regenerate" in result.output
        assert "export" in result.output
        assert "status" in result.output

    def test_init_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--title" in result.output
        assert "--logline" in result.output
        assert "--genre" in result.output
        assert "--tone" in result.output

    def test_pipeline_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["pipeline", "--help"])
        assert result.exit_code == 0
        assert "--llm-provider" in result.output
        assert "--llm-model" in result.output

    def test_regenerate_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["regenerate", "--help"])
        assert result.exit_code == 0
        assert "ELEMENT" in result.output
        assert "beats" in result.output
        assert "characters" in result.output
        assert "script" in result.output
        assert "scenes" in result.output

    def test_export_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "FORMAT" in result.output
        assert "fdx" in result.output
        assert "text" in result.output
