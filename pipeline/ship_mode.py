"""
pipeline/ship_mode.py
--ship-prove loop: field-test complete projects (separate from main seeding loop).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.message_bus import Message
from pipeline.paths import projects_dir
from pipeline.ship_provenance import load_provenance
from pipeline.ship_status import TERMINAL_SHIP_STATUSES, is_ship_prove_eligible

if TYPE_CHECKING:
    from pipeline.message_bus import MessageBus

SHIP_AGENT_ROLES = (
    "field_test_planner",
    "executor",
)


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug.strip("_") or "unknown"


def queue_ship_prove_projects(
    bus: "MessageBus",
    *,
    slug_filter: str = "",
    limit: int = 0,
) -> int:
    """
    Queue field_test_planner for projects with status=complete.

    Skips projects already field_proven or ship_insufficient.
    Returns count queued.
    """
    root = projects_dir()
    if not root.is_dir():
        return 0

    queued = 0
    for project_dir in sorted(root.iterdir()):
        if not project_dir.is_dir():
            continue
        slug = project_dir.name
        if slug_filter and slug_filter not in slug:
            continue

        state_file = project_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        status = state.get("status", "")
        if status in TERMINAL_SHIP_STATUSES:
            continue
        if status == "field_test_failed":
            # Re-queue after executor fix — handled by dispatch_ship_requeue
            continue
        if not is_ship_prove_eligible(status):
            continue

        prov = load_provenance(project_dir)
        if prov.get("maturity_stage") in ("M2", "M3", "M4"):
            continue

        state["status"] = "field_test_planning"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="field_test_planner",
                type="task",
                payload={
                    "idea_slug": slug,
                    "phase": state.get("phase", state.get("total_phases", 1)),
                },
                priority=1,
            )
        )
        print(f"  [ship-prove] Queued field tests for '{state.get('title', slug)}'")
        queued += 1
        if limit and queued >= limit:
            break
    return queued


def dispatch_ship_requeue(
    bus: "MessageBus",
    slug: str,
    title: str,
    state: dict,
    project_dir: Path,
    status: str,
) -> bool:
    """Re-queue ship-track statuses (field_test_planning / field_test_failed)."""
    if status == "field_test_planning":
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="field_test_planner",
                type="task",
                payload={
                    "idea_slug": slug,
                    "phase": state.get("phase", 1),
                },
            )
        )
        return True
    if status == "field_test_failed":
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="executor",
                type="task",
                payload={
                    "phase": state.get("phase", 1),
                    "idea_slug": slug,
                    "ship_fix": True,
                    "field_test_results_path": "phases/ship/field_test_results.md",
                    "tasks_path": f"phases/phase_{state.get('phase', 1)}/tasks.md",
                    "workspace_path": str(project_dir / "workspace"),
                    "fix_required": True,
                    "error_summary": "Field tests failed — fix and re-run ship prove.",
                },
                priority=1,
            )
        )
        return True
    return False


def run_ship_prove_mode(
    bus: "MessageBus",
    *,
    slug_filter: str = "",
) -> int:
    """Entry for startup: queue all eligible complete projects."""
    return queue_ship_prove_projects(bus, slug_filter=slug_filter)
