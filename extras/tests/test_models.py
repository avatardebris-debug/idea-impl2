"""Tests for ai_movie_gen_suite models."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ai_movie_gen_suite.models import (
    Beat,
    BeatSheet,
    Character,
    CharacterRegistry,
    DialogueLine,
    Project,
    Scene,
    Script,
    SceneDescription,
)


class TestProject:
    def test_create_project(self):
        p = Project(title="Test", logline="A test logline")
        assert p.title == "Test"
        assert p.logline == "A test logline"
        assert p.project_id is not None
        assert p.beats is None
        assert p.characters is None
        assert p.script is None

    def test_project_to_dict(self):
        p = Project(title="Test", logline="A test logline")
        d = p.to_dict()
        assert d["title"] == "Test"
        assert "project_id" in d

    def test_project_from_dict(self):
        d = {"title": "Test", "logline": "A test logline"}
        p = Project(**d)
        assert p.title == "Test"

    def test_project_save_load(self):
        p = Project(title="Test", logline="A test logline")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "project.json"
            path.write_text(json.dumps(p.to_dict(), indent=2))
            loaded = json.loads(path.read_text())
            p2 = Project(**loaded)
            assert p2.title == p.title
            assert p2.logline == p.logline


class TestBeatSheet:
    def test_create_beatsheet(self):
        beats = [
            Beat(beat_number=1, beat_name="opening_image", summary="Open", description="Open desc"),
            Beat(beat_number=2, beat_name="theme_stated", summary="Theme", description="Theme desc"),
        ]
        bs = BeatSheet(project_id="P1", logline="Test logline", beats=beats)
        assert len(bs.beats) == 2
        assert bs.beats[0].beat_number == 1

    def test_beatsheet_to_dict(self):
        beats = [Beat(beat_number=1, beat_name="opening_image", summary="Open", description="Open desc")]
        bs = BeatSheet(project_id="P1", logline="Test logline", beats=beats)
        d = bs.to_dict()
        assert len(d["beats"]) == 1


class TestCharacterRegistry:
    def test_create_registry(self):
        chars = [
            Character(
                id="CHAR_1",
                name="Hero",
                role="protagonist",
                physical_description="Tall, brave",
                personality_traits=["brave", "kind"],
                visual_anchor="tall, brave hero",
                arc_summary="Grows from coward to hero",
            )
        ]
        cr = CharacterRegistry(project_id="P1", characters=chars)
        assert len(cr.characters) == 1
        assert cr.characters[0].name == "Hero"

    def test_registry_to_dict(self):
        chars = [Character(id="CHAR_1", name="Hero", role="protagonist", visual_anchor="hero", arc_summary="arc")]
        cr = CharacterRegistry(project_id="P1", characters=chars)
        d = cr.to_dict()
        assert len(d["characters"]) == 1


class TestScript:
    def test_create_script(self):
        scenes = [
            Scene(
                scene_id="SC-001",
                scene_heading="INT. ROOM - DAY",
                action="Action here",
                characters_present=["CHAR_1"],
                dialogue_lines=[
                    DialogueLine(character_id="CHAR_1", character_name="Hero", text="Hello")
                ],
            )
        ]
        s = Script(project_id="P1", logline="Test logline", scenes=scenes)
        assert len(s.scenes) == 1
        assert s.scenes[0].scene_heading == "INT. ROOM - DAY"

    def test_script_to_dict(self):
        scenes = [Scene(scene_id="SC-001", scene_heading="INT. ROOM - DAY", action="Action", characters_present=["CHAR_1"], dialogue_lines=[])]
        s = Script(project_id="P1", logline="Test logline", scenes=scenes)
        d = s.to_dict()
        assert len(d["scenes"]) == 1


class TestSceneDescription:
    def test_create_description(self):
        desc = SceneDescription(
            scene_id="SC-001",
            setting="A dark room",
            lighting="Dim, blue",
            camera_notes="Wide shot",
            mood="Tense",
            visual_style="Noir",
            action_beats=["Enter hero", "Discover clue"],
        )
        assert desc.scene_id == "SC-001"
        assert desc.mood == "Tense"

    def test_description_to_dict(self):
        desc = SceneDescription(
            scene_id="SC-001",
            setting="A room",
            lighting="Bright",
            camera_notes="Close up",
            mood="Happy",
            visual_style="Bright",
            action_beats=[],
        )
        d = desc.to_dict()
        assert d["scene_id"] == "SC-001"
