"""Tests for multi-scene recipe assembly (Phase 2)."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the project root is on the path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from video_recipe_mu.multi_scene_assembler import (
    MultiSceneRecipe,
    _build_object_map,
    _merge_steps_across_scenes,
    _resolve_cross_scene_preconditions,
    assemble_multi_scene_recipe,
    load_multi_scene_json,
    load_multi_scene_markdown,
    multi_scene_recipe_to_json,
)
from video_recipe_mu.recipe_parser import SceneInfo
from video_recipe_mu.schema import RobotRecipeStep


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_scenes():
    """Create two sample scene descriptions for testing."""
    scene1 = SceneInfo(
        index=0,
        time_range=[0.0, 5.0],
        description="A hand picks up a red cup from the table.",
        visual_elements=["red_cup", "table"],
        camera_notes="Close-up on table surface.",
    )
    scene2 = SceneInfo(
        index=1,
        time_range=[5.0, 10.0],
        description="The hand places the red cup on a shelf.",
        visual_elements=["red_cup", "shelf"],
        camera_notes="Camera pans up to shelf.",
    )
    return [scene1, scene2]


@pytest.fixture
def sample_steps():
    """Create sample robot recipe steps."""
    return [
        {"step": 1, "action": "pick_up", "object": "red_cup", "xyz_delta": {"x": 0.1, "y": 0.0, "z": 0.2}, "duration_s": 1.5, "preconditions": [], "success_state": "red_cup_gripped"},
        {"step": 2, "action": "move_to", "object": "red_cup", "xyz_delta": {"x": 0.0, "y": 0.0, "z": 0.5}, "duration_s": 2.0, "preconditions": ["red_cup_gripped"], "success_state": "red_cup_moved"},
        {"step": 3, "action": "place", "object": "red_cup", "xyz_delta": {"x": 0.0, "y": 0.0, "z": 0.0}, "duration_s": 1.0, "preconditions": ["red_cup_moved"], "success_state": "red_cup_placed"},
    ]


# ── Tests: _build_object_map ────────────────────────────────────────────────

class TestBuildObjectMap:
    def test_shared_object_across_scenes(self, sample_scenes):
        obj_map = _build_object_map(sample_scenes)
        assert "red_cup" in obj_map
        assert obj_map["red_cup"] == [0, 1]

    def test_scene_specific_object(self, sample_scenes):
        obj_map = _build_object_map(sample_scenes)
        assert "table" in obj_map
        assert obj_map["table"] == [0]
        assert "shelf" in obj_map
        assert obj_map["shelf"] == [1]

    def test_empty_scenes(self):
        obj_map = _build_object_map([])
        assert obj_map == {}


# ── Tests: _merge_steps_across_scenes ───────────────────────────────────────

class TestMergeStepsAcrossScenes:
    def test_merge_two_scenes(self, sample_scenes, sample_steps):
        scene_steps = [sample_steps, sample_steps]
        merged, boundaries = _merge_steps_across_scenes(scene_steps, sample_scenes)
        assert len(merged) == 6
        assert boundaries == [3, 6]
        assert merged[0]["step"] == 1
        assert merged[5]["step"] == 6

    def test_merge_single_scene(self, sample_scenes, sample_steps):
        scene_steps = [sample_steps]
        merged, boundaries = _merge_steps_across_scenes(scene_steps, sample_scenes)
        assert len(merged) == 3
        assert boundaries == [3]

    def test_merge_empty_scenes(self):
        merged, boundaries = _merge_steps_across_scenes([], [])
        assert merged == []
        assert boundaries == []


# ── Tests: _resolve_cross_scene_preconditions ───────────────────────────────

class TestResolveCrossScenePreconditions:
    def test_shared_object_tracking(self, sample_scenes, sample_steps):
        shared_objects = {"red_cup": [0, 1]}
        resolved = _resolve_cross_scene_preconditions(sample_steps, sample_scenes, shared_objects)
        assert len(resolved) == len(sample_steps)

    def test_empty_shared_objects(self, sample_scenes, sample_steps):
        resolved = _resolve_cross_scene_preconditions(sample_steps, sample_scenes, {})
        assert resolved == sample_steps


# ── Tests: assemble_multi_scene_recipe ──────────────────────────────────────

class TestAssembleMultiSceneRecipe:
    def test_assemble_with_scenes(self, sample_scenes):
        recipe = assemble_multi_scene_recipe(sample_scenes)
        assert isinstance(recipe, MultiSceneRecipe)
        assert recipe.metadata["num_scenes"] == 2
        assert recipe.metadata["total_steps"] > 0
        assert "red_cup" in recipe.shared_objects

    def test_assemble_empty_scenes(self):
        recipe = assemble_multi_scene_recipe([])
        assert recipe.steps == []
        assert recipe.metadata.get("error") == "no scenes"

    def test_assemble_single_scene(self):
        scene = SceneInfo(
            index=0,
            time_range=[0.0, 5.0],
            description="A hand picks up a red cup.",
            visual_elements=["red_cup"],
            camera_notes="",
        )
        recipe = assemble_multi_scene_recipe([scene])
        assert recipe.metadata["num_scenes"] == 1
        assert recipe.metadata["total_steps"] > 0


# ── Tests: load_multi_scene_json ────────────────────────────────────────────

class TestLoadMultiSceneJson:
    def test_load_json_file(self):
        # The parser expects frame.content_summary and frame.visual_elements
        data = {
            "scenes": [
                {
                    "frame": {
                        "content_summary": "Scene one.",
                        "visual_elements": ["cup"],
                        "camera_notes": "",
                    }
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            tmp_path = f.name
        try:
            scenes = load_multi_scene_json(tmp_path)
            assert len(scenes) == 1
            assert scenes[0].description == "Scene one."
        finally:
            os.unlink(tmp_path)


# ── Tests: load_multi_scene_markdown ────────────────────────────────────────

class TestLoadMultiSceneMarkdown:
    def test_load_markdown_file(self):
        # The parser looks for ## Content Summary and ## Visual Elements headers
        md_content = """## Content Summary
Scene one.

## Visual Elements
cup
table
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(md_content)
            f.flush()
            tmp_path = f.name
        try:
            scenes = load_multi_scene_markdown(tmp_path)
            assert len(scenes) >= 1
            assert scenes[0].description == "Scene one."
        finally:
            os.unlink(tmp_path)


# ── Tests: multi_scene_recipe_to_json ───────────────────────────────────────

class TestMultiSceneRecipeToJson:
    def test_serialize_recipe(self, sample_scenes):
        recipe = assemble_multi_scene_recipe(sample_scenes)
        json_str = multi_scene_recipe_to_json(recipe)
        parsed = json.loads(json_str)
        assert "steps" in parsed
        assert "shared_objects" in parsed
        assert "scene_boundaries" in parsed
        assert "num_scenes" in parsed

    def test_empty_recipe(self):
        recipe = MultiSceneRecipe(scenes=[], steps=[], scene_boundaries=[], shared_objects={})
        json_str = multi_scene_recipe_to_json(recipe)
        parsed = json.loads(json_str)
        assert parsed["total_steps"] == 0
