"""
pipeline/project_tick.py
Deterministic tick after reviewer verdict.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pipeline.message_bus import Message, MessageBus
from pipeline.pipeline_config import (
    AGENT_ROLES,
    MAX_PHASE_RETRIES,
    MAX_PROJECT_LIFETIME_RETRIES,
    PROJECT_ROOT,
)
from pipeline.slug_util import slugify_title as _slugify
from pipeline.project_phase import (
    _advance_phase,
    _extract_shared_libs,
    _mark_complete,
)
from pipeline.project_state import (
    _append_polish,
    _increment_retries,
    _reset_retries,
    _write_state,
)

if TYPE_CHECKING:
    pass

# Maximum reviewer->executor round-trips per phase before force-advancing
# 5 attempts = ~25-35 min max per stuck phase (saves 40+ min vs old limit of 12)
MAX_PHASE_RETRIES = 5
MAX_PROJECT_LIFETIME_RETRIES = 80  # absolute cap: force budget_exceeded if a project exceeds this many total retries across ALL phases


def _tick_project(
    bus: MessageBus,
    project_dir: pathlib.Path,
    state: dict,
    phase_num: int,
    slug: str,
) -> bool:
    """Deterministic state machine tick for a reviewed project.

    Reads the reviewer's verdict from current_idea.json and routes:
    - 0 blocking bugs → advance to next phase (or complete)
    - Blocking bugs → send back to executor (up to MAX_PHASE_RETRIES)
    - Emergency (architectural issues) → re-plan the phase

    Returns True if a message was sent, False if nothing to do.
    """
    review = state.get("review_result", {})
    blocking_bugs = review.get("blocking_bugs", 0)
    if review.get("review_fail") and blocking_bugs <= 0:
        blocking_bugs = 1
    review_content = review.get("review_content_preview", "")
    non_blocking_notes = review.get("non_blocking_notes", "")
    tasks_path = review.get("tasks_path", f"phases/phase_{phase_num}/tasks.md")
    workspace_path = review.get("workspace_path", str(project_dir / "workspace"))
    review_path = review.get("review_path", f"phases/phase_{phase_num}/review.md")
    title = state.get("title", slug)

    # Sync checkbox counts into state for status display / honesty
    try:
        from pipeline.task_checkboxes import (
            format_open_tasks_message,
            phase_tasks_closed,
            stats_for_phase,
            sync_task_counts_to_state,
        )

        sync_task_counts_to_state(state, project_dir, phase_num)
    except Exception:
        phase_tasks_closed = None  # type: ignore
        stats_for_phase = None  # type: ignore
        format_open_tasks_message = None  # type: ignore

    # Check for emergency rework indicators
    rework_indicators = sum(1 for word in ["fundamental", "architectural",
                                            "completely wrong", "redesign",
                                            "start over", "rewrite"]
                            if word in review_content.lower())
    is_emergency = rework_indicators >= 3 or blocking_bugs > 5

    # Cap emergency reworks — after 2, fall through to normal fix path
    MAX_EMERGENCY_REWORKS = 2
    emergency_count = 0
    retries_file = project_dir / "state" / "phase_retries.json"
    if retries_file.exists():
        try:
            _rd = json.loads(retries_file.read_text(encoding="utf-8"))
            emergency_count = _rd.get(f"phase_{phase_num}_emergency", 0)
        except Exception:
            pass

    if is_emergency and emergency_count < MAX_EMERGENCY_REWORKS:
        # EMERGENCY REWORK — re-plan the phase with actual review content
        review_full_path = project_dir / review_path if review_path else None
        review_text = ""
        if review_full_path and review_full_path.exists():
            try:
                review_text = review_full_path.read_text(encoding="utf-8")[:4000]
            except Exception:
                pass

        # Read master plan section for this phase
        master_plan_section = ""
        mp_file = project_dir / "state" / "master_plan.md"
        if mp_file.exists():
            try:
                mp = mp_file.read_text(encoding="utf-8")
                m = re.search(rf"## Phase {phase_num}\b[^\n]*\n.*?(?=## Phase \d|$)",
                              mp, re.DOTALL | re.IGNORECASE)
                if m:
                    master_plan_section = m.group(0)[:2000]
            except Exception:
                pass

        bus.send(Message.create(
            from_agent="runner",
            to_agent="phase_planner",
            type="task",
            payload={
                "phase": phase_num,
                "phase_spec": (
                    f"REWORK REQUIRED for phase {phase_num} (attempt {emergency_count + 1}/{MAX_EMERGENCY_REWORKS}).\n\n"
                    f"## Original Phase Goal\n{master_plan_section}\n\n"
                    f"## Reviewer Feedback (fix these issues):\n{review_text}\n"
                ),
                "is_rework": True,
                "idea_slug": slug,
            },
            priority=0,
        ))
        # Track emergency count
        _rd = {}
        if retries_file.exists():
            try:
                _rd = json.loads(retries_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        _rd[f"phase_{phase_num}_emergency"] = emergency_count + 1
        retries_file.parent.mkdir(parents=True, exist_ok=True)
        retries_file.write_text(json.dumps(_rd, indent=2), encoding="utf-8")

        # Update status
        _write_state(project_dir, state, f"phase_{phase_num}_planning")
        print(f"  🚨 Emergency rework for '{title}' phase {phase_num} (attempt {emergency_count + 1}/{MAX_EMERGENCY_REWORKS})")
        return True

    elif is_emergency and emergency_count >= MAX_EMERGENCY_REWORKS:
        # Emergency cap hit — demote to normal fix path (blocking_bugs > 0 branch below)
        print(f"  ⚠️  Emergency cap hit for '{title}' phase {phase_num} — switching to incremental fix path")
        blocking_bugs = max(blocking_bugs, 1)  # ensure we enter the fix path

    # Task checkbox gate: never advance/complete with open - [ ] tasks
    tasks_closed = True
    task_stats = None
    if phase_tasks_closed is not None:
        try:
            tasks_closed = phase_tasks_closed(project_dir, phase_num)
            task_stats = stats_for_phase(project_dir, phase_num)
        except Exception:
            tasks_closed = True

    if not tasks_closed:
        # Treat open checkboxes as blocking work (even on review PASS)
        blocking_bugs = max(int(blocking_bugs or 0), 1)

    if blocking_bugs > 0:
        # Increment retry counter
        retries = _increment_retries(project_dir, phase_num)

        if retries >= MAX_PHASE_RETRIES and tasks_closed:
            # Too many retries — force-advance only if checkboxes are closed
            print(
                f"  ⚠️  Force-advancing '{title}' phase {phase_num} after {retries} "
                f"retries ({blocking_bugs} bugs remain)"
            )
            _reset_retries(project_dir, phase_num)
            state["quality_risk"] = True
            state["force_advanced"] = True
            advanced = _advance_phase(bus, project_dir, state, phase_num, slug)
            if not advanced:
                _mark_complete(project_dir, state, title)
                print(f"  ✅ '{title}' completed all phases (force-advanced past last phase)!")
            return True

        # Open tasks or review bugs → executor (no advance while [ ] remain)
        review_full = str(project_dir / review_path) if review_path else ""
        if not tasks_closed and task_stats is not None and format_open_tasks_message:
            open_msg = format_open_tasks_message(task_stats, phase=phase_num)
            fix_instructions = (
                f"TASK CHECKBOX GATE: {open_msg}\n"
                f"Finish remaining work, then mark each finished task `- [x]` in `{tasks_path}`. "
                f"Do NOT mark [x] unless the Done-when criteria are met. "
                f"Also address any blocking review bugs (attempt {retries}/{MAX_PHASE_RETRIES}). "
                f"Read `{review_full}` for review details."
            )
            print(
                f"  ☑️  '{title}' phase {phase_num}: open tasks → executor "
                f"(retry {retries}/{MAX_PHASE_RETRIES})"
            )
        else:
            fix_instructions = (
                f"Fix {blocking_bugs} blocking bugs from review "
                f"(attempt {retries}/{MAX_PHASE_RETRIES}). "
                f"Read `{review_full}` for details. "
                f"Mark completed tasks [x] in `{tasks_path}`."
            )
            print(
                f"  🔧 '{title}' phase {phase_num}: {blocking_bugs} bugs → executor "
                f"(retry {retries}/{MAX_PHASE_RETRIES})"
            )

        bus.send(Message.create(
            from_agent="runner",
            to_agent="executor",
            type="task",
            payload={
                "phase": phase_num,
                "tasks_path": tasks_path,
                "workspace_path": workspace_path,
                "fix_required": True,
                "review_path": review_path,
                "blocking_bugs": blocking_bugs,
                "open_tasks": not tasks_closed,
                "fix_instructions": fix_instructions,
                "idea_slug": slug,
            },
        ))
        _write_state(project_dir, state, f"phase_{phase_num}_executing")
        return True
    else:
        # Clean pass + all tasks closed — save non-blocking notes, advance or complete
        if non_blocking_notes:
            _append_polish(project_dir, phase_num, non_blocking_notes)

        # --- Extract reusable components from review (no LLM needed) ---
        _extract_shared_libs(project_dir, review_path, workspace_path, title)

        _reset_retries(project_dir, phase_num)

        advanced = _advance_phase(bus, project_dir, state, phase_num, slug)
        if not advanced:
            _mark_complete(project_dir, state, title)
            print(f"  ✅ '{title}' completed all phases!")
        else:
            print(f"  ➡️  '{title}' phase {phase_num} passed → advancing to phase {phase_num + 1}")

        return True
