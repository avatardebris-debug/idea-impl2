"""
pipeline/ideator_enrich.py
Post-process ideator output: kind tags, harness → capability_gaps, bridge metadata.
"""

from __future__ import annotations

import re
from typing import Any

from pipeline.capability_gaps import append_capability_gap
from pipeline.connector_synthesis import parse_ideator_groups

HARNESS_GROUPS = frozenset({"pipeline_core", "debug", "speed", "learning", "harness"})
BRIDGE_GROUPS = frozenset({"bridge", "combination", "agentic"})
EXPERIMENT_GROUPS = frozenset({"experiment", "experiments"})


def _group_from_header(label: str, num: str) -> str:
    label = label.upper()
    if num == "1" or "PIPELINE" in label and "CORE" in label:
        return "pipeline_core"
    if num == "2" or "DEBUG" in label:
        return "debug"
    if num == "3" or "SPEED" in label or "EFFICI" in label:
        return "speed"
    if num == "4" or "LEARNING" in label or "RSI" in label:
        return "learning"
    if num == "5" or "AGENTIC" in label or "BRIDGE" in label:
        return "agentic"
    if num == "6" or "EXPERIMENT" in label:
        return "experiment"
    # legacy
    if "COMBINATION" in label:
        return "combination"
    if "BRIDGE" in label:
        return "bridge"
    if "HARNESS" in label:
        return "harness"
    return "unknown"


def parse_groups_with_labels(raw_text: str) -> list[dict[str, Any]]:
    """Like connector_synthesis.parse_ideator_groups but with new group keys."""
    from pipeline.connector_synthesis import IDEA_LINE_RE, GROUP_HEADER_RE, _parse_title_and_desc

    current = "unknown"
    items: list[dict[str, Any]] = []
    for line in raw_text.splitlines():
        gh = GROUP_HEADER_RE.search(line)
        if gh:
            current = _group_from_header(gh.group("label") or "", gh.group("num"))
            continue
        if not re.match(r"^\s*-\s*\[[ xX]\]", line):
            continue
        title, desc, reqs = _parse_title_and_desc(line)
        if not title:
            continue
        items.append(
            {
                "group": current,
                "title": title,
                "description": desc,
                "requires": reqs,
                "line": line.strip(),
            }
        )
    return items


def _inject_kind(line: str, kind: str) -> str:
    if re.search(rf"\bkind:\s*{kind}\b", line, re.I):
        return line
    # Insert after **title**
    m = re.match(r"^(\s*-\s*\[[ xX]\]\s*\*\*.+?\*\*)\s*(.*)$", line)
    if not m:
        return line
    rest = m.group(2)
    if rest.lstrip().startswith("kind:"):
        return line
    return f"{m.group(1)} kind:{kind} {rest}"


def _line_title(line: str) -> str:
    m = re.search(r"\*\*(.+?)\*\*", line)
    return m.group(1).strip() if m else line.strip()


def enrich_ideator_lines(raw_text: str, idea_lines: list[str]) -> tuple[list[str], dict[str, Any]]:
    """
    Tag lines by group; append harness ideas to capability_gaps.md.
    Returns updated lines + summary.
    """
    grouped = parse_groups_with_labels(raw_text)
    title_to_group: dict[str, str] = {g["title"]: g["group"] for g in grouped}

    harness_added = 0
    tagged = 0
    updated: list[str] = []

    for line in idea_lines:
        title = _line_title(line)
        group = title_to_group.get(title, "unknown")
        new_line = line

        if group in HARNESS_GROUPS:
            new_line = _inject_kind(new_line, "harness")
            tagged += 1
            if title:
                desc_m = re.split(r"[—–-]\s*", new_line, maxsplit=1)
                desc = desc_m[-1].strip() if len(desc_m) > 1 else ""
                try:
                    append_capability_gap(title, f"[harness] {desc[:300]}")
                    harness_added += 1
                except Exception:
                    pass
        elif group in EXPERIMENT_GROUPS:
            new_line = _inject_kind(new_line, "experiment")
            tagged += 1
        elif group in BRIDGE_GROUPS:
            if "kind:connector" not in new_line.lower():
                new_line = _inject_kind(new_line, "connector")
            tagged += 1

        updated.append(new_line)

    return updated, {
        "tagged": tagged,
        "harness_gaps_added": harness_added,
    }
