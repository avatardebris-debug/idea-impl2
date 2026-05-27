#!/usr/bin/env python3
"""
fix_missing_plans.py — Reconstruct master_plan.md for projects that lost it.

For each project without state/master_plan.md:
  1. Builds a minimal but accurate plan from description + workspace files
  2. Marks phases as DONE if tasks.md shows [x] completions or status=complete
  3. Sets total_phases = 1 for simple tools, otherwise preserves existing
  4. Does NOT re-route complete projects — they stay complete

Run from project root:
    python fix_missing_plans.py
"""
from __future__ import annotations
import json
import pathlib
import re
import sys

PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.paths import projects_dir  # noqa: E402


def count_workspace_py(proj: pathlib.Path) -> tuple[int, int]:
    ws = proj / "workspace"
    if not ws.exists():
        return 0, 0
    py = [p for p in ws.rglob("*.py") if "__pycache__" not in str(p)]
    tests = [p for p in py if p.name.startswith("test_")]
    return len(py) - len(tests), len(tests)


def phase_task_counts(proj: pathlib.Path, phase_num: int) -> tuple[int, int]:
    tf = proj / f"phases/phase_{phase_num}/tasks.md"
    if not tf.exists():
        return 0, 0
    content = tf.read_text(encoding="utf-8", errors="ignore")
    done  = len(re.findall(r"^- \[x\]", content, re.MULTILINE | re.IGNORECASE))
    total = done + len(re.findall(r"^- \[ \]", content, re.MULTILINE))
    return done, total


def phase_has_validation(proj: pathlib.Path, phase_num: int) -> bool:
    return (proj / f"phases/phase_{phase_num}/validation_report.md").exists()


def build_plan(proj: pathlib.Path, state: dict) -> str:
    title       = state.get("title", proj.name)
    description = state.get("description", "")
    status      = state.get("status", "")
    total_ph    = state.get("total_phases", 1)
    src, tests  = count_workspace_py(proj)

    is_complete = status in ("complete", "budget_exceeded")

    lines = [
        f"# {title} — Master Plan",
        f"",
        f"## Overview",
        f"{description}",
        f"",
        f"*Reconstructed from project state — original plan was not preserved.*",
        f"",
    ]

    for ph in range(1, int(total_ph) + 1):
        done, total = phase_task_counts(proj, ph)
        has_val     = phase_has_validation(proj, ph)

        # Determine phase status label
        if is_complete or has_val or (done > 0 and done == total):
            status_note = " ✅ COMPLETE"
        elif done > 0:
            status_note = f" (in progress: {done}/{total} tasks)"
        else:
            status_note = ""

        lines.append(f"## Phase {ph}: Implementation{status_note}")

        if ph == 1:
            lines.append(f"**Goal**: Implement the core functionality of {title}.")
            lines.append(f"**Deliverable**: Working Python package with tests.")
        elif ph == 2:
            lines.append(f"**Goal**: Add testing, error handling, and documentation.")
            lines.append(f"**Deliverable**: Full test suite passing, README complete.")
        elif ph == 3:
            lines.append(f"**Goal**: Integration, CLI/API polish, and deployment readiness.")
            lines.append(f"**Deliverable**: Production-ready package.")
        else:
            lines.append(f"**Goal**: Phase {ph} enhancements and refinements.")
            lines.append(f"**Deliverable**: Phase {ph} deliverables complete.")

        if total > 0:
            lines.append(f"**Tasks done**: {done}/{total}")

        spec_file = proj / f"phases/phase_{ph}/spec.md"
        if spec_file.exists():
            spec_txt = spec_file.read_text(encoding="utf-8", errors="ignore").strip()
            if spec_txt and "no plan available" not in spec_txt and "Resume phase" not in spec_txt:
                lines.append(f"")
                lines.append(f"### Spec")
                lines.append(spec_txt[:1500])

        lines.append(f"")

    lines.append(f"## Workspace Summary")
    lines.append(f"- Source files: {src}")
    lines.append(f"- Test files: {tests}")

    return "\n".join(lines)


def fix_state_total_phases(proj: pathlib.Path, state: dict) -> dict:
    """Ensure total_phases is set and phase is set."""
    changed = False

    # Count actual phase dirs
    phase_dirs = list(proj.glob("phases/phase_*"))
    actual_phases = max(
        (int(d.name.split("_")[1]) for d in phase_dirs if d.name.split("_")[1].isdigit()),
        default=1
    )

    if not state.get("total_phases"):
        state["total_phases"] = actual_phases
        changed = True

    if not state.get("phase"):
        # Infer from status string e.g. "phase_2_validating" -> 2
        m = re.search(r"phase_(\d+)_", state.get("status", ""))
        if m:
            state["phase"] = int(m.group(1))
        elif state.get("status") in ("complete", "budget_exceeded"):
            state["phase"] = actual_phases
        else:
            state["phase"] = 1
        changed = True

    return state, changed


def main():
    fixed = 0
    skipped = 0
    root = projects_dir()
    if not root.exists():
        print(f"No projects directory found at {root}")
        return

    for proj in sorted(root.iterdir()):
        if not proj.is_dir():
            continue

        plan_path  = proj / "state" / "master_plan.md"
        state_path = proj / "state" / "current_idea.json"

        if not state_path.exists():
            continue

        state = json.loads(state_path.read_text(encoding="utf-8"))

        # Fix missing total_phases / phase regardless of plan existence
        state, state_changed = fix_state_total_phases(proj, state)
        if state_changed:
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            print(f"  [state fixed] {proj.name}: phase={state['phase']}/{state['total_phases']}")

        if plan_path.exists():
            skipped += 1
            continue

        # Build and write the reconstructed plan
        plan_content = build_plan(proj, state)
        plan_path.write_text(plan_content, encoding="utf-8")
        fixed += 1

        src, tests = count_workspace_py(proj)
        print(f"  [plan created] {proj.name}: {state['status']} "
              f"phase={state['phase']}/{state['total_phases']} "
              f"src={src} tests={tests}")

    print(f"\nDone: {fixed} plans created, {skipped} projects already had plans.")


if __name__ == "__main__":
    main()
