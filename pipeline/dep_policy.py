"""
pipeline/dep_policy.py
Shared dependency satisfaction rules for seeding and rebuild paths.
"""

from __future__ import annotations

import re
from typing import Literal

_REQUIRES_TRAILING_RE = re.compile(
    r"\brequires:\s*([\w,\s_-]+?)[\]\s.]*$",
    re.IGNORECASE,
)

DepContext = Literal["seeding", "rebuild", "purge"]


def parse_requires_from_description(text: str) -> list[str]:
    """Parse trailing ``requires: slug1, slug2`` from an idea description."""
    m = _REQUIRES_TRAILING_RE.search(text)
    if not m:
        return []
    return [d.strip() for d in re.split(r"[,;]+", m.group(1)) if d.strip()]


def split_requires_from_description(text: str) -> tuple[str, list[str]]:
    """Return description with requires suffix removed, plus dependency slugs."""
    m = _REQUIRES_TRAILING_RE.search(text)
    if not m:
        return text, []
    deps = parse_requires_from_description(text)
    cleaned = text[: m.start()].strip().rstrip(".")
    return cleaned, deps


def dep_status_satisfied(status: str, *, context: DepContext) -> bool:
    """Return True when a dependency project's status unblocks dependents.

    ``budget_exceeded`` does NOT satisfy — the prereq must actually finish.
    Rebuild may reset budget_exceeded prereqs separately so they can be retried.
    All contexts share this rule; ``context`` documents the call site.
    """
    _ = context  # reserved for future context-specific rules
    return status in ("complete", "field_proven")


def dep_blocking_reason(
    dep_slug: str,
    status: str | None,
    *,
    context: DepContext,
) -> str | None:
    """Human-readable blocker if *dep_slug* is not satisfied, else None."""
    if status is None:
        return f"{dep_slug} (not started)"
    if dep_status_satisfied(status, context=context):
        return None
    return f"{dep_slug} ({status or '?'})"
