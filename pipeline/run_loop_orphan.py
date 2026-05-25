"""
pipeline/run_loop_orphan.py
Orphan requeue tick and zero-task stall kills.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pipeline.pipeline_config import AGENT_ROLES, PIPELINE_DIR
from pipeline.project_ops import _rebuild_queues_from_state

from pipeline.run_loop_types import MainLoopConfig


def tick_orphan_requeue(cfg: MainLoopConfig) -> int:
    """Re-queue orphaned projects when idle; returns count re-queued."""
    now = time.time()
    if now - cfg.state.last_orphan_requeue < cfg.orphan_requeue_cooldown_s:
        return 0
    orphaned = 0 if cfg.fresh_list_only else _rebuild_queues_from_state(cfg.bus)
    if orphaned:
        cfg.state.last_orphan_requeue = now
        print(f"  🔁 Re-queued {orphaned} orphaned project(s) — not seeding new ideas yet")
    return orphaned


def tick_zero_task_stall_kill(
    cfg: MainLoopConfig,
    idea_state: dict[str, Any],
    *,
    tasks_done: int,
    tasks_total: int,
    ws_file_count: int,
    ws_last_mtime: float,
) -> None:
    """Kill executing phases stuck at 0/N tasks with no recent workspace writes."""
    _active_slug = idea_state.get("_slug", "")
    _zpk = f"{_active_slug}:{idea_state.get('phase', 1)}"
    _is_locked = idea_state.get("budget_lock", False)
    if not (
        tasks_total > 0
        and tasks_done == 0
        and "executing" in idea_state.get("status", "")
        and _active_slug
        and not _is_locked
        and idea_state.get("status", "") not in ("complete", "budget_exceeded")
    ):
        cfg.state.zero_progress_since.pop(_zpk, None)
        cfg.state.zero_task_warned.discard(_zpk)
        return

    _ACTIVITY_WINDOW = 8 * 60
    _ws_active = ws_last_mtime > 0 and (time.time() - ws_last_mtime) < _ACTIVITY_WINDOW
    if _ws_active:
        cfg.state.zero_progress_since.pop(_zpk, None)
        cfg.state.zero_task_warned.discard(_zpk)
        return

    if _zpk not in cfg.state.zero_progress_since:
        cfg.state.zero_progress_since[_zpk] = time.time()
        return

    _stall_secs = time.time() - cfg.state.zero_progress_since[_zpk]
    if _stall_secs > cfg.zero_task_warn_s and _zpk not in cfg.state.zero_task_warned:
        cfg.state.zero_task_warned.add(_zpk)
        print(
            f"  ⚠️  Zero-task stall: '{idea_state.get('title', _active_slug)}' "
            f"phase {idea_state.get('phase', 1)} — "
            f"0/{tasks_total} tasks for {int(_stall_secs // 60)}m, "
            f"{ws_file_count} workspace file(s), "
            f"last write {int((time.time() - ws_last_mtime) // 60) if ws_last_mtime else '?'}m ago "
            f"(kill in {(cfg.zero_task_phase_kill_s - _stall_secs) // 60:.0f}m)"
        )
    if _stall_secs > cfg.zero_task_phase_kill_s:
        _proj_file = PIPELINE_DIR / "projects" / _active_slug / "state" / "current_idea.json"
        try:
            _st = json.loads(_proj_file.read_text(encoding="utf-8"))
            if _st.get("status", "") not in ("complete", "budget_exceeded"):
                _st["status"] = "budget_exceeded"
                _st["budget_note"] = (
                    f"Phase {idea_state.get('phase', 1)} stuck: "
                    f"0/{tasks_total} tasks after {cfg.zero_task_phase_kill_s // 60}m"
                )
                _proj_file.write_text(json.dumps(_st, indent=2), encoding="utf-8")
                print(
                    f"  ⏰ Zero-task timeout: '{idea_state.get('title', _active_slug)}' "
                    f"phase {idea_state.get('phase', 1)} — "
                    f"0/{tasks_total} tasks in {cfg.zero_task_phase_kill_s // 60}m → budget_exceeded"
                )
                for _role in AGENT_ROLES:
                    cfg.bus.clear_queue(_role)
        except Exception:
            pass
        cfg.state.zero_progress_since.pop(_zpk, None)
        cfg.state.zero_task_warned.discard(_zpk)
