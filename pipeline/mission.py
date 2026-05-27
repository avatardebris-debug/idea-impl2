"""Load mission.yaml for ideator, goals, and seed policy."""

from __future__ import annotations

import pathlib
from typing import Any

import yaml

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
MISSION_PATH = PROJECT_ROOT / "mission.yaml"


def load_mission() -> dict[str, Any]:
    if not MISSION_PATH.exists():
        return {}
    try:
        data = yaml.safe_load(MISSION_PATH.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def mission_text() -> str:
    return (load_mission().get("mission") or "").strip()


def hard_values() -> list[dict[str, str]]:
    vals = load_mission().get("values") or {}
    hard = vals.get("hard") or []
    return [v for v in hard if isinstance(v, dict)]


def soft_values() -> list[dict[str, str]]:
    vals = load_mission().get("values") or {}
    soft = vals.get("soft") or []
    return [v for v in soft if isinstance(v, dict)]


def ideator_construct_prompt() -> str:
    m = load_mission()
    block = (m.get("ideator") or {}).get("construct_pass") or ""
    return block.strip()


def ideator_deconstruct_prompt() -> str:
    m = load_mission()
    block = (m.get("ideator") or {}).get("deconstruct_pass") or ""
    return block.strip()


def format_values_for_prompt(*, include_hard: bool = True, include_soft: bool = True) -> str:
    lines: list[str] = []
    if mission_text():
        lines.append(f"Mission: {mission_text()}")
    if include_hard and hard_values():
        lines.append("Hard values (must not violate):")
        for v in hard_values():
            lines.append(f"  - {v.get('id', '?')}: {v.get('rule', '')}")
    if include_soft and soft_values():
        lines.append("Soft values (prefer):")
        for v in soft_values():
            lines.append(f"  - {v.get('id', '?')}: {v.get('rule', '')}")
    return "\n".join(lines)
