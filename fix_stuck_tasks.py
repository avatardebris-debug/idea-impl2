#!/usr/bin/env python3
"""
fix_stuck_tasks.py — Detect and fix projects stuck with code but unmarked tasks.

For each project:
  1. Find the current phase from current_idea.json
  2. Check if workspace has .py files (code was written)
  3. Check if tasks.md has unchecked tasks for that phase
  4. If code exists but tasks are all [ ], mark Phase N tasks as [x]
  5. Report what was fixed

Usage:
    python fix_stuck_tasks.py              # dry run (report only)
    python fix_stuck_tasks.py --fix        # actually fix tasks.md files
"""

import json
import pathlib
import re
import sys

import sys

PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.paths import projects_dir  # noqa: E402


def extract_phase_tasks(content: str, phase_num: int) -> tuple[str, int, int]:
    """Extract phase section and return (section_text, start_pos, end_pos)."""
    pattern = rf'^(#{{1,4}})\s+(?:.*?)?Phase\s+{phase_num}\b.*$'
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    if not match:
        return content, 0, len(content)

    start = match.start()
    next_pattern = rf'^#{{1,4}}\s+(?:.*?)?Phase\s+(?:{phase_num + 1}|{phase_num + 2}|{phase_num + 3})\b'
    next_match = re.search(next_pattern, content[match.end():], re.MULTILINE | re.IGNORECASE)
    if next_match:
        end = match.end() + next_match.start()
    else:
        end = len(content)

    return content[start:end], start, end


def check_project(project_dir: pathlib.Path, do_fix: bool = False) -> dict:
    """Check a single project for stuck tasks. Returns status dict."""
    state_file = project_dir / "state" / "current_idea.json"
    if not state_file.exists():
        return {"status": "no_state"}

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "bad_state"}

    title = state.get("title", project_dir.name)
    status = state.get("status", "")
    phase_num = state.get("phase", 1)

    if status in ("complete", "budget_exceeded", ""):
        return {"status": "terminal", "title": title, "phase_status": status}

    # Check workspace for code
    workspace = project_dir / "workspace"
    py_files = list(workspace.rglob("*.py")) if workspace.exists() else []
    total_lines = 0
    for f in py_files:
        try:
            total_lines += len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            pass

    # Check tasks.md
    tasks_file = project_dir / f"phases/phase_{phase_num}/tasks.md"
    if not tasks_file.exists():
        return {
            "status": "no_tasks_file",
            "title": title,
            "py_files": len(py_files),
            "lines": total_lines,
        }

    raw = tasks_file.read_text(encoding="utf-8")
    scoped, sec_start, sec_end = extract_phase_tasks(raw, phase_num)

    unchecked = re.findall(r'^\s*- \[ \]', scoped, re.MULTILINE)
    checked = re.findall(r'^\s*- \[x\]', scoped, re.MULTILINE | re.IGNORECASE)

    result = {
        "status": "ok" if checked else ("stuck" if py_files else "not_started"),
        "title": title,
        "phase": phase_num,
        "phase_status": status,
        "py_files": len(py_files),
        "lines": total_lines,
        "tasks_done": len(checked),
        "tasks_unchecked": len(unchecked),
        "tasks_total": len(checked) + len(unchecked),
    }

    # Fix: mark all unchecked Phase N tasks as [x] if code exists
    if do_fix and result["status"] == "stuck" and len(py_files) >= 3:
        # Only fix within the phase section
        fixed_section = re.sub(r'^\s*- \[ \]', '- [x]', scoped, flags=re.MULTILINE)
        new_content = raw[:sec_start] + fixed_section + raw[sec_end:]
        tasks_file.write_text(new_content, encoding="utf-8")
        new_checked = len(re.findall(r'^\s*- \[x\]', fixed_section, re.MULTILINE | re.IGNORECASE))
        result["fixed"] = True
        result["tasks_done"] = new_checked
        result["tasks_unchecked"] = 0

    return result


def main():
    do_fix = "--fix" in sys.argv

    root = projects_dir()
    if not root.exists():
        print("No pipeline projects directory found.")
        return

    projects = sorted(root.iterdir())
    print(f"\n{'=' * 70}")
    print(f"  Project Task Audit — {len(projects)} projects")
    print(f"  Mode: {'FIX' if do_fix else 'DRY RUN (use --fix to apply)'}")
    print(f"{'=' * 70}\n")

    stuck = []
    ok = []
    terminal = []
    not_started = []

    for p in projects:
        if not p.is_dir():
            continue
        result = check_project(p, do_fix=do_fix)
        slug = p.name[:40]

        if result["status"] == "stuck":
            stuck.append(result)
            fix_label = " → FIXED ✅" if result.get("fixed") else ""
            print(f"  🔴 STUCK  {slug}")
            print(f"           Phase {result['phase']} ({result['phase_status']}): "
                  f"{result['tasks_done']}/{result['tasks_total']} tasks, "
                  f"{result['py_files']} files, {result['lines']} lines{fix_label}")
        elif result["status"] == "ok":
            ok.append(result)
            print(f"  🟢 OK     {slug} — {result['tasks_done']}/{result['tasks_total']} tasks done")
        elif result["status"] == "not_started":
            not_started.append(result)
            print(f"  ⚪ EMPTY  {slug} — no code written yet")
        elif result["status"] == "terminal":
            terminal.append(result)
            print(f"  ⏹  DONE   {slug} ({result['phase_status']})")
        else:
            print(f"  ❓ {result['status']:7s} {slug}")

    print(f"\n{'=' * 70}")
    print(f"  Summary: {len(stuck)} stuck, {len(ok)} ok, {len(not_started)} empty, {len(terminal)} done")
    if stuck and not do_fix:
        print(f"\n  Run with --fix to mark {len(stuck)} stuck projects' tasks as done.")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
