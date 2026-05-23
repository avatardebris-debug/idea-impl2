"""
pipeline/project_rebuild.py
Rebuild queues from saved project state.
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
    PIPELINE_DIR,
    PROJECT_ROOT,
)
from pipeline.slug_util import slugify_title as _slugify
from pipeline.project_state import _write_state
from pipeline.project_tick import _tick_project

if TYPE_CHECKING:
    pass


def _rebuild_single_project(bus: MessageBus, slug: str, state: dict, project_dir: pathlib.Path) -> bool:
    """Re-queue one specific in-progress project. Returns True if queued."""
    status = state.get("status", "")
    title  = state.get("title", slug)

    if status in ("", "complete", "budget_exceeded", "dep_waiting"):
        return False

    # Reset session budget timer
    _now = datetime.now(timezone.utc).isoformat()
    state["session_started_at"] = _now
    state.pop("budget_note", None)
    state_file = project_dir / "state" / "current_idea.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    if status == "planning":
        bus.send(Message.create(from_agent="runner", to_agent="idea_planner", type="task",
            payload={"title": title, "idea": state.get("description", title), "idea_slug": slug}))
        return True

    if not status.startswith("phase_"):
        return False

    phase_match = re.match(r"phase_(\d+)_(\w+)", status)
    if not phase_match:
        return False
    phase_num  = int(phase_match.group(1))
    phase_step = phase_match.group(2)

    tasks_path     = f"phases/phase_{phase_num}/tasks.md"
    workspace_path = str(project_dir / "workspace")
    report_path    = f"phases/phase_{phase_num}/validation_report.md"
    review_path    = f"phases/phase_{phase_num}/review.md"

    if phase_step == "planning":
        master_plan_file = project_dir / "state" / "master_plan.md"
        phase_spec = f"Resume phase {phase_num} of {title}"
        if master_plan_file.exists():
            try:
                mp = master_plan_file.read_text(encoding="utf-8")
                m = re.search(rf"## Phase {phase_num}\b[^\n]*\n.*?(?=## Phase \d|$)", mp, re.DOTALL | re.IGNORECASE)
                if m:
                    phase_spec = m.group(0)[:3000]
            except Exception:
                pass
        bus.send(Message.create(from_agent="runner", to_agent="phase_planner", type="task",
            payload={"phase": phase_num, "phase_spec": phase_spec, "idea_slug": slug}))
    elif phase_step == "executing":
        tasks_file_path = project_dir / tasks_path
        if not tasks_file_path.exists():
            ph_spec = f"Phase {phase_num} of project {slug}"
            mp_file = project_dir / "state" / "master_plan.md"
            if mp_file.exists():
                try:
                    mp_txt = mp_file.read_text(encoding="utf-8")
                    pm = re.search(rf"## Phase {phase_num}\b.*?(?=## Phase \d|$)", mp_txt, re.DOTALL | re.IGNORECASE)
                    if pm:
                        ph_spec = pm.group(0)
                except Exception:
                    pass
            _write_state(project_dir, state, f"phase_{phase_num}_planning")
            bus.send(Message.create(from_agent="runner", to_agent="phase_planner", type="task",
                payload={"phase": phase_num, "phase_spec": ph_spec[:3000], "idea_slug": slug}))
        else:
            bus.send(Message.create(from_agent="runner", to_agent="executor", type="task",
                payload={"phase": phase_num, "tasks_path": tasks_path,
                         "workspace_path": workspace_path, "idea_slug": slug}))
    elif phase_step == "validating":
        existing_report = ""
        report_file = project_dir / report_path
        if report_file.exists():
            try:
                existing_report = report_file.read_text(encoding="utf-8")[:3000]
            except Exception:
                pass
        has_failures = existing_report and "Verdict: PASS" not in existing_report
        bus.send(Message.create(from_agent="runner", to_agent="validator", type="task",
            payload={"phase": phase_num, "tasks_path": tasks_path, "workspace_path": workspace_path,
                     "validation_report_path": report_path, "idea_slug": slug,
                     "fix_required": has_failures, "validation_report": existing_report if has_failures else "",
                     "error_summary": "Re-queued by runner — continue fixing failures." if has_failures else ""}))
    elif phase_step == "reviewing":
        bus.send(Message.create(from_agent="runner", to_agent="reviewer", type="task",
            payload={"phase": phase_num, "tasks_path": tasks_path, "workspace_path": workspace_path,
                     "validation_report_path": report_path, "review_path": review_path, "idea_slug": slug}))
    elif phase_step == "reviewed":
        return bool(_tick_project(bus, project_dir, state, phase_num, slug))
    else:
        return False

    return True


def _rebuild_queues_from_state(bus: MessageBus, ideas_path: pathlib.Path | None = None) -> int:
    """Re-inject a queue message for ONE in-progress project that has no queued work.

    Called at startup and during the health-check loop when queues appear empty.
    Re-queues ONE project at a time (matching seed_from_master_list behaviour)
    so the pipeline works serially through incomplete projects rather than
    dumping all of them into the queue at once.

    Also enforces a wall-clock budget per project — any project that has been
    running longer than PROJECT_TIME_BUDGET minutes is force-completed.

    Returns the number of projects re-queued (0 or 1).
    """
    if bus.has_active_work():
        return 0  # Queues are already populated — nothing to rebuild

    projects_dir = PIPELINE_DIR / "projects"
    if not projects_dir.exists():
        return 0

    # ----------------------------------------------------------------
    # PRE-PASS: Unblock ALL dep_waiting projects whose deps are done.
    # This must run before the main requeue loop because the main loop
    # returns after processing ONE project — if a more-recently-touched
    # project is first, dep_waiting projects never get evaluated.
    # ----------------------------------------------------------------
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
        state_file = project_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if state.get("status") != "dep_waiting":
            continue

        title = state.get("title", project_dir.name)
        deps = state.get("depends_on", [])

        # Re-parse deps from master_ideas.md (state may have stale deps from seed time)
        mi_path = ideas_path if ideas_path else PROJECT_ROOT / "master_ideas.md"
        if mi_path.exists():
            try:
                mi_text = mi_path.read_text(encoding="utf-8")
                _mi_title = state.get("title", "")
                if _mi_title:
                    for mi_line in mi_text.splitlines():
                        if _mi_title.strip("[]") in mi_line:
                            _dm = re.search(r'\brequires:\s*([\w,\s_-]+?)[\]\s.]*$', mi_line, re.IGNORECASE)
                            if _dm:
                                fresh_deps = [d.strip() for d in re.split(r'[,;]+', _dm.group(1)) if d.strip()]
                                if set(fresh_deps) != set(deps):
                                    print(f"  🔄 Updated deps for '{title}': {deps} → {fresh_deps}")
                                    deps = fresh_deps
                                    state["depends_on"] = deps
                            break
            except Exception:
                pass

        DONE = ("complete",)  # budget_exceeded does NOT satisfy a dep — the
        # prereq must have actually finished. If it only hit budget, the dependent
        # project stays blocked and waits for the prereq to be retried.
        still_blocked = [
            d for d in deps
            if not (projects_dir / d / "state" / "current_idea.json").exists()
            or (
                (projects_dir / d / "state" / "current_idea.json").exists()
                and json.loads((projects_dir / d / "state" / "current_idea.json")
                              .read_text(encoding="utf-8")).get("status") not in DONE
            )
        ]
        if still_blocked:
            continue  # still waiting

        # All deps done — restore last real phase status
        new_status = state.get("pre_dep_status", "phase_1_executing")
        state["status"] = new_status
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(f"  ✅ '{title}' deps satisfied — resuming from {new_status}")

    # ----------------------------------------------------------------
    # MAIN LOOP: Find the most-recently-active incomplete project and
    # requeue it. Only ONE project at a time.
    # ----------------------------------------------------------------
    injected = 0
    def _project_recency(d: pathlib.Path) -> float:
        sf = d / "state" / "current_idea.json"
        try:
            s = json.loads(sf.read_text(encoding="utf-8"))
            return -datetime.fromisoformat(s.get("started_at", "2000-01-01T00:00:00+00:00")).timestamp()
        except Exception:
            return 0.0
    for project_dir in sorted(projects_dir.iterdir(), key=_project_recency):
        if not project_dir.is_dir():
            continue

        state_file = project_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        status = state.get("status", "")
        title  = state.get("title", project_dir.name)
        slug   = project_dir.name

        if status == "evicted":
            pre_status = state.get("pre_evict_status", "phase_1_executing")
            print(f"  [rebuilt] Restoring evicted project '{title}' status: evicted -> {pre_status}")
            state["status"] = pre_status
            state["evict_requested"] = False
            state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            status = pre_status

        if status in ("", "complete", "budget_exceeded", "dep_waiting"):
            continue

        # --- Budget enforcement: ALWAYS reset session_started_at on requeue ---
        # This is a NEW runner session — any stale session_started_at from a
        # previous run would cause instant budget_exceeded (e.g. 5000+ min elapsed).
        state["session_started_at"] = datetime.now(timezone.utc).isoformat()
        # Also set started_at if missing (legacy projects)
        if not state.get("started_at"):
            state["started_at"] = state["session_started_at"]
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


        # Skip projects whose validator has already hit the stall limit —
        # these should have been force-advanced by the manager, but if the
        # manager message was lost, don't loop forever on the same project.
        retries_file = project_dir / "state" / "phase_retries.json"
        if retries_file.exists():
            try:
                retries = json.loads(retries_file.read_text(encoding="utf-8"))
                # Check for any no_progress streak >= 4 (our stall limit)
                # BUT respect budget_lock: locked projects are never force-completed
                _is_locked = state.get("budget_lock", False)
                for k, v in retries.items():
                    if "no_progress" in k and isinstance(v, int) and v >= 4 and not _is_locked:
                        # Force-mark as budget_exceeded (NOT complete) so [lock] can recover it
                        state["status"] = "budget_exceeded"
                        state["budget_note"] = f"Stalled: no_progress streak {v} cycles on {k}"
                        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
                        print(f"  ⏭️  Stall-stopped project '{title}' (stuck {v} cycles) → budget_exceeded")
                        break
                else:
                    retries = None  # didn't break — not stalled
                if state.get("status") == "budget_exceeded":
                    continue
            except Exception:
                pass

        # --- Dependency check: don't re-queue if deps aren't done yet ---
        depends_on = state.get("depends_on", [])
        if depends_on:
            dep_blocked = []
            DONE_STATUSES = ("complete",)  # budget_exceeded is NOT a satisfied dep
            for dep_slug in depends_on:
                dep_file = projects_dir / dep_slug / "state" / "current_idea.json"
                if not dep_file.exists():
                    dep_blocked.append(f"{dep_slug} (not started)")
                    continue
                try:
                    dep_st = json.loads(dep_file.read_text(encoding="utf-8"))
                    if dep_st.get("status") not in DONE_STATUSES:
                        dep_blocked.append(f"{dep_slug} ({dep_st.get('status','?')})")
                except Exception:
                    dep_blocked.append(f"{dep_slug} (unreadable)")
            if dep_blocked:
                print(f"  ⏸  '{title}' dep_waiting — blocked by: {', '.join(dep_blocked)}")
                continue  # don't re-queue until deps are finished

        phase_match = re.match(r"phase_(\d+)_(\w+)", status)
        if phase_match:
            phase_num  = int(phase_match.group(1))
            phase_step = phase_match.group(2)

            # --- Retroactive format normalization ---
            # Normalize task formatting for backward compatibility (## Task N: → - [ ] Task N:)
            # NOTE: no longer trims oversized tasks — the phase_planner handles overflow
            # with the planner-chooses system (restructure/split/trim).
            tasks_file = project_dir / f"phases/phase_{phase_num}/tasks.md"
            if tasks_file.exists():
                try:
                    from pipeline.agent_process import AgentProcess
                    AgentProcess.normalize_tasks_file(tasks_file)
                except Exception:
                    pass


        # Always refresh timestamps when re-queuing — budget is per-session,
        # not total project lifetime. Without this, a manually-reset project
        # or one from a previous session fires budget_exceeded immediately.
        _now = datetime.now(timezone.utc).isoformat()
        state["started_at"] = _now
        state["session_started_at"] = _now  # MUST also reset this — budget enforcement reads it first
        state.pop("budget_note", None)
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        if status == "planning":
            # Was in initial idea planning — restart from idea_planner
            msg = Message.create(
                from_agent="runner",
                to_agent="idea_planner",
                type="task",
                payload={
                    "title": title,
                    "idea": state.get("description", title),
                    "idea_slug": slug,
                },
            )
            bus.send(msg)
            injected += 1
            print(f"  [re-queue] Re-queued '{title}' -> idea_planner (was: planning)")
            continue
        elif not status.startswith("phase_"):
            continue  # Unknown status — skip


        tasks_path     = f"phases/phase_{phase_num}/tasks.md"
        workspace_path = str(project_dir / "workspace")
        report_path    = f"phases/phase_{phase_num}/validation_report.md"
        review_path    = f"phases/phase_{phase_num}/review.md"

        # Route to the correct agent based on phase step
        if phase_step == "planning":
            # phase_planner was building the task list — extract specific phase section
            master_plan_file = project_dir / "state" / "master_plan.md"
            phase_spec = f"Resume phase {phase_num} of {title}"
            if master_plan_file.exists():
                try:
                    mp = master_plan_file.read_text(encoding="utf-8")
                    m = re.search(rf"## Phase {phase_num}\b[^\n]*\n.*?(?=## Phase \d|$)",
                                  mp, re.DOTALL | re.IGNORECASE)
                    if m:
                        phase_spec = m.group(0)[:3000]
                except Exception:
                    pass
            agent    = "phase_planner"
            payload  = {"phase": phase_num, "phase_spec": phase_spec, "idea_slug": slug}
        elif phase_step == "executing":
            # Don't re-queue if workspace files were written in last 10 min —
            # the executor may still be mid-run (acked msg but writing files).
            workspace_dir = project_dir / "workspace"
            recently_active = False
            if workspace_dir.exists():
                cutoff = time.time() - 600  # 10 minutes
                for _root, _, _files in os.walk(str(workspace_dir)):
                    if recently_active:
                        break
                    for _fn in _files:
                        if _fn.endswith((".py", ".md", ".json", ".yaml")):
                            try:
                                if os.path.getmtime(os.path.join(_root, _fn)) > cutoff:
                                    recently_active = True
                                    break
                            except OSError:
                                pass
            if recently_active:
                print(f"  [skip] '{title}' executor active recently — skipping re-queue")
                continue
            # Guard: if tasks.md is missing, re-route to phase_planner
            tasks_file_path = project_dir / tasks_path
            if not tasks_file_path.exists():
                mp_file = project_dir / "state" / "master_plan.md"
                ph_spec = f"Phase {phase_num} of project {slug}"
                if mp_file.exists():
                    try:
                        mp_txt = mp_file.read_text(encoding="utf-8")
                        pm = re.search(
                            rf"## Phase {phase_num}\b.*?(?=## Phase \d|$)",
                            mp_txt, re.DOTALL | re.IGNORECASE)
                        if pm:
                            ph_spec = pm.group(0)
                    except Exception:
                        pass
                _write_state(project_dir, state, f"phase_{phase_num}_planning")
                print(f"  [re-route] '{title}' missing tasks.md -> re-routing to phase_planner")
                agent   = "phase_planner"
                payload = {"phase": phase_num, "phase_spec": ph_spec[:3000], "idea_slug": slug}
            else:
                agent   = "executor"
                payload = {"phase": phase_num, "tasks_path": tasks_path,
                           "workspace_path": workspace_path, "idea_slug": slug}


        elif phase_step == "validating":
            agent = "validator"
            # Check if there's an existing failed report — if so, treat this as a
            # fix_required re-queue so the validator's retry/no-progress counter
            # doesn't reset (the runner re-queue was resetting it each time).
            existing_report = ""
            report_file = project_dir / report_path
            if report_file.exists():
                try:
                    existing_report = report_file.read_text(encoding="utf-8")[:3000]
                except Exception:
                    pass
            has_failures = existing_report and "Verdict: PASS" not in existing_report
            payload = {
                "phase": phase_num,
                "tasks_path": tasks_path,
                "workspace_path": workspace_path,
                "validation_report_path": report_path,
                "idea_slug": slug,
                # Preserve retry context so validator doesn't treat this as fresh start
                "fix_required": has_failures,
                "validation_report": existing_report if has_failures else "",
                "error_summary": "Re-queued by runner after stall detection — continue fixing failures." if has_failures else "",
            }
        elif phase_step == "reviewing":
            agent   = "reviewer"
            payload = {"phase": phase_num, "tasks_path": tasks_path,
                       "workspace_path": workspace_path,
                       "validation_report_path": report_path,
                       "review_path": review_path, "idea_slug": slug}
        elif phase_step == "reviewed":
            # Reviewer finished — deterministic routing via _tick_project
            routed = _tick_project(bus, project_dir, state, phase_num, slug)
            if routed:
                return 1
            continue
        else:
            continue  # Unknown step

        bus.send(Message.create(from_agent="runner", to_agent=agent,
                                type="task", payload=payload))
        print(f"  [re-queue] Re-queued '{title}' -> {agent} (was: {status})")
        return 1  # One at a time — next project picked up after this one completes

    # -----------------------------------------------------------------
    # RECOVERY: If we found nothing to run, check whether ALL remaining
    # blocked projects are waiting exclusively on budget_exceeded prereqs.
    # In that case, reset those prereqs so they can be retried rather than
    # generating new ideas or starting dependents without their prereq.
    # -----------------------------------------------------------------
    blocked_by_budget: dict[str, list[str]] = {}  # prereq_slug -> [waiters]
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue
        state_file = project_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if state.get("status") != "dep_waiting":
            continue
        title = state.get("title", project_dir.name)
        deps  = state.get("depends_on", [])
        for dep_slug in deps:
            dep_file = projects_dir / dep_slug / "state" / "current_idea.json"
            if not dep_file.exists():
                continue
            try:
                dep_state = json.loads(dep_file.read_text(encoding="utf-8"))
                if dep_state.get("status") == "budget_exceeded":
                    blocked_by_budget.setdefault(dep_slug, []).append(title)
            except Exception:
                pass

    if blocked_by_budget:
        now = datetime.now(timezone.utc).isoformat()
        for dep_slug, waiters in blocked_by_budget.items():
            dep_file = projects_dir / dep_slug / "state" / "current_idea.json"
            try:
                dep_state = json.loads(dep_file.read_text(encoding="utf-8"))
                # Restore where the project was before it hit budget
                pre_status = dep_state.get("pre_budget_status", "phase_1_executing")
                dep_state["status"]            = pre_status
                dep_state["session_started_at"] = now
                dep_state["started_at"]         = now
                dep_state.pop("budget_note", None)
                dep_file.write_text(json.dumps(dep_state, indent=2), encoding="utf-8")
                print(
                    f"  🔄 Resetting budget_exceeded prereq '{dep_slug}' → {pre_status} "
                    f"(required by: {', '.join(waiters)})"
                )
            except Exception:
                pass
        # Re-run one more time so the now-unblocked prereq gets queued
        return _rebuild_queues_from_state(bus, ideas_path)

    return 0  # No incomplete projects found
