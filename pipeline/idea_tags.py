"""Parse [[goal]], [[system]], [[mission]], [[values]] tags and --mission/--values flags."""

from __future__ import annotations

import re
from typing import Any

_TAG_GOAL = re.compile(r"\[\[goal\]\s*([^\]]+)\]", re.IGNORECASE)
_TAG_SYSTEM = re.compile(r"\[\[system\]\s*([^\]]+)\]", re.IGNORECASE)
_TAG_MISSION = re.compile(r"\[\[mission\]\s*([^\]]+)\]", re.IGNORECASE)
_TAG_VALUES = re.compile(r"\[\[values\]\s*([^\]]+)\]", re.IGNORECASE)

# Trailing flags (same family as --goal / --hermes)
_FLAG_MISSION = re.compile(r"\s--mission\s*$", re.IGNORECASE)
_FLAG_VALUES = re.compile(r"\s--values\s*$", re.IGNORECASE)
_FLAG_HARDVALUE = re.compile(r"\s--hardvalue\s*$", re.IGNORECASE)
_FLAG_STEERING = re.compile(
    r"\s--(?:mission|values|hardvalue)\s*$", re.IGNORECASE
)


def is_steering_line(line: str) -> bool:
    """True when the line declares mission/values and must not seed as a software project."""
    return bool(_FLAG_STEERING.search(line or ""))


def parse_idea_tags(text: str, *, title: str = "") -> dict[str, Any]:
    """
    Extract structured tags from a master_ideas description line.

    Returns dict with goal_id, system_id, mission (list), values (list of {kind, rule}),
    and steering (mission|values|hardvalue|"").
    """
    text = text or ""
    steering = ""
    if _FLAG_HARDVALUE.search(text):
        steering = "hardvalue"
        text = _FLAG_HARDVALUE.sub("", text).strip()
    elif _FLAG_VALUES.search(text):
        steering = "values"
        text = _FLAG_VALUES.sub("", text).strip()
    elif _FLAG_MISSION.search(text):
        steering = "mission"
        text = _FLAG_MISSION.sub("", text).strip()

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

    # Flag-only lines: use title + remaining description as the mission/value body
    body = strip_idea_tags(text).strip()
    if steering == "mission" and not missions:
        label = (title or "").strip().strip("[]") or body[:80]
        missions.append(label if not body else f"{label}: {body}" if label and body and label.lower() not in body.lower() else (body or label))
    if steering in ("values", "hardvalue") and not values:
        kind = "hard" if steering == "hardvalue" else "soft"
        rule = body or (title or "").strip().strip("[]")
        if rule:
            values.append({"kind": kind, "rule": rule})

    return {
        "goal_id": goal_m.group(1).strip() if goal_m else "",
        "system_id": system_m.group(1).strip() if system_m else "",
        "mission": missions,
        "values": values,
        "steering": steering,
    }


def strip_idea_tags(text: str) -> str:
    """Remove [[...]] tags and trailing --mission/--values/--hardvalue flags."""
    out = text or ""
    for pat in (_TAG_GOAL, _TAG_SYSTEM, _TAG_MISSION, _TAG_VALUES):
        out = pat.sub("", out)
    out = _FLAG_HARDVALUE.sub("", out)
    out = _FLAG_VALUES.sub("", out)
    out = _FLAG_MISSION.sub("", out)
    return re.sub(r"\s{2,}", " ", out).strip()
