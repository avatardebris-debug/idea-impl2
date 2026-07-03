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
from pipeline.pipeline_config import SHIP_AGENT_ROLES
from pipeline.ship_provenance import load_provenance
from pipeline.ship_status import TERMINAL_SHIP_STATUSES, is_ship_prove_eligible, is_ship_status

if TYPE_CHECKING:
    from pipeline.message_bus import MessageBus


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug.strip("_") or "unknown"


def resolve_slug_prefix(prefix: str) -> str:
    """Map --ship-slug substring filter to a project folder name for status display."""
    if not prefix:
        return ""
    root = projects_dir()
    if not root.is_dir():
        return prefix
    exact = root / prefix
    if exact.is_dir():
        return prefix
    matches = sorted(p.name for p in root.iterdir() if p.is_dir() and prefix in p.name)
    if len(matches) == 1:
        return matches[0]
    return prefix


def ship_bus_has_work(bus: "MessageBus") -> bool:
    """True if ship-prove agents have pending or in-flight tasks."""
    pending = sum(bus.queue_depth(r) for r in SHIP_AGENT_ROLES)
    if pending > 0:
        return True
    try:
        processing = bus.get_processing_messages()
    except Exception:
        return False
    ship_roles = set(SHIP_AGENT_ROLES)
    return any(getattr(m, "to_agent", "") in ship_roles for m in processing)


def queue_ship_prove_projects(
    bus: "MessageBus",
    *,
    slug_filter: str = "",
    limit: int = 0,
) -> tuple[int, set[str]]:
    """
    Queue field_test_planner for projects with status=complete.

    Skips projects already field_proven or ship_insufficient.
    Returns (count queued, slugs freshly queued).
    """
    root = projects_dir()
    if not root.is_dir():
        return 0, set()

    queued = 0
    fresh_slugs: set[str] = set()
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
            # Mid-flight — requeue_in_progress_ship_projects handles resume
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
        fresh_slugs.add(slug)
        if limit and queued >= limit:
            break
    return queued, fresh_slugs


def dispatch_ship_requeue(
    bus: "MessageBus",
    slug: str,
    title: str,
    state: dict,
    project_dir: Path,
    status: str,
) -> bool:
    """Re-queue ship-track statuses."""
    phase = state.get("phase", 1)
    base = {"idea_slug": slug, "phase": phase}

    if status == "field_test_planning":
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="field_test_planner",
                type="task",
                payload=base,
            )
        )
        return True
    if status == "field_test_failed":
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="debug_loop",
                type="task",
                payload={**base, "field_test_results_path": "phases/ship/field_test_results.md"},
                priority=1,
            )
        )
        return True
    if status == "field_test_passed":
        from pipeline.ship_config import skip_thermo_review

        agent = "ship_evaluator" if skip_thermo_review() else "thermo_reviewer"
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent=agent,
                type="task",
                payload=base,
            )
        )
        return True
    if status == "thermo_reviewing":
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="thermo_reviewer",
                type="task",
                payload=base,
            )
        )
        return True
    if status == "thermo_refactoring":
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="executor",
                type="task",
                payload={
                    **base,
                    "thermo_refactor": True,
                    "thermo_review_path": "phases/ship/thermo_review.md",
                    "workspace_path": str(project_dir / "workspace"),
                    "fix_required": True,
                    "error_summary": "Resume thermo refactor.",
                },
                priority=1,
            )
        )
        return True
    if status == "ship_evaluating":
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="ship_evaluator",
                type="task",
                payload=base,
            )
        )
        return True
    return False


def requeue_in_progress_ship_projects(
    bus: "MessageBus",
    *,
    slug_filter: str = "",
    skip_slugs: set[str] | None = None,
) -> int:
    """Resume ship-track projects that are mid-flight (not complete/terminal)."""
    root = projects_dir()
    if not root.is_dir():
        return 0
    skip = skip_slugs or set()
    requeued = 0
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
        if status in TERMINAL_SHIP_STATUSES or status == "complete":
            continue
        if not is_ship_status(status):
            continue
        if slug in skip and status == "field_test_planning":
            continue
        title = state.get("title", slug)
        if dispatch_ship_requeue(bus, slug, title, state, project_dir, status):
            print(f"  [ship-prove] Re-queued '{title}' ({status})")
            requeued += 1
    return requeued


def run_ship_prove_mode(
    bus: "MessageBus",
    *,
    slug_filter: str = "",
) -> int:
    """Entry for startup: queue complete projects and resume in-progress ship track."""
    n, fresh = queue_ship_prove_projects(bus, slug_filter=slug_filter)
    n += requeue_in_progress_ship_projects(bus, slug_filter=slug_filter, skip_slugs=fresh)
    deduped = bus.dedupe_pending_tasks("field_test_planner", ("idea_slug",))
    if deduped:
        print(f"  [ship-prove] Deduped {deduped} duplicate field_test_planner task(s)")
    return n
