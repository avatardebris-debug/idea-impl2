"""
pipeline/dep_policy.py
Shared dependency satisfaction and project status vocabulary.
"""

from __future__ import annotations

import re
from typing import Any, Literal, Mapping

_REQUIRES_TRAILING_RE = re.compile(
    r"\brequires:\s*([\w,\s_-]+?)[\]\s.]*$",
    re.IGNORECASE,
)

DepContext = Literal["seeding", "rebuild", "purge"]

# Full completion unlocks dependents. mvp_complete does NOT.
FULL_COMPLETE_STATUSES = frozenset({"complete", "field_proven"})

# Terminal / non-coding statuses for runner & agents
BUILD_TERMINAL_STATUSES = frozenset({
    "complete",
    "mvp_complete",
    "budget_exceeded",
    "dep_waiting",
    "field_proven",
    "ship_insufficient",
    "stalled",
})

# Eligible for --polish / polish-first resume
POLISHABLE_STATUSES = frozenset({"complete", "mvp_complete", "budget_exceeded"})

# Sacred: in-flight agents must not overwrite these
AGENT_SACRED_STATUSES = frozenset({
    "complete",
    "mvp_complete",
    "stalled",
    "budget_exceeded",
    "field_proven",
    "ship_insufficient",
})

# Skip when counting active slots / eviction / rebuild (aligned with build terminals)
EVICTION_SKIP_STATUSES = BUILD_TERMINAL_STATUSES | frozenset({""})


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


def phases_fully_built(state: Mapping[str, Any]) -> bool:
    """True when current phase index has reached planned total_phases."""
    try:
        phase = state.get("phase", 0)
        total = state.get("total_phases", 1)
        # Explicit None (key present) must not raise — treat as incomplete
        return int(phase if phase is not None else 0) >= int(total if total is not None else 1)
    except (TypeError, ValueError):
        return False


def is_full_complete(state: Mapping[str, Any]) -> bool:
    """True when project is fully complete (all phases) or field-proven."""
    status = str(state.get("status", ""))
    if status == "field_proven":
        return True
    if status != "complete":
        return False
    return phases_fully_built(state)


def is_build_terminal(status: str) -> bool:
    return status in BUILD_TERMINAL_STATUSES


def is_polishable(status: str) -> bool:
    return status in POLISHABLE_STATUSES


def is_runner_inactive(status: str) -> bool:
    """Statuses that should not appear as the active in-progress project."""
    return status in BUILD_TERMINAL_STATUSES or status == ""


def is_eviction_skip(status: str) -> bool:
    """Inactive for parallel-slot eviction and rebuild mutation skips."""
    return status in EVICTION_SKIP_STATUSES


def is_rebuild_skip(status: str) -> bool:
    """Do not rewrite session timestamps or requeue these statuses."""
    return is_eviction_skip(status)


def is_seed_list_skip(status: str) -> bool:
    """Master-list lines with these statuses: continue scanning (never SEED_SEEDED).

    ``dep_waiting`` is excluded — it needs dependency re-check / possible resume.
    """
    return status in BUILD_TERMINAL_STATUSES and status != "dep_waiting"


def is_agent_sacred(status: str) -> bool:
    return status in AGENT_SACRED_STATUSES


def dep_status_satisfied(
    status: str | None = None,
    *,
    context: DepContext,
    state: Mapping[str, Any] | None = None,
) -> bool:
    """Return True when a dependency unblocks dependents.

    Prefer *state* so phase/total are checked (legacy ``complete`` with
    incomplete phases does NOT satisfy). Status-only is only safe for
    ``field_proven``; bare ``complete`` without state is treated as incomplete.
    """
    _ = context
    if state is not None:
        return is_full_complete(state)
    if status == "field_proven":
        return True
    # Without phase data, bare "complete" is ambiguous — fail closed
    return False


def dep_blocking_reason(
    dep_slug: str,
    status: str | None = None,
    *,
    context: DepContext,
    state: Mapping[str, Any] | None = None,
) -> str | None:
    """Human-readable blocker if *dep_slug* is not satisfied, else None."""
    if state is not None:
        if is_full_complete(state):
            return None
        st = str(state.get("status") or status or "?")
        if st == "complete" and not phases_fully_built(state):
            return (
                f"{dep_slug} (complete p{state.get('phase', '?')}"
                f"/{state.get('total_phases', '?')} — not full)"
            )
        return f"{dep_slug} ({st})"
    if status is None:
        return f"{dep_slug} (not started)"
    if dep_status_satisfied(status, context=context):
        return None
    if status == "complete":
        return f"{dep_slug} (complete, phase unknown)"
    return f"{dep_slug} ({status or '?'})"
