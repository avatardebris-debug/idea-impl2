#!/usr/bin/env python3
"""
import_cloud_zip.py â€” Import a cloud run zip file into the local project.

Usage:
    python import_cloud_zip.py <path_to_zip>
    python import_cloud_zip.py latest   # finds newest zip in Downloads

What it does:
    1. Extracts the zip to a temp dir
    2. Detects and fixes workspace/ double-nesting (workspace/workspace/)
    3. Detects stray files written outside .pipeline/ and moves them in
    4. Merges extracted .pipeline/ into local .pipeline/ (non-destructive)
    5. Prints a manifest of every project and its file counts
    6. Does NOT overwrite state files unless cloud version is NEWER
"""
from __future__ import annotations
import io
import json
import pathlib
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError from
# project content or state JSON that contains non-ASCII characters)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pipeline.paths import get_pipeline_dir, project_dir, projects_dir
from pipeline.pipeline_config import PROJECT_ROOT


def find_latest_zip() -> pathlib.Path:
    """Find the most recently modified zip in Downloads."""
    downloads = pathlib.Path.home() / "Downloads"
    zips = list(downloads.glob("*.zip"))
    if not zips:
        print("ERROR: no zip files found in ~/Downloads")
        sys.exit(1)
    latest = max(zips, key=lambda p: p.stat().st_mtime)
    print(f"  Found latest zip: {latest.name}")
    return latest


def fix_double_workspace(project_dir: pathlib.Path) -> int:
    """
    Detect and flatten workspace/workspace/ double-nesting.
    
    Root cause: LLM writes to relative 'workspace/' inside the workspace dir,
    creating .pipeline/projects/<slug>/workspace/workspace/<files>.
    Fix: move all contents of workspace/workspace/ up one level.
    Returns number of files moved.
    """
    ws = project_dir / "workspace"
    double = ws / "workspace"
    if not double.exists():
        return 0

    moved = 0
    for item in double.iterdir():
        dest = ws / item.name
        if dest.exists():
            if dest.is_dir() and item.is_dir():
                # Merge directories
                for sub in item.rglob("*"):
                    if sub.is_file():
                        rel = sub.relative_to(item)
                        target = dest / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(str(sub), str(target))
                        moved += 1
            else:
                # File conflict â€” keep newer
                try:
                    src_mtime = item.stat().st_mtime
                    dst_mtime = dest.stat().st_mtime
                    if src_mtime > dst_mtime:
                        shutil.copy2(str(item), str(dest))
                        moved += 1
                except OSError:
                    pass
        else:
            shutil.move(str(item), str(dest))
            moved += 1

    # Remove now-empty double workspace dir
    try:
        shutil.rmtree(str(double))
    except OSError:
        pass

    return moved


def fix_stray_phases(project_dir: pathlib.Path) -> int:
    """
    Detect validation_report.md / review.md written inside workspace/phases/
    instead of .pipeline/projects/<slug>/phases/.
    Moves them to the correct location.
    """
    moved = 0
    stray_phases = project_dir / "workspace" / "phases"
    if not stray_phases.exists():
        return 0

    real_phases = project_dir / "phases"
    for f in stray_phases.rglob("*"):
        if f.is_file():
            rel = f.relative_to(stray_phases)
            dest = real_phases / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(str(f), str(dest))
                moved += 1
                print(f"    Moved stray: workspace/phases/{rel} â†’ phases/{rel}")

    try:
        shutil.rmtree(str(stray_phases))
    except OSError:
        pass
    return moved


STATUS_ORDER = [
    "dep_waiting",
    "planning", "phase_1_planning", "phase_1_executing",
    "phase_1_validating", "phase_1_reviewing", "phase_1_reviewed",
    "phase_2_planning", "phase_2_executing", "phase_2_validating",
    "phase_2_reviewing", "phase_2_reviewed",
    "phase_3_planning", "phase_3_executing", "phase_3_validating",
    "phase_3_reviewing", "phase_3_reviewed",
    "phase_4_planning", "phase_4_executing", "phase_4_validating",
    "phase_4_reviewing", "phase_4_reviewed",
    "phase_5_planning", "phase_5_executing", "phase_5_validating",
    "phase_5_reviewing", "phase_5_reviewed",
    "phase_6_planning", "phase_6_executing", "phase_6_validating",
    "phase_6_reviewing", "phase_6_reviewed",
    "budget_exceeded", "complete",
]


def status_rank(status: str) -> int:
    """Return the ordinal rank of a status string. Unknown = -1."""
    try:
        return STATUS_ORDER.index(status)
    except ValueError:
        return -1


def merge_state(local: pathlib.Path, remote: pathlib.Path) -> tuple[bool, int]:
    """
    Merge remote current_idea.json into local â€” keep whichever has a
    more advanced status rank.

    Returns (updated: bool, rank_delta: int)
      rank_delta > 0  â†’ remote is ahead  (remote wins)
      rank_delta == 0 â†’ same rank
      rank_delta < 0  â†’ local is ahead   (local wins)
    """
    try:
        r_data = json.loads(remote.read_text(encoding="utf-8"))
        r_rank = status_rank(r_data.get("status", ""))
        if local.exists():
            l_data = json.loads(local.read_text(encoding="utf-8"))
            l_rank = status_rank(l_data.get("status", ""))
            delta = r_rank - l_rank
            if delta <= 0:
                return False, delta   # local is same or further ahead
        else:
            delta = r_rank + 1        # anything > 0 â†’ remote wins
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(r_data, indent=2), encoding="utf-8")
        return True, delta
    except Exception:
        return False, 0


def merge_files(src_root: pathlib.Path, dst_root: pathlib.Path,
                remote_ahead: bool, skip_patterns: tuple[str, ...] = ()) -> int:
    """
    Copy files from src_root into dst_root.

    Conflict resolution:
      remote_ahead=True  â†’ remote wins for ALL files (overwrite existing)
      remote_ahead=False â†’ copy only files that don't exist locally
                           (for equal-rank projects, mtime is used as tiebreaker)

    Returns count of files written.
    """
    if not src_root.exists():
        return 0
    written = 0
    for src in src_root.rglob("*"):
        if not src.is_file():
            continue
        src_str = str(src)
        if any(p in src_str for p in skip_patterns):
            continue
        rel = src.relative_to(src_root)
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(str(src), str(dst))
            written += 1
        elif remote_ahead:
            # Remote is further along â€” trust its files unconditionally
            shutil.copy2(str(src), str(dst))
            written += 1
        else:
            # Same rank â€” use mtime as tiebreaker (git resets mtime, so
            # this only helps for genuinely concurrent runs, not pulls)
            if src.stat().st_mtime > dst.stat().st_mtime:
                shutil.copy2(str(src), str(dst))
                written += 1
    return written


def import_zip(zip_path: pathlib.Path) -> None:
    print(f"\n{'='*60}")
    print(f"  ðŸ“¦ Importing: {zip_path.name}")
    print(f"{'='*60}\n")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = pathlib.Path(tmp_dir)

        # Extract
        print("  Extracting...")
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            zf.extractall(tmp_dir)

        # Find the .pipeline dir inside the zip
        pipeline_candidates = list(tmp.rglob(".pipeline"))
        if not pipeline_candidates:
            print("  ERROR: no .pipeline/ directory found in zip")
            sys.exit(1)

        # Use the shallowest .pipeline (shortest path = zip root)
        remote_pipeline = min(pipeline_candidates, key=lambda p: len(p.parts))
        print(f"  Found .pipeline at: {remote_pipeline.relative_to(tmp)}")

        # Process each project
        remote_projects = remote_pipeline / "projects"
        if not remote_projects.exists():
            print("  No projects/ dir found in zip â€” nothing to import")
            return

        SKIP = (".pytest_cache", "__pycache__", "opportunity_pipelines")

        total_files_merged = 0
        for remote_proj in sorted(remote_projects.iterdir()):
            if not remote_proj.is_dir():
                continue

            slug = remote_proj.name
            local_proj = project_dir(slug)
            print(f"\n  ðŸ“ Project: {slug}")

            # Fix double-nesting before merging
            double_fixed = fix_double_workspace(remote_proj)
            if double_fixed:
                print(f"    âœ‚ï¸  Fixed workspace/workspace/ double-nesting ({double_fixed} files)")

            # Fix stray phases
            stray_fixed = fix_stray_phases(remote_proj)
            if stray_fixed:
                print(f"    âœ‚ï¸  Fixed {stray_fixed} stray phase files")

            # â”€â”€ State merge: determines who is "ahead" â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            remote_state = remote_proj / "state" / "current_idea.json"
            local_state  = local_proj  / "state" / "current_idea.json"
            remote_ahead = False
            if remote_state.exists():
                updated, delta = merge_state(local_state, remote_state)
                remote_ahead = delta > 0  # remote has higher status rank
                if updated:
                    state = json.loads(remote_state.read_text())
                    print(f"    ðŸ“Š State updated â†’ {state.get('status','?')} "
                          f"phase {state.get('phase','?')}/{state.get('total_phases','?')}")
                else:
                    if local_state.exists():
                        state = json.loads(local_state.read_text())
                        arrow = "ahead" if delta < 0 else "same"
                        print(f"    ðŸ“Š State kept (local is {arrow}): {state.get('status','?')}")

            # â”€â”€ Workspace files â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # If remote is further along, its workspace files win unconditionally.
            # This fixes the git-clone mtime reset problem where git-pulled files
            # appear "newer" than zip files from a completed cloud run.
            ws_written = merge_files(
                remote_proj / "workspace",
                local_proj  / "workspace",
                remote_ahead=remote_ahead,
                skip_patterns=SKIP,
            )

            # â”€â”€ Phase files â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            ph_written = merge_files(
                remote_proj / "phases",
                local_proj  / "phases",
                remote_ahead=remote_ahead,
            )

            proj_files = ws_written + ph_written
            lead = "⬆️   remote ahead" if remote_ahead else "local ahead/tied"
            print(f"    📄 Merged {proj_files} file(s)  [{lead}]")
            total_files_merged += proj_files

        print(f"\n  ✅ Import complete — {total_files_merged} total file(s) merged")

    # Print manifest
    print_manifest()

    # Auto-generate import report
    write_import_report(get_pipeline_dir())


def print_manifest() -> None:
    """Print a clean manifest of all projects and their key file counts."""
    projects_root = projects_dir()
    if not projects_root.exists():
        return

    print(f"\n{'='*60}")
    print(f"  ðŸ“‹ Project Manifest")
    print(f"{'='*60}")

    for proj_dir in sorted(projects_root.iterdir()):
        if not proj_dir.is_dir():
            continue

        state_file = proj_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        slug   = proj_dir.name
        status = state.get("status", "?")
        phase  = state.get("phase", "?")
        total  = state.get("total_phases", "?")
        title  = state.get("title", slug)

        ws = proj_dir / "workspace"
        py_files = list(ws.rglob("*.py")) if ws.exists() else []
        py_files = [f for f in py_files if "__pycache__" not in str(f)]

        test_files = [f for f in py_files if f.name.startswith("test_")]
        source_files = [f for f in py_files if not f.name.startswith("test_")]

        has_master_plan = (proj_dir / "state" / "master_plan.md").exists()

        phases_done = []
        for i in range(1, 7):
            tasks_f = proj_dir / f"phases/phase_{i}/tasks.md"
            if tasks_f.exists():
                content = tasks_f.read_text(encoding="utf-8", errors="ignore")
                done = content.count("- [x]")
                total_t = content.count("- [ ]") + done
                if total_t:
                    phases_done.append(f"p{i}:{done}/{total_t}")

        print(f"\n  [{slug}]")
        print(f"    Title:   {title[:55]}")
        print(f"    Status:  {status}  (phase {phase}/{total})")
        print(f"    Plan:    {'âœ…' if has_master_plan else 'âŒ MISSING'}")
        print(f"    Source:  {len(source_files)} .py files")
        print(f"    Tests:   {len(test_files)} test files")
        if phases_done:
            print(f"    Tasks:   {' | '.join(phases_done)}")

        # Warn about double-nesting
        if (ws / "workspace").exists():
            print(f"    âš ï¸  workspace/workspace/ double-nesting detected â€” run this script to fix")

    print(f"\n{'='*60}\n")


def write_import_report(pipeline_dir: pathlib.Path) -> pathlib.Path:
    """Write .pipeline/state/last_import_report.md summarising project states.

    Called after every import to give a quick human-readable snapshot.
    Returns the path of the written report.
    """
    projects_dir = pipeline_dir / "projects"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Import Report — {now}",
        "",
        "| Project | Status | Phase | Notes |",
        "|---|---|---|---|",
    ]

    complete, budget_exc, in_prog, missing = [], [], [], []

    if projects_dir.exists():
        for proj_dir in sorted(projects_dir.iterdir()):
            if not proj_dir.is_dir():
                continue
            sf = proj_dir / "state" / "current_idea.json"
            if not sf.exists():
                missing.append(proj_dir.name)
                continue
            try:
                s = json.loads(sf.read_text(encoding="utf-8"))
            except Exception:
                missing.append(proj_dir.name)
                continue
            status = s.get("status", "?")
            phase  = s.get("phase", "?")
            total  = s.get("total_phases", "?")
            title  = s.get("title", proj_dir.name)[:40]
            note   = ""
            if status == "complete":
                try:
                    if int(phase) < int(total):
                        note = f"⚠ only p{phase}/{total} done"
                except Exception:
                    pass
                complete.append((proj_dir.name, phase, total, title, note))
            elif status == "budget_exceeded":
                pre = s.get("pre_budget_status", "")
                note = s.get("budget_note", "")[:60]
                budget_exc.append((proj_dir.name, phase, total, title, note))
            else:
                in_prog.append((proj_dir.name, status, phase, total, title))

    for row in complete:
        slug, phase, total, title, note = row
        lines.append(f"| {slug} | complete | p{phase}/{total} | {note} |")
    for row in budget_exc:
        slug, phase, total, title, note = row
        lines.append(f"| {slug} | **budget_exceeded** | p{phase}/{total} | {note} |")
    for row in in_prog:
        slug, status, phase, total, title = row
        lines.append(f"| {slug} | {status} | p{phase}/{total} | in progress |")
    if missing:
        lines.append("")
        lines.append(f"**Missing state files:** {', '.join(missing)}")

    lines += [
        "",
        f"**Summary:** {len(complete)} complete | {len(budget_exc)} budget_exceeded | {len(in_prog)} in-progress",
        "",
        "Run `python pipeline/runner.py --polish` to resume projects with missing phases.",
        "Run `python pipeline/runner.py --from-list` to retry budget_exceeded projects.",
    ]

    report_path = pipeline_dir / "state" / "last_import_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n  [import] Report written to {report_path.relative_to(pipeline_dir.parent)}")
    return report_path


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "manifest":
        print_manifest()
    elif sys.argv[1] == "latest":
        import_zip(find_latest_zip())
    else:
        zip_path = pathlib.Path(sys.argv[1])
        if not zip_path.exists():
            print(f"ERROR: {zip_path} does not exist")
            sys.exit(1)
        import_zip(zip_path)
