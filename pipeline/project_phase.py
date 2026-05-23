"""
pipeline/project_phase.py
Phase advance, completion, shared lib extraction.
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
from pipeline.project_state import _write_state_dict

if TYPE_CHECKING:
    pass

def _extract_shared_libs(
    project_dir: pathlib.Path,
    review_path: str,
    workspace_path: str,
    title: str,
) -> None:
    """Post-hook: parse ## Reusable Components from review.md and copy files
    to .pipeline/shared_libs/ + append to reusable_tools.md.

    Runs after every clean reviewer pass — no LLM budget needed.
    The reviewer LLM only needs to LIST components; we handle file copying.
    """
    import re as _re
    import shutil as _shutil

    run_dir   = project_dir.parent.parent.parent  # .pipeline/projects/slug -> idea impl/
    shared    = run_dir / ".pipeline" / "shared_libs"
    tools_log = run_dir / ".pipeline" / "state" / "reusable_tools.md"
    review_full = project_dir / review_path

    if not review_full.exists():
        return
    try:
        review_text = review_full.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return

    # Extract the ## Reusable Components section (handles bold: **Reusable Components**)
    m = _re.search(
        r"(?:##\s*\*{0,2}Reusable Components\*{0,2})(.*?)(?=\n##\s|\Z)",
        review_text, _re.DOTALL | _re.IGNORECASE,
    )
    if not m:
        return
    section = m.group(1).strip()
    if not section or _re.search(r"\b(none|n/a|nothing)\b", section, _re.IGNORECASE):
        return

    ws_path = pathlib.Path(workspace_path) if workspace_path else project_dir / "workspace"
    extracted: list[str] = []

    for line in section.splitlines():
        line = line.strip()
        # Strip bullet markers: "- ", "* ", "1. ", "2. " etc.
        line = _re.sub(r"^[-*\d]+[.)]\s*", "", line).strip()
        if not line or len(line) < 8:
            continue

        # Strip leading backticks/code spans for the name
        clean = _re.sub(r"`([^`]+)`", r"\1", line)

        # Derive a safe component name from the first word/phrase before : or —
        first_part = _re.split(r"[:\s—–]", clean)[0].strip().lower()
        component_name = _re.sub(r"[^a-z0-9_]", "_", first_part).strip("_")[:40]
        if not component_name or len(component_name) < 2:
            continue

        # Find any .py file references in the bullet line
        file_refs = _re.findall(r"`([^`]+\.py)`|([\w./]+\.py)", line)
        dest_dir = shared / component_name
        copied = 0

        for ref_tuple in file_refs:
            ref = (ref_tuple[0] or ref_tuple[1]).lstrip("/")
            candidates = [
                ws_path / ref,
                ws_path / pathlib.Path(ref).name,
                *list(ws_path.rglob(pathlib.Path(ref).name)),
            ]
            for candidate in candidates:
                if candidate.exists() and candidate.is_file():
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    _shutil.copy2(candidate, dest_dir / candidate.name)
                    copied += 1
                    break

        # Log entry whether or not we found the file — metadata is still useful
        desc = line[:120]
        log_entry = f"- {component_name}: {desc} (source: {title})\n"
        tools_log.parent.mkdir(parents=True, exist_ok=True)
        existing = tools_log.read_text(encoding="utf-8") if tools_log.exists() else ""
        if component_name not in existing:
            with tools_log.open("a", encoding="utf-8") as f:
                f.write(log_entry)
            extracted.append(component_name)

    if extracted:
        print(f"  [shared_libs] {len(extracted)} component(s) from '{title}': {', '.join(extracted)}")
        try:
            from pipeline.pipeline_mode import legacy_mode
            if not legacy_mode():
                from pipeline.capability_registry import register_shared_lib_capability

                for comp in extracted:
                    register_shared_lib_capability(
                        comp,
                        source_project=project_dir.name,
                        purpose=f"Reusable component from {title}",
                        status="draft",
                    )
        except Exception:
            pass


def _advance_phase(
    bus: MessageBus,
    project_dir: pathlib.Path,
    state: dict,
    completed_phase: int,
    slug: str,
) -> bool:
    """Advance to next phase if one exists. Returns True if advanced.

    Checks for overflow tasks first — if phase N had >8 tasks split into
    batches, the overflow runs before advancing to phase N+1.
    """
    # --- Overflow check: run batch 2 before advancing ---
    overflow_tasks_path = project_dir / f"phases/phase_{completed_phase}_overflow/tasks.md"
    overflow_done_marker = project_dir / f"phases/phase_{completed_phase}_overflow/.completed"
    if overflow_tasks_path.exists() and not overflow_done_marker.exists():
        # Overflow tasks exist and haven't been completed yet — queue them
        workspace = project_dir / "workspace"
        state["status"] = f"phase_{completed_phase}_executing"
        state.pop("review_result", None)
        _write_state_dict(project_dir, state)

        # Mark that we're in overflow mode so we don't loop
        overflow_done_marker.parent.mkdir(parents=True, exist_ok=True)

        bus.send(Message.create(
            from_agent="runner",
            to_agent="executor",
            type="task",
            payload={
                "phase": completed_phase,
                "tasks_path": f"phases/phase_{completed_phase}_overflow/tasks.md",
                "workspace_path": str(workspace),
                "idea_slug": slug,
                "is_overflow": True,
            },
        ))
        title = state.get("title", slug)
        print(f"  📦 '{title}' phase {completed_phase} overflow: queuing batch 2 tasks")
        return True

    # If overflow was just completed, mark it and continue to next phase
    if overflow_done_marker.exists():
        # Mark overflow as done for this phase
        try:
            overflow_done_marker.write_text("completed", encoding="utf-8")
        except Exception:
            pass

    next_phase = completed_phase + 1

    # --- Primary check: master_plan.md has a ## Phase N heading ---
    phase_found_in_plan = False
    phase_spec = f"Phase {next_phase} of project {slug}"
    master_plan_file = project_dir / "state" / "master_plan.md"
    if master_plan_file.exists():
        try:
            master_plan = master_plan_file.read_text(encoding="utf-8")
            pattern = rf"## Phase {next_phase}\b"
            if re.search(pattern, master_plan, re.IGNORECASE):
                phase_found_in_plan = True
                phase_pattern = rf"(## Phase {next_phase}\b[^\n]*\n)(.*?)(?=## Phase \d|$)"
                match = re.search(phase_pattern, master_plan, re.DOTALL | re.IGNORECASE)
                if match:
                    phase_spec = match.group(0)
        except Exception:
            pass

    # --- REMOVED: total_phases fallback ---
    # Previously we trusted state["total_phases"] as a fallback when the master
    # plan didn't have a ## Phase N heading. This caused phantom phases (7-9)
    # with generic boilerplate tasks when total_phases > actual plan headings.
    # Now only master_plan.md headings determine available phases.

    if not phase_found_in_plan:
        return False  # No more phases

    # Update state
    state["status"] = f"phase_{next_phase}_planning"
    state["phase"] = next_phase
    state.pop("review_result", None)  # Clear stale review data
    _write_state_dict(project_dir, state)

    # Write spec.md so the agent always has full context on disk
    spec_dir = project_dir / f"phases/phase_{next_phase}"
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_file = spec_dir / "spec.md"
    if phase_spec and not spec_file.exists():
        try:
            spec_file.write_text(phase_spec, encoding="utf-8")
        except Exception:
            pass

    # Send to phase planner
    bus.send(Message.create(
        from_agent="runner",
        to_agent="phase_planner",
        type="task",
        payload={
            "phase": next_phase,
            "phase_spec": phase_spec[:3000],
            "idea_slug": slug,
        },
    ))
    return True


def _mark_complete(project_dir: pathlib.Path, state: dict, title: str, ideas_path: pathlib.Path | None = None) -> None:
    """Mark a project as complete in state, registry, and master_ideas.md (slug-aware)."""
    state["status"] = "complete"
    state.pop("review_result", None)
    slug = state.get("_slug") or project_dir.name
    state["_slug"] = slug
    state["completed_at"] = datetime.now(timezone.utc).isoformat()
    _write_state_dict(project_dir, state)
    print(f"  ✅ '{title}' completed all phases!")

    from pipeline.pipeline_status import get_runner_ideas_path

    mi_path = ideas_path or get_runner_ideas_path() or (PROJECT_ROOT / "master_ideas.md")
    try:
        from pipeline.ideas_sync import record_completion
        n = record_completion(
            slug,
            title,
            ideas_path=mi_path if mi_path.exists() else None,
            description=state.get("description", ""),
            workspace=str(project_dir / "workspace"),
        )
        if n:
            print(f"  [truth] removed {n} line(s) from {mi_path.name}")
    except Exception as _is_err:
        import logging as _log
        _log.getLogger(__name__).debug("truth/completion record skipped: %s", _is_err)

    # --- Fine-tune corpus: emit training pairs for this completed project ---
    try:
        from pipeline.corpus_collector import collect_project_on_complete
        collect_project_on_complete(project_dir, state)
    except Exception as _cc_err:
        import logging as _log
        _log.getLogger(__name__).debug("corpus_collector skipped (non-critical): %s", _cc_err)

    try:
        from pipeline.capability_registry import refresh_capability
        if refresh_capability(slug):
            print(f"  [registry] refreshed capability '{slug}'")
    except Exception as _reg_err:
        import logging as _log
        _log.getLogger(__name__).debug("capability refresh skipped: %s", _reg_err)
