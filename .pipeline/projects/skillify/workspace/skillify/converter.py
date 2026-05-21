"""
converter.py — Converts extraction dicts into skill JSON files.
"""
from __future__ import annotations
import json
import re
import pathlib
from datetime import datetime, timezone
from typing import Any


def _to_skill_id(title: str) -> str:
    """Convert title to snake_case skill ID."""
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug[:60] or "unnamed_skill"


def _infer_tags(extraction: dict) -> list[str]:
    fmt = extraction.get("format", "steps")
    topic = extraction.get("topic", "").lower()
    tags = [fmt]
    # Include explicit tags from extraction if provided
    explicit_tags = extraction.get("tags", [])
    if explicit_tags:
        tags.extend(explicit_tags)
    for kw, tag in [
        ("cook", "cooking"), ("recipe", "cooking"), ("bake", "cooking"),
        ("code", "programming"), ("program", "programming"), ("software", "programming"),
        ("security", "security"), ("legal", "legal"), ("medical", "health"),
        ("install", "setup"), ("setup", "setup"), ("config", "setup"),
        ("market", "marketing"), ("seo", "marketing"), ("sales", "business"),
    ]:
        if kw in topic:
            tags.append(tag)
    return list(dict.fromkeys(tags))  # dedup, preserve order


def _build_parameters(extraction: dict) -> dict:
    """Build a JSON Schema parameters block describing the skill's inputs."""
    components = extraction.get("components", [])
    properties: dict[str, Any] = {}
    required: list[str] = []

    if components:
        properties["components"] = {
            "type": "array",
            "description": "List of required ingredients/materials",
            "items": {"type": "object"},
            "default": components,
        }

    # Generic parameters that apply to all skills
    properties["context"] = {
        "type": "string",
        "description": "Optional context or customization notes for this skill execution",
    }
    properties["target_output"] = {
        "type": "string",
        "description": "Desired output or goal for this skill run",
    }

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def convert(extraction: dict, skill_id: str | None = None) -> dict[str, Any]:
    """Convert an extraction dict to a skill JSON dict.

    Args:
        extraction: Output from extraction.extractor.extract()
        skill_id:   Override skill ID (auto-generated from title if None)

    Returns:
        Skill dict ready for JSON serialisation.
    """
    title  = extraction.get("title", "Unnamed Skill")
    sid    = skill_id or _to_skill_id(title)
    meta   = extraction.get("metadata", {})

    skill = {
        "skill_id":    sid,
        "name":        title,
        "version":     "1.0.0",
        "description": extraction.get("description", ""),
        "tags":        _infer_tags(extraction),
        "parameters":  _build_parameters(extraction),
        "steps": [
            {
                "step":     s.get("step_number", i + 1),
                "action":   s.get("action", ""),
                "detail":   s.get("detail", ""),
                "duration": s.get("duration", ""),
                "tools":    s.get("tools", []),
                "warnings": s.get("warnings", []),
            }
            for i, s in enumerate(extraction.get("steps", []))
        ],
        "components": extraction.get("components", []),
        "tips":        extraction.get("tips", []),
        "source": {
            "format":       extraction.get("format", "steps"),
            "topic":        extraction.get("topic", ""),
            "extracted_at": meta.get("extracted_at", datetime.now(timezone.utc).isoformat()),
            "model":        meta.get("model", "unknown"),
            "source_length": meta.get("source_length", 0),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return skill


def save_skill(skill: dict, output_path: str | pathlib.Path) -> pathlib.Path:
    """Save skill dict as a JSON file.

    Args:
        skill:       Skill dict from convert()
        output_path: File path to write (created if missing)

    Returns:
        Resolved Path of the written file.
    """
    p = pathlib.Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(skill, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def load_skill(path: str | pathlib.Path) -> dict[str, Any]:
    """Load a skill JSON file."""
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
