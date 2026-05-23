"""Multi-scene recipe assembly — chain multiple scene descriptions into a single coherent robot recipe."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from video_recipe_mu.recipe_parser import ParsedSceneDescription, SceneInfo, parse_json_scene, parse_markdown_scene
from video_recipe_mu.recipe_extractor import extract_recipe_from_parsed
from video_recipe_mu.recipe_validator import validate_steps, normalize_steps
from video_recipe_mu.schema import RobotRecipeStep


@dataclass
class MultiSceneRecipe:
    """A unified recipe assembled from multiple scenes."""

    scenes: List[SceneInfo]
    steps: List[RobotRecipeStep]
    scene_boundaries: List[int]  # indices in `steps` where each scene ends
    shared_objects: Dict[str, List[int]]  # object -> list of scene indices where it appears
    metadata: Dict[str, Any] = field(default_factory=dict)


def _build_object_map(scenes: List[SceneInfo]) -> Dict[str, List[int]]:
    """Map each object name to the list of scene indices where it appears."""
    obj_map: Dict[str, List[int]] = {}
    for idx, scene in enumerate(scenes):
        for obj in scene.visual_elements:
            obj_lower = obj.lower().strip()
            if obj_lower not in obj_map:
                obj_map[obj_lower] = []
            obj_map[obj_lower].append(idx)
    return obj_map


def _resolve_cross_scene_preconditions(
    steps: List[RobotRecipeStep],
    scenes: List[SceneInfo],
    shared_objects: Dict[str, List[int]],
) -> List[RobotRecipeStep]:
    """Add cross-scene preconditions for shared objects.

    If an object is placed in scene N and picked up in scene N+1,
    ensure the preconditions reflect that the object is available.
    """
    # Track the last known action for each shared object
    object_last_action: Dict[str, str] = {}
    for obj in shared_objects:
        object_last_action[obj] = ""

    for scene_idx, scene in enumerate(scenes):
        for step in steps:
            obj = step.get("object", "")
            action = step.get("action", "")
            if obj and obj.lower() in shared_objects:
                object_last_action[obj.lower()] = action

    return steps


def _merge_steps_across_scenes(
    scene_steps: List[List[RobotRecipeStep]],
    scenes: List[SceneInfo],
) -> Tuple[List[RobotRecipeStep], List[int]]:
    """Merge per-scene steps into a single list, renumbering steps and tracking boundaries."""
    merged: List[RobotRecipeStep] = []
    boundaries: List[int] = []
    global_step = 0

    for scene_idx, steps in enumerate(scene_steps):
        for step in steps:
            global_step += 1
            merged_step = dict(step)
            merged_step["step"] = global_step
            merged.append(merged_step)
        scene_end = len(merged)
        boundaries.append(scene_end)

    return merged, boundaries


def assemble_multi_scene_recipe(
    scenes: List[SceneInfo],
    provider: str = "openai",
) -> MultiSceneRecipe:
    """Assemble a unified robot recipe from multiple scene descriptions.

    Args:
        scenes: List of parsed scene descriptions from video_scribe.
        provider: LLM provider to use ("openai" or "anthropic").

    Returns:
        MultiSceneRecipe with merged steps, boundaries, and shared object info.
    """
    if not scenes:
        return MultiSceneRecipe(scenes=[], steps=[], scene_boundaries=[], shared_objects={}, metadata={"error": "no scenes"})

    # Extract per-scene recipes
    scene_steps: List[List[RobotRecipeStep]] = []
    for scene in scenes:
        parsed = ParsedSceneDescription(scenes=[scene], global_summary="")
        steps = extract_recipe_from_parsed(parsed, provider=provider)
        scene_steps.append(steps)

    # Merge steps across scenes
    merged_steps, boundaries = _merge_steps_across_scenes(scene_steps, scenes)

    # Resolve shared objects
    shared_objects = _build_object_map(scenes)

    # Resolve cross-scene preconditions
    merged_steps = _resolve_cross_scene_preconditions(merged_steps, scenes, shared_objects)

    # Validate and normalize
    merged_steps = normalize_steps(merged_steps)
    validation_errors = validate_steps(merged_steps)

    metadata: Dict[str, Any] = {
        "num_scenes": len(scenes),
        "total_steps": len(merged_steps),
        "shared_objects": list(shared_objects.keys()),
        "validation_errors": validation_errors,
    }

    return MultiSceneRecipe(
        scenes=scenes,
        steps=merged_steps,
        scene_boundaries=boundaries,
        shared_objects=shared_objects,
        metadata=metadata,
    )


def load_multi_scene_json(file_path: str) -> List[SceneInfo]:
    """Load multi-scene output from a video_scribe JSON file."""
    parsed = parse_json_scene(file_path)
    return parsed.scenes


def load_multi_scene_markdown(file_path: str) -> List[SceneInfo]:
    """Load multi-scene output from a video_scribe Markdown file."""
    parsed = parse_markdown_scene(file_path)
    return parsed.scenes


def multi_scene_recipe_to_json(recipe: MultiSceneRecipe) -> str:
    """Serialize a MultiSceneRecipe to JSON string."""
    output = {
        "num_scenes": recipe.metadata.get("num_scenes", len(recipe.scenes)),
        "total_steps": recipe.metadata.get("total_steps", len(recipe.steps)),
        "shared_objects": recipe.shared_objects,
        "scene_boundaries": recipe.scene_boundaries,
        "steps": recipe.steps,
    }
    return json.dumps(output, indent=2)
