"""Tests for ai_movie_gen_suite screenplay_writer module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_movie_gen_suite.models import (
    DialogueLine,
    Project,
    Scene,
    Script,
)
from ai_movie_gen_suite.screenplay_writer import (
    save_fdx,
    save_screenplay_text,
)


class TestSaveFdx:
    def test_save_fdx_basic(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            script=Script(
                logline="A test logline",
                scenes=[
                    Scene(
                        scene_id="1",
                        scene_heading="INT. ROOM - DAY",
                        action="Action here.",
                        characters_present=["Hero"],
                        dialogue_lines=[],
                    )
                ],
            ),
        )
        output_path = tmp_path / "output.fdx"
        save_fdx(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Test Movie" in content
        assert "INT. ROOM - DAY" in content
        assert "Action here." in content

    def test_save_fdx_with_dialogue(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            script=Script(
                logline="A test logline",
                scenes=[
                    Scene(
                        scene_id="1",
                        scene_heading="INT. ROOM - DAY",
                        action="Action.",
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
            ),
        )
        output_path = tmp_path / "output.fdx"
        save_fdx(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Hero" in content
        assert "Hello!" in content

    def test_save_fdx_creates_parent_directory(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            script=Script(
                logline="A test logline",
                scenes=[],
            ),
        )
        output_path = tmp_path / "subdir" / "output.fdx"
        save_fdx(project, output_path)

        assert output_path.exists()

    def test_save_fdx_empty_script(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            script=Script(
                logline="A test logline",
                scenes=[],
            ),
        )
        output_path = tmp_path / "output.fdx"
        save_fdx(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Test Movie" in content

    def test_save_fdx_multiple_scenes(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            script=Script(
                logline="A test logline",
                scenes=[
                    Scene(
                        scene_id="1",
                        scene_heading="INT. ROOM - DAY",
                        action="Action 1.",
                        characters_present=["Hero"],
                        dialogue_lines=[],
                    ),
                    Scene(
                        scene_id="2",
                        scene_heading="EXT. PARK - NIGHT",
                        action="Action 2.",
                        characters_present=["Hero", "Villain"],
                        dialogue_lines=[],
                    ),
                ],
            ),
        )
        output_path = tmp_path / "output.fdx"
        save_fdx(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "INT. ROOM - DAY" in content
        assert "EXT. PARK - NIGHT" in content
        assert "Action 1." in content
        assert "Action 2." in content


class TestSaveScreenplayText:
    def test_save_screenplay_text_basic(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
            script=Script(
                logline="A test logline",
                scenes=[
                    Scene(
                        scene_id="1",
                        scene_heading="INT. ROOM - DAY",
                        action="Action here.",
                        characters_present=["Hero"],
                        dialogue_lines=[],
                    )
                ],
            ),
        )
        output_path = tmp_path / "output.txt"
        save_screenplay_text(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Test Movie" in content
        assert "INT. ROOM - DAY" in content
        assert "Action here." in content

    def test_save_screenplay_text_with_dialogue(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            script=Script(
                logline="A test logline",
                scenes=[
                    Scene(
                        scene_id="1",
                        scene_heading="INT. ROOM - DAY",
                        action="Action.",
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
            ),
        )
        output_path = tmp_path / "output.txt"
        save_screenplay_text(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Hero" in content
        assert "Hello!" in content

    def test_save_screenplay_text_creates_parent_directory(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            script=Script(
                logline="A test logline",
                scenes=[],
            ),
        )
        output_path = tmp_path / "subdir" / "output.txt"
        save_screenplay_text(project, output_path)

        assert output_path.exists()

    def test_save_screenplay_text_empty_script(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            script=Script(
                logline="A test logline",
                scenes=[],
            ),
        )
        output_path = tmp_path / "output.txt"
        save_screenplay_text(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Test Movie" in content

    def test_save_screenplay_text_multiple_scenes(self, tmp_path):
        project = Project(
            title="Test Movie",
            logline="A test logline",
            script=Script(
                logline="A test logline",
                scenes=[
                    Scene(
                        scene_id="1",
                        scene_heading="INT. ROOM - DAY",
                        action="Action 1.",
                        characters_present=["Hero"],
                        dialogue_lines=[],
                    ),
                    Scene(
                        scene_id="2",
                        scene_heading="EXT. PARK - NIGHT",
                        action="Action 2.",
                        characters_present=["Hero", "Villain"],
                        dialogue_lines=[],
                    ),
                ],
            ),
        )
        output_path = tmp_path / "output.txt"
        save_screenplay_text(project, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "INT. ROOM - DAY" in content
        assert "EXT. PARK - NIGHT" in content
        assert "Action 1." in content
        assert "Action 2." in content
