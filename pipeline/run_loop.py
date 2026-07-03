"""
pipeline/run_loop.py
Main pipeline monitoring loop (extracted from runner.py).
"""

from __future__ import annotations

import time

from pipeline.pipeline_status import _get_active_idea_state
from pipeline.pipeline_config import SHIP_AGENT_ROLES
from pipeline.project_state import _check_priority_eviction
from pipeline.run_loop_budget import tick_budget_enforcement
from pipeline.run_loop_health import (
    check_single_idea_complete,
    read_task_progress,
    read_workspace_activity,
    tick_health_preamble,
    tick_project_metrics,
    tick_reviewed_advance,
    tick_stall_recovery,
    tick_status_display,
)
from pipeline.run_loop_orphan import tick_orphan_requeue, tick_zero_task_stall_kill
from pipeline.run_loop_seed_idle import tick_seed_after_project_advance, tick_seed_idle_when_empty
from pipeline.run_loop_types import LoopControl, MainLoopConfig, MainLoopState

__all__ = [
    "LoopControl",
    "MainLoopConfig",
    "MainLoopState",
    "run_main_loop",
]


def _tick_dropbox(cfg: MainLoopConfig) -> None:
    if cfg.ship_prove:
        return
    if time.time() - cfg.state.last_dropbox_check < cfg.dropbox_interval_s:
        return
    try:
        from pipeline.dropbox import check_dropbox, ensure_dropbox

        ensure_dropbox()
        _dn = check_dropbox(cfg.bus, cfg.ideas_path)
        if _dn:
            print(f"  [dropbox] Queued {_dn} user message(s) for manager")
    except Exception as _db_err:
        print(f"  [dropbox] check failed: {_db_err}")
    cfg.state.last_dropbox_check = time.time()


def _tick_eviction(cfg: MainLoopConfig) -> None:
    if cfg.ship_prove:
        return
    try:
        _check_priority_eviction(cfg.bus, cfg.state.parallel_seeds, ideas_path=cfg.ideas_path)
    except Exception as _ee:
        print(f"  [eviction] Controller error: {_ee}")


def _tick_time_limit(cfg: MainLoopConfig) -> bool:
    """Return True if the run should stop due to time limit."""
    if cfg.time_limit_minutes <= 0:
        return False
    elapsed = (time.time() - cfg.start_time) / 60
    if elapsed >= cfg.time_limit_minutes:
        print(f"\n  ⏰ Time limit reached ({cfg.time_limit_minutes:.0f} min)")
        return True
    return False


def _tick_health_cycle(cfg: MainLoopConfig) -> bool:
    """One health-check cycle. Return True to break the main loop."""
    health = tick_health_preamble(cfg)
    if cfg.ship_prove:
        all_empty = all(cfg.bus.queue_depth(r) == 0 for r in SHIP_AGENT_ROLES)
    else:
        all_empty = cfg.bus.all_queues_empty()

    focus = cfg.focus_slug
    if cfg.ship_prove and cfg.ship_slug and not focus:
        focus = cfg.ship_slug
    idea_state = _get_active_idea_state(cfg.pipeline_dir, preferred_slug=focus)

    if not cfg.ship_prove:
        idea_state = tick_budget_enforcement(cfg, idea_state)
        idea_state = tick_reviewed_advance(cfg, idea_state, all_empty)
        tick_seed_after_project_advance(cfg, idea_state)

    tasks_done, tasks_total = read_task_progress(cfg, idea_state)
    _active_slug = idea_state.get("_slug", "")
    ws_file_count, ws_last_mtime = read_workspace_activity(cfg, _active_slug)

    tick_status_display(
        cfg,
        health,
        idea_state,
        tasks_done=tasks_done,
        tasks_total=tasks_total,
        ws_file_count=ws_file_count,
    )

    if not cfg.ship_prove:
        tick_zero_task_stall_kill(
            cfg,
            idea_state,
            tasks_done=tasks_done,
            tasks_total=tasks_total,
            ws_file_count=ws_file_count,
            ws_last_mtime=ws_last_mtime,
        )

    if check_single_idea_complete(cfg, all_empty):
        return True

    if not cfg.ship_prove and all_empty and cfg.from_list and not cfg.bus.has_active_work():
        orphaned = tick_orphan_requeue(cfg)
        tick_seed_idle_when_empty(cfg, all_empty, orphaned=orphaned)

    tick_project_metrics(cfg, idea_state, tasks_done=tasks_done)
    tick_stall_recovery(cfg, running_agents=sum(1 for s in health.values() if s == "running"))
    cfg.state.last_health_check = time.time()
    return False


def run_main_loop(cfg: MainLoopConfig) -> None:
    while not cfg.control.stop_requested:
        _tick_dropbox(cfg)
        _tick_eviction(cfg)
        if _tick_time_limit(cfg):
            break

        if time.time() - cfg.state.last_health_check >= cfg.health_check_interval:
            if _tick_health_cycle(cfg):
                break

        time.sleep(2)
