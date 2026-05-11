"""Tests for ai_movie_gen_suite formatters."""

from ai_movie_gen_suite.formatters.screenplay_formatter import (
    format_screenplay_text,
    format_fdx,
)
from ai_movie_gen_suite.models import DialogueLine, Scene, Script


class TestScreenplayFormatter:
    def test_format_screenplay_text(self):
        scenes = [
            Scene(
                scene_id="SC-001",
                scene_heading="INT. ROOM - DAY",
                action="A person enters.",
                characters_present=["CHAR_1"],
                dialogue_lines=[
                    DialogueLine(character_id="CHAR_1", character_name="Hero", text="Hello there!", parenthetical="smiling"),
                ],
            )
        ]
        script = Script(project_id="P1", logline="Test logline", scenes=scenes)
        text = format_screenplay_text(script)
        assert "INT. ROOM - DAY" in text
        assert "Hero" in text
        assert "Hello there!" in text
        assert "(smiling)" in text

    def test_format_fdx(self):
        scenes = [
            Scene(
                scene_id="SC-001",
                scene_heading="INT. ROOM - DAY",
                action="Action",
                characters_present=["CHAR_1"],
                dialogue_lines=[
                    DialogueLine(character_id="CHAR_1", character_name="Hero", text="Hi"),
                ],
            )
        ]
        script = Script(project_id="P1", logline="Test logline", scenes=scenes)
        fdx = format_fdx(script)
        assert fdx["title"] == "Test logline"
        assert len(fdx["scenes"]) == 1
        assert fdx["scenes"][0]["heading"] == "INT. ROOM - DAY"
        assert len(fdx["scenes"][0]["dialogue"]) == 1
        assert fdx["scenes"][0]["dialogue"][0]["character"] == "Hero"
