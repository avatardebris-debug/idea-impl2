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
    """When active project is complete/mvp/budget_exceeded, advance queues and seed/polish."""
    from pipeline.dep_policy import is_polishable

    if not is_polishable(idea_state.get("status", "")):
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
    """True if any project has a working-state status modified in the last 15 min."""
    _working_states = ("_executing", "_validating", "_reviewing", "_planning")
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
            if any(_ss.endswith(ws) for ws in _working_states):
                return True
        except Exception:
            pass
    return False


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
