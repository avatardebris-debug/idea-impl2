"""
pipeline/run_loop_budget.py
Per-session time budget enforcement for the active project.

Uses active-clock elapsed (budget_ladder) so laptop sleep / calendar gaps
do not force budget_exceeded.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pipeline.pipeline_config import AGENT_ROLES
from pipeline.ship_status import is_ship_status

from pipeline.run_loop_types import MainLoopConfig

_ACTIVE_WORKING_SUFFIXES = (
    "_executing",
    "_validating",
    "_reviewing",
    "_planning",
    "_grok_running",
)


def tick_budget_enforcement(cfg: MainLoopConfig, idea_state: dict[str, Any]) -> dict[str, Any]:
    """Enforce per-session time budget; may mutate idea_state and project file."""
    if cfg.ship_prove:
        return idea_state
    _active_slug = idea_state.get("_slug", "")
    _active_status_for_budget = idea_state.get("status", "")
    if is_ship_status(_active_status_for_budget):
        return idea_state
    if _active_status_for_budget in ("", "complete", "budget_exceeded", "field_proven"):
        return idea_state

    from pipeline.budget_ladder import (
        apply_budget_yield,
        effective_elapsed_minutes,
        maybe_refresh_stale_session,
        touch_active_work,
    )

    _proj_file = cfg.pipeline_dir / "projects" / _active_slug / "state" / "current_idea.json"
    _active_started = idea_state.get("session_started_at", "")

    # Stamp active work when status looks like real progress
    if any(str(_active_status_for_budget).endswith(s) for s in _ACTIVE_WORKING_SUFFIXES):
        idea_state = touch_active_work(idea_state)

    if _active_slug and not _active_started:
        _active_started = datetime.now(timezone.utc).isoformat()
        idea_state["session_started_at"] = _active_started
        idea_state = touch_active_work(idea_state)
        try:
            _proj_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
        except Exception:
            pass

    if not (_active_slug and idea_state.get("session_started_at")):
        return idea_state

    # Long idle wake: refresh session instead of charging calendar time
    idea_state, refreshed = maybe_refresh_stale_session(idea_state)
    if refreshed:
        print(
            f"  [budget] refreshed stale session for '{idea_state.get('title', _active_slug)}' "
            f"(idle gap — active clock)",
            flush=True,
        )
        try:
            _proj_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
        except Exception:
            pass
        return idea_state

    _is_locked = idea_state.get("budget_lock", False)
    try:
        _elapsed = effective_elapsed_minutes(idea_state)

        _total_phases = idea_state.get("total_phases", 3)
        _phase_budget = max(cfg.base_budget, int(_total_phases) * cfg.phase_budget)

        _current_phase = idea_state.get("phase", 1)
        _on_final_phase = (
            isinstance(_current_phase, int)
            and isinstance(_total_phases, int)
            and _current_phase >= _total_phases
        )
        if _on_final_phase:
            _phase_budget = int(_phase_budget * 1.5)
        # Optional extension grants from manager
        grants = int(idea_state.get("budget_extension_grants") or 0)
        if grants:
            _phase_budget = int(_phase_budget * (1.0 + 0.5 * grants))

        if _elapsed > _phase_budget and not _is_locked:
            idea_state = apply_budget_yield(
                idea_state,
                elapsed_min=_elapsed,
                phase_budget=float(_phase_budget),
                total_phases=int(_total_phases) if _total_phases else 3,
            )
            _proj_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
            print(
                f"  Budget yielded for '{idea_state.get('title', _active_slug)}' "
                f"({_elapsed:.0f}m active > {_phase_budget}m "
                f"[{_total_phases} phases] strike={idea_state.get('budget_strikes')}) -- skipping"
            )
            cleared = 0
            for _role in AGENT_ROLES:
                cleared += cfg.bus.clear_queue(_role)
            if cleared:
                print(f"  Cleared {cleared} queued message(s) for budget-exceeded project")
        elif _elapsed > _phase_budget and _is_locked:
            if int(_elapsed) % 30 < 2:
                print(
                    f"  🔒 [LOCKED] '{idea_state.get('title', _active_slug)}' "
                    f"over budget ({_elapsed:.0f}m active) but lock prevents skip"
                )
    except Exception as _budget_err:
        print(f"  [budget] Enforcement failed for '{_active_slug}': {_budget_err}")
    return idea_state
