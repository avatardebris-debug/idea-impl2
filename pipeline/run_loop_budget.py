"""
pipeline/run_loop_budget.py
Per-session time budget enforcement for the active project.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pipeline.pipeline_config import AGENT_ROLES

from pipeline.run_loop_types import MainLoopConfig


def tick_budget_enforcement(cfg: MainLoopConfig, idea_state: dict[str, Any]) -> dict[str, Any]:
    """Enforce per-session time budget; may mutate idea_state and project file."""
    _active_slug = idea_state.get("_slug", "")
    _active_status_for_budget = idea_state.get("status", "")
    _active_started = idea_state.get("session_started_at", "")
    if (
        _active_slug
        and _active_status_for_budget not in ("", "complete", "budget_exceeded")
        and not _active_started
    ):
        _active_started = datetime.now(timezone.utc).isoformat()
        idea_state["session_started_at"] = _active_started
        _stamp_file = cfg.pipeline_dir / "projects" / _active_slug / "state" / "current_idea.json"
        try:
            _stamp_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
        except Exception:
            pass
    if (
        _active_slug
        and _active_started
        and _active_status_for_budget not in ("", "complete", "budget_exceeded")
    ):
        _is_locked = idea_state.get("budget_lock", False)
        try:
            _start = datetime.fromisoformat(_active_started)
            _elapsed = (datetime.now(timezone.utc) - _start).total_seconds() / 60

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

            if _elapsed > _phase_budget and not _is_locked:
                _proj_file = cfg.pipeline_dir / "projects" / _active_slug / "state" / "current_idea.json"
                idea_state["pre_budget_status"] = idea_state.get("status", "phase_1_executing")
                idea_state["status"] = "budget_exceeded"
                idea_state["budget_note"] = (
                    f"Force-completed after {_elapsed:.0f} min "
                    f"(budget: {_phase_budget} min for {_total_phases}-phase project)"
                )
                _proj_file.write_text(json.dumps(idea_state, indent=2), encoding="utf-8")
                print(
                    f"  Budget exceeded for '{idea_state.get('title', _active_slug)}' "
                    f"({_elapsed:.0f}m > {_phase_budget}m [{_total_phases} phases]) -- skipping"
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
                        f"over budget ({_elapsed:.0f}m) but lock prevents skip"
                    )
        except Exception as _budget_err:
            print(f"  [budget] Enforcement failed for '{_active_slug}': {_budget_err}")
    return idea_state
