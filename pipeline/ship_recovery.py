"""Ship-prove failure recovery — no manager agent; self-heal or mark ship_insufficient."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.paths import projects_dir
from pipeline.ship_provenance import load_provenance, save_provenance
from pipeline.ship_status import TERMINAL_SHIP_STATUSES, is_ship_in_flight

if TYPE_CHECKING:
    from pipeline.message_bus import MessageBus


def max_ship_agent_failures() -> int:
    try:
        return max(1, int(os.environ.get("MAX_SHIP_AGENT_FAILURES", "5")))
    except ValueError:
        return 5


def max_ship_stall_recoveries() -> int:
    try:
        return max(1, int(os.environ.get("MAX_SHIP_STALL_RECOVERIES", "8")))
    except ValueError:
        return 8


def ship_stall_recovery_cooldown_s() -> float:
    try:
        return max(60.0, float(os.environ.get("SHIP_STALL_RECOVERY_COOLDOWN_S", "300")))
    except ValueError:
        return 300.0


def _project_dir(slug: str) -> Path:
    return projects_dir() / slug


def _append_recovery_note(project_dir: Path, line: str) -> None:
    path = project_dir / "phases" / "ship" / "recovery_log.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    existing = path.read_text(encoding="utf-8") if path.is_file() else "# Ship recovery log\n\n"
    path.write_text(existing + f"- [{ts}] {line}\n", encoding="utf-8")


def mark_ship_insufficient(slug: str, reason: str) -> None:
    """Terminal ship status — runner may advance to next project or exit."""
    project_dir = _project_dir(slug)
    state_file = project_dir / "state" / "current_idea.json"
    if not state_file.is_file():
        return
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return
    state["status"] = "ship_insufficient"
    state["ship_insufficient_reason"] = reason[:500]
    state["ship_insufficient_at"] = datetime.now(timezone.utc).isoformat()
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    _append_recovery_note(project_dir, f"**ship_insufficient** — {reason}")
    print(f"  [ship-recovery] '{slug}' → ship_insufficient: {reason[:120]}", flush=True)


def _requeue_from_status(bus: "MessageBus", slug: str, status: str) -> bool:
    from pipeline.ship_mode import dispatch_ship_requeue

    project_dir = _project_dir(slug)
    state_file = project_dir / "state" / "current_idea.json"
    if not state_file.is_file():
        return False
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return False
    title = state.get("title", slug)
    return dispatch_ship_requeue(bus, slug, title, state, project_dir, status)


def handle_ship_agent_failure(
    bus: "MessageBus",
    slug: str,
    role: str,
    reason: str,
) -> None:
    """
    Called when a ship agent crashes, times out, or exhausts message retries.

    Retries via re-queue until budget exhausted, then ship_insufficient.
    """
    if not slug:
        return
    project_dir = _project_dir(slug)
    prov = load_provenance(project_dir)
    failures = int(prov.get("agent_failures", 0)) + 1
    save_provenance(project_dir, {**prov, "agent_failures": failures})
    _append_recovery_note(project_dir, f"agent failure #{failures} ({role}): {reason[:200]}")

    if failures >= max_ship_agent_failures():
        mark_ship_insufficient(
            slug,
            f"{role} failed {failures} times: {reason[:200]}",
        )
        try_advance_ship_queue(bus)
        return

    state_file = project_dir / "state" / "current_idea.json"
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        status = state.get("status", "")
    except Exception:
        status = "field_test_planning"

    if status == "field_testing":
        state["status"] = "field_test_planning"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        status = "field_test_planning"
    elif not is_ship_in_flight(status):
        state["status"] = "field_test_planning"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        status = "field_test_planning"

    if _requeue_from_status(bus, slug, status):
        print(
            f"  [ship-recovery] Re-queued '{slug}' after {role} failure "
            f"({failures}/{max_ship_agent_failures()})",
            flush=True,
        )


def record_ship_stall_recovery(slug: str, *, requeued: bool) -> bool:
    """
    Track idle stall recoveries with no LLM progress.

    Returns True if project was marked ship_insufficient.
    """
    if not slug:
        return False
    project_dir = _project_dir(slug)
    prov = load_provenance(project_dir)
    count = int(prov.get("stall_recoveries", 0)) + 1
    save_provenance(project_dir, {**prov, "stall_recoveries": count})
    note = f"stall recovery #{count}" + (" (re-queued)" if requeued else " (no re-queue)")
    _append_recovery_note(project_dir, note)

    if count >= max_ship_stall_recoveries():
        mark_ship_insufficient(
            slug,
            f"No LLM progress after {count} stall recoveries",
        )
        return True
    return False


def handle_ship_stall_idle(
    bus: "MessageBus",
    *,
    slug_filter: str = "",
    requeued: int,
    stuck_slugs: set[str] | None = None,
) -> None:
    """After stall detection: budget stall cycles only for stuck slugs.

    When *stuck_slugs* is provided, only those projects are charged a stall
    recovery. Otherwise fall back to the slug_filter (single-slug runs) or the
    single most-recently-modified in-flight project — never every in-flight
    project in the tree.
    """
    from pipeline.ship_mode import read_project_status, ship_slugs_in_scope

    targets: list[str] = []
    if stuck_slugs:
        targets = sorted(stuck_slugs)
    elif slug_filter:
        targets = ship_slugs_in_scope(slug_filter)
    else:
        # Pick one active in-flight project (most recently checkpointed).
        best_slug = ""
        best_mtime = -1.0
        for slug in ship_slugs_in_scope(""):
            status = read_project_status(slug)
            if status in TERMINAL_SHIP_STATUSES or not is_ship_in_flight(status):
                continue
            state_file = _project_dir(slug) / "state" / "current_idea.json"
            try:
                mtime = state_file.stat().st_mtime
            except OSError:
                mtime = 0.0
            if mtime >= best_mtime:
                best_mtime = mtime
                best_slug = slug
        if best_slug:
            targets = [best_slug]

    for slug in targets:
        status = read_project_status(slug)
        if status in TERMINAL_SHIP_STATUSES:
            continue
        if not is_ship_in_flight(status):
            continue
        if record_ship_stall_recovery(slug, requeued=bool(requeued)):
            try_advance_ship_queue(bus, slug_filter=slug_filter)
            return

    if requeued:
        print(
            f"  [ship-recovery] Stall re-queue ({requeued} project(s)); "
            f"will mark ship_insufficient after {max_ship_stall_recoveries()} idle cycles",
            flush=True,
        )


def try_advance_ship_queue(
    bus: "MessageBus",
    *,
    slug_filter: str = "",
) -> int:
    """
    Queue the next project when the current one is terminal.

    Prefers a fresh ``complete`` project; if none, resumes one in-flight
    ship project (so --ship-serial can drain the backlog one at a time).
    """
    from pipeline.ship_mode import (
        dedupe_ship_pending,
        queue_ship_prove_projects,
        requeue_in_progress_ship_projects,
    )

    n, _fresh = queue_ship_prove_projects(bus, slug_filter=slug_filter, limit=1)
    if not n:
        n = requeue_in_progress_ship_projects(
            bus, slug_filter=slug_filter, limit=1
        )
    if n:
        dedupe_ship_pending(bus)
        print(f"  [ship-recovery] Advanced to next project ({n} queued)", flush=True)
    return n


def reset_ship_failure_counters(project_dir: Path) -> None:
    """Clear failure counters after successful agent completion."""
    prov = load_provenance(project_dir)
    if prov.get("agent_failures") or prov.get("stall_recoveries"):
        save_provenance(
            project_dir,
            {**prov, "agent_failures": 0, "stall_recoveries": 0},
        )
