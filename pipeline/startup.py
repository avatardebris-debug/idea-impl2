"""
pipeline/startup.py
Resolve initial work before the main agent loop starts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.pipeline_config import AGENT_ROLES, PROJECT_ROOT, get_pipeline_dir
from pipeline.slug_util import slugify_title as _slugify
from pipeline.seeding import (
    SEED_BLOCKED,
    SEED_SEEDED,
    _purge_dep_blocked_messages,
    _seeded_this_session,
    check_resume,
    seed_from_master_list,
    seed_idea,
)
from pipeline.project_ops import _rebuild_queues_from_state
from pipeline.project_rebuild import advance_reviewed_projects

if TYPE_CHECKING:
    from pipeline.message_bus import MessageBus
    from pipeline.run_context import RunContext


@dataclass
class StartupResult:
    has_work: bool
    from_list: bool
    stop_early: bool = False
    focus_slug: str | None = None


def resolve_initial_work(
    bus: "MessageBus",
    *,
    run_ctx: "RunContext | None",
    ideas_path: Path,
    idea: str | None,
    from_list: bool,
    resume: bool,
    polish: bool,
    ship_prove: bool = False,
    ship_slug: str = "",
    ship_serial: bool = False,
    fresh_list_only: bool,
    parallel_seeds: int,
    save_pipeline_status,
) -> StartupResult:
    """Polish/resume/seed startup; returns whether agents should run."""
    has_work = False
    stop_early = False

    stale = bus.reset_stale_processing()
    if stale:
        print(f"  🔄 Reset {stale} stale message(s) from previous run")

    shutdowns = bus.discard_stale_shutdowns()
    if shutdowns:
        print(f"  🧹 Discarded {shutdowns} stale SHUTDOWN signal(s) from prior run")

    deduped = bus.dedupe_pending_tasks("phase_planner", ("idea_slug",))
    deduped += bus.dedupe_pending_tasks("reviewer", ("idea_slug", "phase"))
    deduped += bus.dedupe_pending_tasks("executor", ("idea_slug", "phase"))
    if deduped:
        print(f"  🧹 Deduped {deduped} duplicate task message(s) in queue")

    if not ship_prove:
        advanced = advance_reviewed_projects(bus)
        if advanced:
            print(f"  ➡️  Advanced {advanced} project(s) from phase_X_reviewed")

    if polish and run_ctx and run_ctx.polish_path:
        from pipeline.polish_mode import queue_pending, requeue_polish_in_progress, run_polish_mode
        from pipeline.polish_status import print_polish_lifecycle, save_polish_status

        print(f"  Polish:   {run_ctx.polish_path}")
        n = run_polish_mode(bus, run_ctx.polish_path, _seeded_this_session)
        if n == 0:
            n = requeue_polish_in_progress(bus, run_ctx.polish_path, _seeded_this_session)
        pending = queue_pending(bus)
        if n == 0 and not bus.has_active_work():
            print_polish_lifecycle(
                "terminated",
                reason="no qualifying polish entries (all SKIP or missing state)",
                queued=0,
                queue_path=str(run_ctx.polish_path),
            )
            save_pipeline_status({
                "status": "stopped",
                "run_mode": "polish",
                "stopped_at": datetime.now(timezone.utc).isoformat(),
                "reason": "polish_nothing_to_do",
            })
            print("  [polish] In-flight polish work: re-run with --resume, or regenerate the queue:")
            print("           python pipeline/runner.py --polish --resume --provider ollama --model <model>")
            print("           python reset_budget_exceeded.py --generate-polish")
            return StartupResult(has_work=False, from_list=from_list, stop_early=True)

        has_work = True
        from_list = True
        print_polish_lifecycle(
            "running",
            reason="startup",
            queued=n,
            queue_path=str(run_ctx.polish_path),
            pending_messages=pending,
        )

    if ship_prove:
        from pipeline.pipeline_config import SHIP_AGENT_ROLES
        from pipeline.ship_mode import run_ship_prove_mode, ship_bus_has_work

        queue_limit = 1 if ship_serial and not ship_slug else 0
        n = run_ship_prove_mode(bus, slug_filter=ship_slug, queue_limit=queue_limit)
        pending = sum(bus.queue_depth(r) for r in SHIP_AGENT_ROLES)
        if n == 0 and pending == 0 and not ship_bus_has_work(bus):
            print("  [ship-prove] No complete projects eligible for field testing.")
            return StartupResult(has_work=False, from_list=False, stop_early=True)
        has_work = True
        from_list = False
        mode = "serial" if queue_limit == 1 else "batch"
        print(f"  [ship-prove] Queued {n} project(s) ({mode}); pending ship messages={pending}")

    purged = _purge_dep_blocked_messages(bus)
    if purged:
        print(f"  🚫 Purged {purged} dep-blocked queue(s) — will resume when deps complete")

    if fresh_list_only:
        cleared_total = 0
        for role in AGENT_ROLES:
            cleared_total += bus.clear_queue(role)
        if cleared_total:
            print(f"  🧹 Cleared {cleared_total} stale queue message(s) (fresh-list-only mode)")

    if resume:
        from_list = True
        has_work = check_resume(bus)
        if not has_work:
            rebuilt = _rebuild_queues_from_state(bus)
            if rebuilt:
                print(f"  🔄 Rebuilt queues for {rebuilt} project(s) from saved state")
                has_work = True
            else:
                print("  No active pipeline to resume.")

    focus_slug: str | None = None
    if idea:
        title = idea.split(".")[0][:50].strip()
        if not title:
            print("  ✗ Idea text is empty — provide a description after --seed-idea or as positional arg.")
            return StartupResult(has_work=False, from_list=from_list, stop_early=True)
        focus_slug = _slugify(title)
        seed_idea(bus, title, idea)
        purged = bus.purge_tasks_not_matching_slug(focus_slug)
        if purged:
            print(f"  🎯 Single-idea mode — cleared {purged} queued message(s) for other projects")
        has_work = True

    # --polish only replays polish_queue.md; never seed master_ideas / --goal / --hermes.
    if not polish and not ship_prove and not has_work and from_list:
        if not fresh_list_only:
            rebuilt = _rebuild_queues_from_state(bus, ideas_path=ideas_path)
            if rebuilt:
                print(f"  🔄 Rebuilt queues for {rebuilt} project(s) from saved state")
                has_work = True
        if not has_work:
            seed_result = seed_from_master_list(
                bus,
                ideas_path=ideas_path,
                resume_inprogress=fresh_list_only,
                run_ctx=run_ctx,
            )
            has_work = seed_result in (SEED_SEEDED, SEED_BLOCKED)

    if not polish and not ship_prove and has_work and from_list and parallel_seeds > 1:
        from pipeline.pipeline_status import _get_all_active_idea_states

        already_active = len(_get_all_active_idea_states(get_pipeline_dir()))
        queued_now = len(_seeded_this_session)
        effective_active = max(already_active, queued_now)
        slots_to_fill = max(0, parallel_seeds - effective_active)
        if slots_to_fill > 0:
            print(f"  🌱 Pre-seeding {slots_to_fill} additional parallel slot(s)...")
            for _ in range(slots_to_fill):
                sr = seed_from_master_list(
                    bus,
                    ideas_path=ideas_path,
                    resume_inprogress=fresh_list_only,
                    run_ctx=run_ctx,
                )
                if sr != SEED_SEEDED:
                    break

    if not has_work and not fresh_list_only and not ship_prove and bus.has_active_work():
        pending_total = sum(bus.queue_depth(r) for r in AGENT_ROLES)
        print(f"  🔄 Found {pending_total} pending queue message(s) — starting agents")
        has_work = True

    return StartupResult(
        has_work=has_work,
        from_list=from_list,
        stop_early=stop_early,
        focus_slug=focus_slug,
    )
