"""Output formatting for Video Scribe.

Supports markdown and JSON output for single-frame and multi-scene analyses.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def format_single_frame_markdown(
    analysis: Dict[str, Any],
    title: str = "Video Analysis",
    duration: float = 0.0,
) -> str:
    """Format a single-frame analysis as markdown."""
    visual_elements = ", ".join(analysis.get("visual_elements", []))
    camera_notes = analysis.get("camera_notes", "N/A")
    lighting_notes = analysis.get("lighting_color_notes", "N/A")

    return f"""# {title}

**Duration:** {duration:.2f}s

## Content Summary

{analysis.get("content_summary", "N/A")}

## Visual Elements

{visual_elements}

## Camera Notes

{camera_notes}

## Lighting & Color Notes

{lighting_notes}
"""


def format_single_frame_json(
    analysis: Dict[str, Any],
    title: str = "Video Analysis",
    duration: float = 0.0,
) -> str:
    """Format a single-frame analysis as JSON."""
    output = {
        "title": title,
        "duration": duration,
        "content_summary": analysis.get("content_summary", "N/A"),
        "visual_elements": analysis.get("visual_elements", []),
        "camera_notes": analysis.get("camera_notes", "N/A"),
        "lighting_color_notes": analysis.get("lighting_color_notes", "N/A"),
    }
    return json.dumps(output, indent=2)


def format_multi_scene_markdown(
    scenes: List[Dict[str, Any]],
    title: str = "Video Analysis",
    duration: float = 0.0,
) -> str:
    """Format multi-scene analysis as markdown."""
    lines = [f"# {title}", f"", f"**Total Duration:** {duration:.2f}s", ""]

    for i, scene in enumerate(scenes, 1):
        lines.append(f"## Scene {i}")
        lines.append(f"**Time:** {scene.get('start_time', 0):.2f}s - {scene.get('end_time', 0):.2f}s")
        lines.append(f"**Frames:** {scene.get('start_frame', 0)} - {scene.get('end_frame', 0)}")
        lines.append("")
        lines.append(f"**Content:** {scene.get('content_summary', 'N/A')}")
        lines.append("")
        lines.append("**Visual Elements:**")
        for elem in scene.get("visual_elements", []):
            lines.append(f"- {elem}")
        lines.append("")
        lines.append(f"**Camera:** {scene.get('camera_notes', 'N/A')}")
        lines.append("")
        lines.append(f"**Lighting & Color:** {scene.get('lighting_color_notes', 'N/A')}")
        lines.append("")

        if i < len(scenes):
            transition = scene.get("transition_to_next")
            if transition:
                lines.append(f"**Transition to Scene {i+1}:**")
                lines.append(transition)
                lines.append("")

    return "\n".join(lines)


def format_multi_scene_json(
    scenes: List[Dict[str, Any]],
    title: str = "Video Analysis",
    duration: float = 0.0,
) -> str:
    """Format multi-scene analysis as JSON."""
    output = {
        "title": title,
        "duration": duration,
        "scenes": [],
    }

    for i, scene in enumerate(scenes):
        scene_data = {
            "scene_number": i + 1,
            "start_time": scene.get("start_time", 0),
            "end_time": scene.get("end_time", 0),
            "start_frame": scene.get("start_frame", 0),
            "end_frame": scene.get("end_frame", 0),
            "content_summary": scene.get("content_summary", "N/A"),
            "visual_elements": scene.get("visual_elements", []),
            "camera_notes": scene.get("camera_notes", "N/A"),
            "lighting_color_notes": scene.get("lighting_color_notes", "N/A"),
        }
        if "transition_to_next" in scene:
            scene_data["transition_to_next"] = scene["transition_to_next"]
        output["scenes"].append(scene_data)

    return json.dumps(output, indent=2)


class ProgressIndicator:
    """Simple progress indicator for the CLI."""

    def __init__(self, total: int, label: str = "Processing"):
        self.total = total
        self.label = label
        self.current = 0

    def update(self, n: int = 1) -> None:
        self.current += n
        if self.total > 0:
            pct = self.current / self.total * 100
            print(f"\r{self.label}: {self.current}/{self.total} ({pct:.1f}%)", end="", flush=True)

    def finish(self) -> None:
        print()  # Newline after progress
