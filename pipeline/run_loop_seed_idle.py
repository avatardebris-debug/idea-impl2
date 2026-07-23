"""
pipeline/run_loop_seed_idle.py
Empty-queue seeding, ideation, and polish idle handling.
"""

from __future__ import annotations

import json
import os
import pathlib
import threading
import time
from typing import Any

from pipeline.pipeline_config import PROJECT_ROOT
from pipeline.project_ops import _rebuild_queues_from_state
from pipeline.seeding import SEED_EMPTY, SEED_SEEDED, _seeded_this_session, seed_from_master_list
from pipeline.seed_policy import apply_seed_empty as _apply_seed_empty

from pipeline.run_loop_types import MainLoopConfig


def polish_first_enabled() -> bool:
    from pipeline.env_flags import env_bool
    return env_bool("PIPELINE_POLISH_FIRST", default=False)


def _resolve_polish_path(cfg: MainLoopConfig) -> pathlib.Path:
    if cfg.run_ctx and getattr(cfg.run_ctx, "polish_path", None):
        return pathlib.Path(cfg.run_ctx.polish_path)
    return PROJECT_ROOT / "polish_queue.md"


def _try_polish_first(cfg: MainLoopConfig) -> int:
    """If PIPELINE_POLISH_FIRST=1, queue polish work before greenfield seeds. Returns count."""
    if not polish_first_enabled() or cfg.polish:
        return 0
    if cfg.bus.has_active_work():
        return 0
    from pipeline.pipeline_activity import log_activity
    from pipeline.polish_mode import run_polish_mode

    path = _resolve_polish_path(cfg)
    if not path.exists():
        return 0
    n = run_polish_mode(cfg.bus, path, _seeded_this_session)
    if n:
        print(f"  [polish-first] Re-queued {n} project(s) from {path.name}")
        log_activity("polish_first", queued=n, path=str(path))
    return n


def tick_seed_after_project_advance(cfg: MainLoopConfig, idea_state: dict[str, Any]) -> None:
    """When active project is terminal/polishable (incl. budget_exceeded), advance and seed."""
    from pipeline.dep_policy import is_polishable, is_build_terminal

    status = idea_state.get("status", "")
    # budget_exceeded / deeper_work_needed / field_proven / etc. → free the slot
    if not (is_polishable(status) or is_build_terminal(status)):
        return
    # dep_waiting is terminal for build but not "done advancing" for seed focus
    if status == "dep_waiting":
        return
    slug = idea_state.get("_slug", "")
    orphaned = _rebuild_queues_from_state(cfg.bus)
    if orphaned:
        print(f"  ▶️  Advancing past '{slug}' → {orphaned} project(s) queued")
    if cfg.polish and cfg.run_ctx and cfg.run_ctx.polish_path and not cfg.bus.has_active_work():
        from pipeline.polish_mode import run_polish_mode

        _pq = run_polish_mode(cfg.bus, cfg.run_ctx.polish_path, _seeded_this_session)
        if _pq:
            print(f"  [polish] Re-queued {_pq} project(s) from polish_queue.md")
    elif cfg.from_list and not cfg.polish and not cfg.bus.has_active_work():
        if _try_polish_first(cfg):
            return
        _count = cfg.count_active_projects
        active_now = _count() if _count else 0
        slots_free = max(0, cfg.state.parallel_seeds - active_now)
        if slots_free <= 0:
            return
        for _seed_i in range(slots_free):
            seeded = seed_from_master_list(
                cfg.bus,
                silent=cfg.state.ideation_in_progress,
                ideas_path=cfg.ideas_path,
                resume_inprogress=cfg.fresh_list_only,
                run_ctx=cfg.run_ctx,
                max_active=cfg.state.parallel_seeds,
            )
            if seeded == SEED_SEEDED:
                cfg.state.ideation_in_progress = False
                cfg.state.ideation_requested_at = 0.0
                if cfg.state.parallel_seeds > 1:
                    threading.Thread(
                        target=cfg.warm_upcoming_projects,
                        args=(cfg.state.parallel_seeds,),
                        daemon=True,
                        name="env-pool-refill",
                    ).start()
            elif seeded == SEED_EMPTY:
                (
                    cfg.state.ideation_in_progress,
                    cfg.state.ideation_requested_at,
                    _stop,
                ) = _apply_seed_empty(
                    seeded,
                    cfg.bus,
                    cfg.run_ctx,
                    ideation_in_progress=cfg.state.ideation_in_progress,
                    ideation_requested_at=cfg.state.ideation_requested_at,
                    ideation_timeout_s=cfg.ideation_timeout_s,
                )
                if _stop:
                    cfg.control.stop_requested = True
                break
            else:
                break
    elif cfg.from_list and not cfg.polish and not orphaned:
        seed_from_master_list(
            cfg.bus,
            silent=True,
            ideas_path=cfg.ideas_path,
            resume_inprogress=cfg.fresh_list_only,
            run_ctx=cfg.run_ctx,
        )


def _any_project_recently_working(pipeline_dir: pathlib.Path) -> bool:
    """True if any project has a working-state status modified in the last 15 min.

    Ship-only statuses (field_testing, etc.) do NOT count — an idle field_testing
    project with empty queues must not block seeding forever (overnight stall).
    """
    _working_states = ("_executing", "_validating", "_reviewing", "_planning", "_grok_running")
    _recency_cutoff = time.time() - 900
    _projects_dir = pipeline_dir / "projects"
    if not _projects_dir.exists():
        return False
    for _pd in _projects_dir.iterdir():
        _sf = _pd / "state" / "current_idea.json"
        if not _sf.exists():
            continue
        try:
            if os.path.getmtime(str(_sf)) < _recency_cutoff:
                continue
            _st = json.loads(_sf.read_text(encoding="utf-8"))
            _ss = _st.get("status", "")
            # field_testing / ship track alone is not "working" for seed-block
            if _ss.startswith("field_") or _ss in (
                "thermo_reviewing",
                "thermo_refactoring",
                "ship_evaluating",
                "ship_insufficient",
            ):
                continue
            if any(_ss.endswith(ws) for ws in _working_states):
                return True
        except Exception:
            pass
    return False


def tick_park_idle_ship_inflight(cfg: MainLoopConfig) -> int:
    """Park field_testing (etc.) stuck with empty queues into deeper_work_needed.

    Overnight failure mode: orphan re-queue keeps a ship status project "active"
    while no LLM work runs for hours. After FIELD_IDLE_PARK_MINUTES (default 20)
    of no LLM call + empty bus, park so seed/advance can continue.
    """
    from pipeline.env_flags import env_bool
    from pipeline.field_rework_budget import (
        FIELD_REWORK_STATUSES,
        mark_deeper_work_needed,
        maybe_park_if_over_budget,
        write_state,
    )

    if cfg.ship_prove or not cfg.from_list:
        return 0
    if cfg.bus.has_active_work():
        return 0

    raw = (os.environ.get("FIELD_IDLE_PARK_MINUTES") or "20").strip()
    try:
        idle_min = max(5.0, float(raw))
    except ValueError:
        idle_min = 20.0

    # Prefer throughput last-LLM age; fall back to wall time since start
    age_s = None
    try:
        tp = cfg.pipeline_dir / "state" / "throughput.json"
        if tp.is_file():
            data = json.loads(tp.read_text(encoding="utf-8"))
            updated = data.get("updated_at")
            if updated is not None:
                age_s = time.time() - float(updated)
    except Exception:
        age_s = None
    if age_s is None:
        age_s = time.time() - cfg.start_time
    if age_s < idle_min * 60:
        return 0

    parked = 0
    projects = cfg.pipeline_dir / "projects"
    if not projects.is_dir():
        return 0
    for pd in sorted(projects.iterdir()):
        if not pd.is_dir():
            continue
        sf = pd / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            state = json.loads(sf.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        status = (state.get("status") or "").strip()
        if status not in FIELD_REWORK_STATUSES and status != "field_testing":
            continue
        # Over rework budget OR idle long enough with empty queues
        state2, over = maybe_park_if_over_budget(
            state,
            reason_prefix=f"idle ship status={status}",
            slug=pd.name,
            project_dir=pd,
        )
        if over:
            write_state(pd, state2)
            print(
                f"  [idle-park] '{pd.name}' → deeper_work_needed "
                f"(rework budget; was {status})",
                flush=True,
            )
            parked += 1
            continue
        # Idle park: long no-LLM + empty bus
        reason = (
            f"idle ship status={status}: no LLM ~{int(age_s // 60)}m "
            f"with empty queues (FIELD_IDLE_PARK_MINUTES={idle_min:.0f})"
        )
        state3 = mark_deeper_work_needed(
            state, reason=reason, slug=pd.name, project_dir=pd
        )
        write_state(pd, state3)
        print(
            f"  [idle-park] '{pd.name}' → deeper_work_needed ({reason[:100]})",
            flush=True,
        )
        parked += 1
    return parked


def tick_seed_idle_when_empty(cfg: MainLoopConfig, all_empty: bool, *, orphaned: int) -> None:
    """Seed or re-polish when all queues are empty but list mode is on (after orphan tick)."""
    if not all_empty or not cfg.from_list:
        return
    if _any_project_recently_working(cfg.pipeline_dir):
        return
    if not cfg.bus.has_active_work():
        if orphaned:
            return
        if cfg.polish and cfg.run_ctx and cfg.run_ctx.polish_path:
            from pipeline.polish_mode import run_polish_mode as _run_polish_mode

            _pq = _run_polish_mode(cfg.bus, cfg.run_ctx.polish_path, _seeded_this_session)
            if _pq:
                print(f"  [polish] Re-queued {_pq} project(s) from polish_queue.md")
        elif not cfg.polish:
            if _try_polish_first(cfg):
                return
            _count = cfg.count_active_projects
            active_now = _count() if _count else 0
            if active_now >= cfg.state.parallel_seeds:
                return
            seeded = seed_from_master_list(
                cfg.bus,
                silent=cfg.state.ideation_in_progress,
                ideas_path=cfg.ideas_path,
                resume_inprogress=cfg.fresh_list_only,
                run_ctx=cfg.run_ctx,
                max_active=cfg.state.parallel_seeds,
            )
            if seeded == SEED_SEEDED:
                cfg.state.ideation_in_progress = False
                cfg.state.ideation_requested_at = 0.0
            elif seeded == SEED_EMPTY:
                (
                    cfg.state.ideation_in_progress,
                    cfg.state.ideation_requested_at,
                    _stop,
                ) = _apply_seed_empty(
                    seeded,
                    cfg.bus,
                    cfg.run_ctx,
                    ideation_in_progress=cfg.state.ideation_in_progress,
                    ideation_requested_at=cfg.state.ideation_requested_at,
                    ideation_timeout_s=cfg.ideation_timeout_s,
                )
                if _stop:
                    cfg.control.stop_requested = True
