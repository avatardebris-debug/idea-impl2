"""Parse video_scribe output (JSON or Markdown) into an intermediate representation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class SceneInfo:
    """Intermediate representation of a single scene."""

    index: int
    time_range: List[float]  # [start_s, end_s]
    description: str
    visual_elements: List[str] = field(default_factory=list)
    camera_notes: str = ""
    lighting_color_notes: str = ""
    content_summary: str = ""


@dataclass
class ParsedSceneDescription:
    """Intermediate representation of parsed video_scribe output."""

    scenes: List[SceneInfo] = field(default_factory=list)
    global_summary: str = ""


def parse_json_scene(json_path: str) -> ParsedSceneDescription:
    """Parse a single-scene video_scribe JSON output.

    Expects a JSON file with structure similar to video_scribe's
    format_single_frame_json() or format_multi_scene_json() output.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    scenes: List[SceneInfo] = []

    # Handle multi-scene JSON (list of scenes)
    if isinstance(data, list):
        for idx, scene_data in enumerate(data):
            scenes.append(_parse_single_scene_json(scene_data, idx))
        return ParsedSceneDescription(scenes=scenes)

    # Handle single-scene JSON (dict with 'scenes' or 'scene' key)
    if isinstance(data, dict):
        scene_list = data.get("scenes", [data.get("scene", data)])
        if isinstance(scene_list, list):
            for idx, scene_data in enumerate(scene_list):
                scenes.append(_parse_single_scene_json(scene_data, idx))
        else:
            scenes.append(_parse_single_scene_json(scene_list, 0))
        return ParsedSceneDescription(scenes=scenes)

    raise ValueError(f"Unexpected JSON structure: {type(data)}")


def _parse_single_scene_json(scene_data: Dict[str, Any], index: int) -> SceneInfo:
    """Parse a single scene from video_scribe JSON."""
    frame_data = scene_data.get("frame", {})
    content_summary = frame_data.get("content_summary", "")
    visual_elements = frame_data.get("visual_elements", [])
    camera_notes = frame_data.get("camera_notes", "")
    lighting_color_notes = frame_data.get("lighting_color_notes", "")

    # Extract time range from scene boundaries if available
    time_range = [0.0, 5.0]  # default
    if "time_range" in scene_data:
        time_range = scene_data["time_range"]
    elif "frame_number" in scene_data:
        # Estimate time range from frame number (assume 30fps, 5s scenes)
        fn = scene_data["frame_number"]
        time_range = [fn / 30.0, (fn + 150) / 30.0]

    return SceneInfo(
        index=index,
        time_range=time_range,
        description=content_summary,
        visual_elements=visual_elements if isinstance(visual_elements, list) else [str(visual_elements)],
        camera_notes=camera_notes,
        lighting_color_notes=lighting_color_notes,
        content_summary=content_summary,
    )


def parse_markdown_scene(md_path: str) -> ParsedSceneDescription:
    """Parse a single-scene video_scribe Markdown output.

    Expects markdown with sections like:
    ## Content Summary
    ## Visual Elements
    ## Camera Notes
    ## Lighting & Color
    """
    with open(md_path, "r") as f:
        content = f.read()

    scenes: List[SceneInfo] = []

    # Split by scene boundaries (## Scene N or similar)
    scene_sections = re.split(r"##\s+Scene\s+\d+", content)

    for idx, section in enumerate(scene_sections):
        if not section.strip():
            continue
        scene = _parse_markdown_section(section, idx)
        if scene:
            scenes.append(scene)

    if not scenes:
        # Try parsing as a single scene without explicit headers
        scene = _parse_markdown_section(content, 0)
        if scene:
            scenes.append(scene)

    # Extract global summary if present
    global_summary = ""
    global_match = re.search(r"##\s+Global\s+Summary\s*\n(.*?)(?=##|\Z)", content, re.DOTALL)
    if global_match:
        global_summary = global_match.group(1).strip()

    return ParsedSceneDescription(scenes=scenes, global_summary=global_summary)


def _parse_markdown_section(section: str, index: int) -> Optional[SceneInfo]:
    """Parse a markdown section into a SceneInfo."""
    content_summary = ""
    visual_elements: List[str] = []
    camera_notes = ""
    lighting_color_notes = ""

    # Extract content summary
    summary_match = re.search(r"##\s*Content\s*Summary\s*\n(.*?)(?=##|\Z)", section, re.DOTALL)
    if summary_match:
        content_summary = summary_match.group(1).strip()

    # Extract visual elements
    elements_match = re.search(r"##\s*Visual\s*Elements\s*\n(.*?)(?=##|\Z)", section, re.DOTALL)
    if elements_match:
        elements_text = elements_match.group(1).strip()
        # Parse bullet points or comma-separated values
        visual_elements = [
            el.strip().lstrip("-*•").strip()
            for el in elements_text.split("\n")
            if el.strip()
        ]
        if not visual_elements and "," in elements_text:
            visual_elements = [el.strip() for el in elements_text.split(",")]

    # Extract camera notes
    camera_match = re.search(r"##\s*Camera\s*(Notes)?\s*\n(.*?)(?=##|\Z)", section, re.DOTALL)
    if camera_match:
        camera_notes = camera_match.group(2).strip()

    # Extract lighting & color notes
    lighting_match = re.search(r"##\s*Lighting\s*&\s*Color\s*\n(.*?)(?=##|\Z)", section, re.DOTALL)
    if lighting_match:
        lighting_color_notes = lighting_match.group(2).strip()

    if not content_summary and not visual_elements:
        return None

    return SceneInfo(
        index=index,
        time_range=[0.0, 5.0],
        description=content_summary,
        visual_elements=visual_elements,
        camera_notes=camera_notes,
        lighting_color_notes=lighting_color_notes,
        content_summary=content_summary,
    )


def parse_scene_description(input_path: str) -> ParsedSceneDescription:
    """Parse a video_scribe scene description from JSON or Markdown.

    Args:
        input_path: Path to the input file.

    Returns:
        ParsedSceneDescription with extracted scene information.
    """
    if input_path.endswith(".json"):
        return parse_json_scene(input_path)
    elif input_path.endswith(".md"):
        return parse_markdown_scene(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path}. Use .json or .md")
