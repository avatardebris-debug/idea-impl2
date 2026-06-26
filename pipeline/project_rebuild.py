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

from pipeline.dep_policy import dep_blocking_reason, parse_requires_from_description
from pipeline.message_bus import Message, MessageBus
from pipeline.paths import projects_dir
from pipeline.pipeline_config import PROJECT_ROOT
from pipeline.project_state import _write_state
from pipeline.project_tick import _tick_project
from pipeline.review_artifacts import (
    build_review_result,
    review_artifacts_complete,
    validation_passed,
)

if TYPE_CHECKING:
    pass


def _executor_recently_active(project_dir: pathlib.Path, cutoff_s: float = 600) -> bool:
    workspace_dir = project_dir / "workspace"
    if not workspace_dir.exists():
        return False
    cutoff = time.time() - cutoff_s
    for _root, _, _files in os.walk(str(workspace_dir)):
        for _fn in _files:
            if _fn.endswith((".py", ".md", ".json", ".yaml")):
                try:
                    if os.path.getmtime(os.path.join(_root, _fn)) > cutoff:
                        return True
                except OSError:
                    pass
    return False


def _try_finalize_review_without_llm(
    bus: MessageBus,
    slug: str,
    title: str,
    state: dict,
    project_dir: pathlib.Path,
    phase_num: int,
    *,
    tasks_path: str,
    workspace_path: str,
    report_path: str,
    review_path: str,
    log_requeue: bool = False,
) -> bool:
    """Skip reviewer LLM when validation PASS + review.md already complete."""
    report_file = project_dir / report_path
    review_file = project_dir / review_path
    if not report_file.exists() or not review_file.exists():
        return False
    try:
        validation_text = report_file.read_text(encoding="utf-8")
        review_text = review_file.read_text(encoding="utf-8")
    except Exception:
        return False
    if not validation_passed(validation_text) or not review_artifacts_complete(review_text):
        return False

    state["review_result"] = build_review_result(
        review_content=review_text,
        review_path=review_path,
        tasks_path=tasks_path,
        workspace_path=workspace_path,
    )
    reviewed_status = f"phase_{phase_num}_reviewed"
    state["status"] = reviewed_status
    (project_dir / "state" / "current_idea.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8",
    )
    if log_requeue:
        print(
            f"  [skip-review] '{title}' — existing PASS validation + review.md; advancing",
        )
    return bool(_tick_project(bus, project_dir, state, phase_num, slug))


def advance_reviewed_projects(bus: MessageBus) -> int:
    """Run _tick_project for projects stuck at phase_X_reviewed with empty queues."""
    projects_root = projects_dir()
    if not projects_root.exists():
        return 0
    for project_dir in sorted(projects_root.iterdir()):
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
        phase_match = re.match(r"phase_(\d+)_reviewed", status)
        if not phase_match:
            continue
        phase_num = int(phase_match.group(1))
        slug = project_dir.name
        title = state.get("title", slug)
        if dispatch_phase_requeue(
            bus, slug, title, state, project_dir, status, log_requeue=True,
        ):
            return 1
    return 0


def dispatch_phase_requeue(
    bus: MessageBus,
    slug: str,
    title: str,
    state: dict,
    project_dir: pathlib.Path,
    status: str,
    *,
    skip_if_executor_recently_active: bool = False,
    log_requeue: bool = False,
) -> bool:
    """Queue the appropriate agent for *status*. Returns True if dispatched."""
    if status == "planning":
        bus.send(Message.create(
            from_agent="runner",
            to_agent="idea_planner",
            type="task",
            payload={
                "title": title,
                "idea": state.get("description", title),
                "idea_slug": slug,
            },
        ))
        if log_requeue:
            print(f"  [re-queue] Re-queued '{title}' -> idea_planner (was: planning)")
        return True

    if status in ("field_test_planning", "field_test_failed"):
        from pipeline.ship_mode import dispatch_ship_requeue

        if dispatch_ship_requeue(bus, slug, title, state, project_dir, status):
            if log_requeue:
                print(f"  [re-queue] Re-queued '{title}' -> ship track ({status})")
            return True

    if not status.startswith("phase_"):
        return False

    phase_match = re.match(r"phase_(\d+)_(\w+)", status)
    if not phase_match:
        return False
    phase_num = int(phase_match.group(1))
    phase_step = phase_match.group(2)

    tasks_path = f"phases/phase_{phase_num}/tasks.md"
    workspace_path = str(project_dir / "workspace")
    report_path = f"phases/phase_{phase_num}/validation_report.md"
    review_path = f"phases/phase_{phase_num}/review.md"

    if phase_step == "planning":
        master_plan_file = project_dir / "state" / "master_plan.md"
        phase_spec = f"Resume phase {phase_num} of {title}"
        if master_plan_file.exists():
            try:
                mp = master_plan_file.read_text(encoding="utf-8")
                m = re.search(
                    rf"## Phase {phase_num}\b[^\n]*\n.*?(?=## Phase \d|$)",
                    mp, re.DOTALL | re.IGNORECASE,
                )
                if m:
                    phase_spec = m.group(0)[:3000]
            except Exception:
                pass
        agent = "phase_planner"
        payload = {"phase": phase_num, "phase_spec": phase_spec, "idea_slug": slug}
    elif phase_step == "executing":
        if skip_if_executor_recently_active and _executor_recently_active(project_dir):
            if log_requeue:
                print(f"  [skip] '{title}' executor active recently — skipping re-queue")
            return False
        tasks_file_path = project_dir / tasks_path
        if not tasks_file_path.exists():
            ph_spec = f"Phase {phase_num} of project {slug}"
            mp_file = project_dir / "state" / "master_plan.md"
            if mp_file.exists():
                try:
                    mp_txt = mp_file.read_text(encoding="utf-8")
                    pm = re.search(
                        rf"## Phase {phase_num}\b.*?(?=## Phase \d|$)",
                        mp_txt, re.DOTALL | re.IGNORECASE,
                    )
                    if pm:
                        ph_spec = pm.group(0)
                except Exception:
                    pass
            _write_state(project_dir, state, f"phase_{phase_num}_planning")
            if log_requeue:
                print(f"  [re-route] '{title}' missing tasks.md -> re-routing to phase_planner")
            agent = "phase_planner"
            payload = {"phase": phase_num, "phase_spec": ph_spec[:3000], "idea_slug": slug}
        else:
            agent = "executor"
            payload = {
                "phase": phase_num,
                "tasks_path": tasks_path,
                "workspace_path": workspace_path,
                "idea_slug": slug,
            }
    elif phase_step == "validating":
        agent = "validator"
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
            "fix_required": has_failures,
            "validation_report": existing_report if has_failures else "",
            "error_summary": (
                "Re-queued by runner after stall detection — continue fixing failures."
                if has_failures and log_requeue
                else "Re-queued by runner — continue fixing failures."
                if has_failures
                else ""
            ),
        }
    elif phase_step == "reviewing":
        if _try_finalize_review_without_llm(
            bus, slug, title, state, project_dir, phase_num,
            tasks_path=tasks_path,
            workspace_path=workspace_path,
            report_path=report_path,
            review_path=review_path,
            log_requeue=log_requeue,
        ):
            return True
        agent = "reviewer"
        payload = {
            "phase": phase_num,
            "tasks_path": tasks_path,
            "workspace_path": workspace_path,
            "validation_report_path": report_path,
            "review_path": review_path,
            "idea_slug": slug,
        }
    elif phase_step == "reviewed":
        return bool(_tick_project(bus, project_dir, state, phase_num, slug))
    else:
        return False

    bus.send(Message.create(from_agent="runner", to_agent=agent, type="task", payload=payload))
    if log_requeue:
        print(f"  [re-queue] Re-queued '{title}' -> {agent} (was: {status})")
    return True


def _rebuild_single_project(bus: MessageBus, slug: str, state: dict, project_dir: pathlib.Path) -> bool:
    """Re-queue one specific in-progress project. Returns True if queued."""
    status = state.get("status", "")
    title = state.get("title", slug)

    if status in ("", "complete", "budget_exceeded", "dep_waiting"):
        return False

    _now = datetime.now(timezone.utc).isoformat()
    state["session_started_at"] = _now
    state.pop("budget_note", None)
    state_file = project_dir / "state" / "current_idea.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    return dispatch_phase_requeue(
        bus, slug, title, state, project_dir, status,
    )


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
        return 0

    projects_root = projects_dir()
    if not projects_root.exists():
        return 0

    for project_dir in projects_root.iterdir():
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

        mi_path = ideas_path if ideas_path else PROJECT_ROOT / "master_ideas.md"
        if mi_path.exists():
            try:
                mi_text = mi_path.read_text(encoding="utf-8")
                _mi_title = state.get("title", "")
                if _mi_title:
                    for mi_line in mi_text.splitlines():
                        if _mi_title.strip("[]") in mi_line:
                            fresh_deps = parse_requires_from_description(mi_line)
                            if fresh_deps and set(fresh_deps) != set(deps):
                                    print(f"  🔄 Updated deps for '{title}': {deps} → {fresh_deps}")
                                    deps = fresh_deps
                                    state["depends_on"] = deps
                            break
            except Exception:
                pass

        still_blocked = []
        for dep_slug in deps:
            dep_file = projects_root / dep_slug / "state" / "current_idea.json"
            if not dep_file.exists():
                still_blocked.append(dep_blocking_reason(dep_slug, None, context="rebuild"))
                continue
            try:
                dep_status = json.loads(dep_file.read_text(encoding="utf-8")).get("status")
            except Exception:
                still_blocked.append(f"{dep_slug} (unreadable)")
                continue
            reason = dep_blocking_reason(dep_slug, dep_status, context="rebuild")
            if reason:
                still_blocked.append(reason)
        if still_blocked:
            continue

        new_status = state.get("pre_dep_status", "phase_1_executing")
        state["status"] = new_status
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(f"  ✅ '{title}' deps satisfied — resuming from {new_status}")

    def _project_recency(d: pathlib.Path) -> float:
        sf = d / "state" / "current_idea.json"
        try:
            s = json.loads(sf.read_text(encoding="utf-8"))
            return -datetime.fromisoformat(s.get("started_at", "2000-01-01T00:00:00+00:00")).timestamp()
        except Exception:
            return 0.0

    for project_dir in sorted(projects_root.iterdir(), key=_project_recency):
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
        title = state.get("title", project_dir.name)
        slug = project_dir.name

        if status == "evicted":
            pre_status = state.get("pre_evict_status", "phase_1_executing")
            print(f"  [rebuilt] Restoring evicted project '{title}' status: evicted -> {pre_status}")
            state["status"] = pre_status
            state["evict_requested"] = False
            state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            status = pre_status

        if status in ("", "complete", "budget_exceeded", "dep_waiting"):
            continue

        state["session_started_at"] = datetime.now(timezone.utc).isoformat()
        if not state.get("started_at"):
            state["started_at"] = state["session_started_at"]
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        retries_file = project_dir / "state" / "phase_retries.json"
        if retries_file.exists():
            try:
                retries = json.loads(retries_file.read_text(encoding="utf-8"))
                _is_locked = state.get("budget_lock", False)
                for k, v in retries.items():
                    if "no_progress" in k and isinstance(v, int) and v >= 4 and not _is_locked:
                        state["status"] = "budget_exceeded"
                        state["budget_note"] = f"Stalled: no_progress streak {v} cycles on {k}"
                        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
                        print(f"  ⏭️  Stall-stopped project '{title}' (stuck {v} cycles) → budget_exceeded")
                        break
                if state.get("status") == "budget_exceeded":
                    continue
            except Exception:
                pass

        depends_on = state.get("depends_on", [])
        if depends_on:
            dep_blocked = []
            for dep_slug in depends_on:
                dep_file = projects_root / dep_slug / "state" / "current_idea.json"
                if not dep_file.exists():
                    dep_blocked.append(dep_blocking_reason(dep_slug, None, context="rebuild"))
                    continue
                try:
                    dep_st = json.loads(dep_file.read_text(encoding="utf-8"))
                    reason = dep_blocking_reason(
                        dep_slug, dep_st.get("status"), context="rebuild",
                    )
                    if reason:
                        dep_blocked.append(reason)
                except Exception:
                    dep_blocked.append(f"{dep_slug} (unreadable)")
            if dep_blocked:
                print(f"  ⏸  '{title}' dep_waiting — blocked by: {', '.join(dep_blocked)}")
                continue

        phase_match = re.match(r"phase_(\d+)_(\w+)", status)
        if phase_match:
            phase_num = int(phase_match.group(1))
            tasks_file = project_dir / f"phases/phase_{phase_num}/tasks.md"
            if tasks_file.exists():
                try:
                    from pipeline.agent_process import AgentProcess
                    AgentProcess.normalize_tasks_file(tasks_file)
                except Exception:
                    pass

        _now = datetime.now(timezone.utc).isoformat()
        state["started_at"] = _now
        state["session_started_at"] = _now
        state.pop("budget_note", None)
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        if dispatch_phase_requeue(
            bus, slug, title, state, project_dir, status,
            skip_if_executor_recently_active=True,
            log_requeue=True,
        ):
            return 1
        continue

    blocked_by_budget: dict[str, list[str]] = {}
    for project_dir in projects_root.iterdir():
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
        for dep_slug in deps:
            dep_file = projects_root / dep_slug / "state" / "current_idea.json"
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
            dep_file = projects_root / dep_slug / "state" / "current_idea.json"
            try:
                dep_state = json.loads(dep_file.read_text(encoding="utf-8"))
                pre_status = dep_state.get("pre_budget_status", "phase_1_executing")
                dep_state["status"] = pre_status
                dep_state["session_started_at"] = now
                dep_state["started_at"] = now
                dep_state.pop("budget_note", None)
                dep_file.write_text(json.dumps(dep_state, indent=2), encoding="utf-8")
                print(
                    f"  🔄 Resetting budget_exceeded prereq '{dep_slug}' → {pre_status} "
                    f"(required by: {', '.join(waiters)})"
                )
            except Exception:
                pass
        return _rebuild_queues_from_state(bus, ideas_path)

    return 0