#!/usr/bin/env python3
"""
reset_budget_exceeded.py — Reset budget_exceeded projects so the runner can retry them.

Usage:
    python reset_budget_exceeded.py               # list all budget_exceeded projects
    python reset_budget_exceeded.py --reset-all   # reset every budget_exceeded project
    python reset_budget_exceeded.py slug1 slug2   # reset specific project slugs
    python reset_budget_exceeded.py --generate-polish  # also write polish_queue.md for missing-phase projects

The reset sets status back to the pre_budget_status (or phase_N_executing as fallback)
and clears session_started_at so the runner gives a fresh budget window.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

PROJECT_ROOT  = pathlib.Path(__file__).parent.resolve()
from pipeline.paths import projects_dir as _projects_dir
POLISH_QUEUE  = PROJECT_ROOT / "polish_queue.md"


def _status_rank(status: str) -> int:
    order = [
        "phase_1_planning", "phase_1_executing", "phase_1_validating", "phase_1_reviewing", "phase_1_reviewed",
        "phase_2_planning", "phase_2_executing", "phase_2_validating", "phase_2_reviewing", "phase_2_reviewed",
        "phase_3_planning", "phase_3_executing", "phase_3_validating", "phase_3_reviewing", "phase_3_reviewed",
        "phase_4_planning", "phase_4_executing", "phase_4_validating", "phase_4_reviewing", "phase_4_reviewed",
        "phase_5_planning", "phase_5_executing", "phase_5_validating", "phase_5_reviewing", "phase_5_reviewed",
        "phase_6_planning", "phase_6_executing", "phase_6_validating", "phase_6_reviewing", "phase_6_reviewed",
        "complete",
    ]
    try:
        return order.index(status)
    except ValueError:
        return -1


def scan_projects() -> list[dict]:
    """Return info dicts for all projects."""
    results = []
    if not _projects_dir().exists():
        return results
    for proj_dir in sorted(_projects_dir().iterdir()):
        if not proj_dir.is_dir():
            continue
        sf = proj_dir / "state" / "current_idea.json"
        if not sf.exists():
            continue
        try:
            s = json.loads(sf.read_text(encoding="utf-8"))
            s["_slug"] = proj_dir.name
            s["_state_file"] = sf
            results.append(s)
        except Exception:
            continue
    return results


def reset_project(state: dict) -> bool:
    """Reset a single budget_exceeded project. Returns True if reset."""
    slug = state["_slug"]
    sf   = state["_state_file"]
    current_status = state.get("status", "")

    if current_status not in ("budget_exceeded",):
        print(f"  SKIP {slug}: status is '{current_status}' (not budget_exceeded)")
        return False

    # Determine what phase to resume from
    pre = state.get("pre_budget_status", "")
    phase = state.get("phase", 1)
    resume_status = pre if pre and "phase_" in pre else f"phase_{phase}_executing"

    state["status"] = resume_status
    state["session_started_at"] = datetime.now(timezone.utc).isoformat()
    state.pop("budget_note", None)
    state.pop("pre_budget_status", None)

    sf.write_text(json.dumps(state, indent=2), encoding="utf-8")
    title = state.get("title", slug)[:40]
    print(f"  RESET {slug}: budget_exceeded -> {resume_status}  [{title}]")
    return True


def generate_polish_queue(projects: list[dict]) -> int:
    """Write/update polish_queue.md with projects that have missing phases."""
    lines = [
        "# Polish Queue",
        "",
        "Projects marked complete but with missing phases.",
        "The --polish flag resumes them from their last completed phase.",
        "Format: `- [ ] **[project-slug]** — notes about what to add`",
        "",
    ]
    count = 0
    for s in projects:
        status = s.get("status", "")
        phase  = s.get("phase", 1)
        total  = s.get("total_phases", 1)
        slug   = s["_slug"]
        title  = s.get("title", slug)[:50]
        try:
            if status in ("complete", "budget_exceeded") and int(phase) < int(total):
                lines.append(
                    f"- [ ] **[{slug}]** — "
                    f"p{phase}/{total} {status}. Continue phases {int(phase)+1}-{total}. "
                    f"Original title: {title}"
                )
                count += 1
        except Exception:
            continue
    POLISH_QUEUE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n  Wrote {count} entries to {POLISH_QUEUE.name}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slugs", nargs="*",
                        help="Specific project slugs to reset (default: list only)")
    parser.add_argument("--reset-all", action="store_true",
                        help="Reset every budget_exceeded project")
    parser.add_argument("--generate-polish", action="store_true",
                        help="Write polish_queue.md for complete projects with missing phases")
    args = parser.parse_args()

    projects = scan_projects()

    budget_exc = [p for p in projects if p.get("status") == "budget_exceeded"]
    complete_partial = [
        p for p in projects
        if p.get("status") in ("complete", "budget_exceeded")
        and _status_rank("complete") > _status_rank(f"phase_{p.get('total_phases', 1)}_reviewed")
        or (p.get("status") in ("complete", "budget_exceeded")
            and int(p.get("phase", 1)) < int(p.get("total_phases", 1)))
    ]

    if not args.reset_all and not args.slugs and not args.generate_polish:
        # List mode
        print(f"\n{'='*60}")
        print(f"  Budget exceeded ({len(budget_exc)} projects):")
        for p in budget_exc:
            phase = p.get("phase", "?")
            total = p.get("total_phases", "?")
            note  = p.get("budget_note", "")[:50]
            print(f"    {p['_slug']}  p{phase}/{total}  [{note}]")

        print(f"\n  Complete with missing phases ({len(complete_partial)} projects):")
        for p in [x for x in projects
                  if x.get("status") == "complete"
                  and int(x.get("phase", 1)) < int(x.get("total_phases", 1))]:
            phase = p.get("phase", "?")
            total = p.get("total_phases", "?")
            print(f"    {p['_slug']}  p{phase}/{total}")

        print(f"\n  Use --reset-all to reset all budget_exceeded projects.")
        print(f"  Use --generate-polish to write polish_queue.md.")
        print(f"{'='*60}\n")
        return

    reset_count = 0
    if args.reset_all:
        for p in budget_exc:
            if reset_project(p):
                reset_count += 1
    elif args.slugs:
        slug_set = set(args.slugs)
        for p in projects:
            if p["_slug"] in slug_set:
                if reset_project(p):
                    reset_count += 1

    if reset_count:
        print(f"\n  Reset {reset_count} project(s). Run 'python pipeline/runner.py --from-list' to retry.")

    if args.generate_polish:
        generate_polish_queue(projects)


if __name__ == "__main__":
    main()
