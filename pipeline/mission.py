"""Load mission.yaml + optional steering lines from master_ideas.md."""

from __future__ import annotations

import pathlib
import re
from typing import Any

import yaml

from pipeline.pipeline_config import PROJECT_ROOT

MISSION_PATH = PROJECT_ROOT / "mission.yaml"

_IDEA_LINE = re.compile(
    r"^\s*-\s*\[[ xX]\]\s+"
    r"(?:\*\*)?"
    r"(?:\[)?(.+?)(?:\])?"
    r"(?:\*\*)?"
    r"\s*[—–-]\s*(.*)$",
    re.IGNORECASE,
)


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


def _master_ideas_candidates() -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    try:
        from pipeline.paths import get_pipeline_dir

        out = get_pipeline_dir() / "master_ideas.md"
        if out.is_file():
            paths.append(out)
    except Exception:
        pass
    factory = PROJECT_ROOT / "master_ideas.md"
    if factory.is_file() and factory not in paths:
        paths.append(factory)
    return paths


def load_steering_from_master_ideas(
    path: pathlib.Path | None = None,
) -> dict[str, Any]:
    """
    Collect --mission / --values / --hardvalue (and [[mission]]/[[values]]) lines.

    Returns {"missions": [str], "hard": [{id, rule}], "soft": [{id, rule}]}.
    """
    from pipeline.idea_tags import is_steering_line, parse_idea_tags

    missions: list[str] = []
    hard: list[dict[str, str]] = []
    soft: list[dict[str, str]] = []
    seen_m: set[str] = set()
    seen_v: set[str] = set()

    files = [path] if path is not None else _master_ideas_candidates()
    for mi in files:
        if mi is None or not mi.is_file():
            continue
        try:
            text = mi.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            if not line.startswith("-"):
                continue
            # Prefer explicit steering flags; also accept [[mission]]/[[values]] alone
            has_tags = "[[mission]" in line.lower() or "[[values]" in line.lower()
            if not is_steering_line(line) and not has_tags:
                continue
            m = _IDEA_LINE.match(line)
            if not m:
                continue
            title, desc = m.group(1).strip(), m.group(2).strip()
            tags = parse_idea_tags(desc, title=title)
            for mission in tags.get("mission") or []:
                key = mission.lower()
                if key and key not in seen_m:
                    seen_m.add(key)
                    missions.append(mission)
            for v in tags.get("values") or []:
                rule = (v.get("rule") or "").strip()
                if not rule:
                    continue
                key = f"{v.get('kind')}:{rule.lower()}"
                if key in seen_v:
                    continue
                seen_v.add(key)
                entry = {"id": title.strip("[]")[:40] or "value", "rule": rule}
                if (v.get("kind") or "soft") == "hard":
                    hard.append(entry)
                else:
                    soft.append(entry)

    return {"missions": missions, "hard": hard, "soft": soft}


def format_values_for_prompt(*, include_hard: bool = True, include_soft: bool = True) -> str:
    lines: list[str] = []
    if mission_text():
        lines.append(f"Factory mission (mission.yaml): {mission_text()}")

    steering = load_steering_from_master_ideas()
    if steering.get("missions"):
        lines.append("Active missions (from master_ideas.md — prefer these when constructing goals):")
        for m in steering["missions"]:
            lines.append(f"  - {m}")

    hard = list(hard_values())
    if include_hard:
        # yaml hard first (immutable defaults), then master_ideas hard tags
        extra_hard = steering.get("hard") or []
        if hard or extra_hard:
            lines.append("Hard values (must not violate; yaml is immutable pipeline policy):")
            for v in hard:
                lines.append(f"  - {v.get('id', '?')}: {v.get('rule', '')}")
            for v in extra_hard:
                lines.append(f"  - {v.get('id', '?')}: {v.get('rule', '')} [master_ideas]")

    if include_soft:
        soft = list(soft_values())
        extra_soft = steering.get("soft") or []
        if soft or extra_soft:
            lines.append("Soft values (prefer; adjustable via master_ideas / slack):")
            for v in soft:
                lines.append(f"  - {v.get('id', '?')}: {v.get('rule', '')}")
            for v in extra_soft:
                lines.append(f"  - {v.get('id', '?')}: {v.get('rule', '')} [master_ideas]")

    return "\n".join(lines)


def mission_prompt_block(*, include_construct: bool = False) -> str:
    """Mission + values block for ideator prompts."""
    block = format_values_for_prompt()
    if include_construct:
        construct = ideator_construct_prompt()
        if construct:
            block = f"{block}\n\nConstruct pass:\n{construct}".strip()
    return block
