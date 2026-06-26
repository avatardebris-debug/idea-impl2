"""Parse [[goal]], [[system]], [[mission]], [[values]] tags from master_ideas lines."""

from __future__ import annotations

import re
from typing import Any

_TAG_GOAL = re.compile(r"\[\[goal\]\s*([^\]]+)\]", re.IGNORECASE)
_TAG_SYSTEM = re.compile(r"\[\[system\]\s*([^\]]+)\]", re.IGNORECASE)
_TAG_MISSION = re.compile(r"\[\[mission\]\s*([^\]]+)\]", re.IGNORECASE)
_TAG_VALUES = re.compile(r"\[\[values\]\s*([^\]]+)\]", re.IGNORECASE)


def parse_idea_tags(text: str) -> dict[str, Any]:
    """
    Extract structured tags from a master_ideas description line.

    Returns dict with goal_id, system_id, mission (list), values (list of {kind, rule}).
    """
    goal_m = _TAG_GOAL.search(text)
    system_m = _TAG_SYSTEM.search(text)
    missions = [m.group(1).strip() for m in _TAG_MISSION.finditer(text)]
    values: list[dict[str, str]] = []
    for m in _TAG_VALUES.finditer(text):
        raw = m.group(1).strip()
        if ":" in raw:
            kind, rule = raw.split(":", 1)
            kind = kind.strip().lower()
            rule = rule.strip()
        else:
            kind, rule = "soft", raw
        if kind not in ("hard", "soft"):
            kind = "soft"
        values.append({"kind": kind, "rule": rule})

    return {
        "goal_id": goal_m.group(1).strip() if goal_m else "",
        "system_id": system_m.group(1).strip() if system_m else "",
        "mission": missions,
        "values": values,
    }


def strip_idea_tags(text: str) -> str:
    """Remove [[...]] tags from description for seeding prompts."""
    out = text
    for pat in (_TAG_GOAL, _TAG_SYSTEM, _TAG_MISSION, _TAG_VALUES):
        out = pat.sub("", out)
    return re.sub(r"\s{2,}", " ", out).strip()
