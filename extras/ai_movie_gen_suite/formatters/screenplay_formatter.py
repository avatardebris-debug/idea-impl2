"""Screenplay formatters — convert between data models and output formats."""

from __future__ import annotations

import json
from pathlib import Path

from ai_movie_gen_suite.models import Script


def format_screenplay_text(script: Script) -> str:
    """Format a Script into standard screenplay text (industry format)."""
    lines = []
    lines.append(f"TITLE: {script.logline}")
    lines.append("=" * 60)

    for scene in script.scenes:
        lines.append(f"\n{scene.scene_heading}")
        lines.append("-" * 40)

        if scene.action:
            lines.append(scene.action)
            lines.append("")

        for line in scene.dialogue_lines:
            lines.append(f"    {line.character_name}")
            if line.parenthetical:
                lines.append(f"        ({line.parenthetical})")
            lines.append(f"        {line.text}")
            lines.append("")

    return "\n".join(lines)


def format_fdx(script: Script) -> dict:
    """Format a Script as FDX-compatible JSON (Final Draft export format)."""
    fdx = {
        "title": script.logline,
        "format": "screenplay",
        "scenes": [],
    }

    for scene in script.scenes:
        fdx_scene = {
            "scene_id": scene.scene_id,
            "heading": scene.scene_heading,
            "action": scene.action,
            "characters_present": scene.characters_present,
            "dialogue": [],
        }

        for line in scene.dialogue_lines:
            fdx_scene["dialogue"].append({
                "character": line.character_name,
                "character_id": None,
                "text": line.text,
                "parenthetical": line.parenthetical,
            })

        fdx["scenes"].append(fdx_scene)

    return fdx


def save_screenplay_text(script: Script, output_path: Path) -> None:
    """Save screenplay as formatted text file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_screenplay_text(script))


def save_fdx(script: Script, output_path: Path) -> None:
    """Save screenplay as FDX-compatible JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(format_fdx(script), indent=2))
