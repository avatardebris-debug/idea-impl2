#!/usr/bin/env python3
"""
import_cloud_zip.py — Import a cloud run zip file into the local project.

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
import json
import pathlib
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
PIPELINE_DIR = PROJECT_ROOT / ".pipeline"

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
                # File conflict — keep newer
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
                print(f"    Moved stray: workspace/phases/{rel} → phases/{rel}")

    try:
        shutil.rmtree(str(stray_phases))
    except OSError:
        pass
    return moved


def merge_state(local: pathlib.Path, remote: pathlib.Path) -> bool:
    """
    Merge remote current_idea.json into local — keep whichever has a
    more advanced status or later timestamp.
    Returns True if local was updated.
    """
    STATUS_ORDER = [
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

    try:
        r_data = json.loads(remote.read_text(encoding="utf-8"))
        if local.exists():
            l_data = json.loads(local.read_text(encoding="utf-8"))
            r_status = r_data.get("status", "")
            l_status = l_data.get("status", "")
            r_rank = STATUS_ORDER.index(r_status) if r_status in STATUS_ORDER else -1
            l_rank = STATUS_ORDER.index(l_status) if l_status in STATUS_ORDER else -1
            if r_rank <= l_rank:
                return False  # local is same or further ahead
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(r_data, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def import_zip(zip_path: pathlib.Path) -> None:
    print(f"\n{'='*60}")
    print(f"  📦 Importing: {zip_path.name}")
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
            print("  No projects/ dir found in zip — nothing to import")
            return

        total_files_merged = 0
        for remote_proj in sorted(remote_projects.iterdir()):
            if not remote_proj.is_dir():
                continue

            slug = remote_proj.name
            local_proj = PIPELINE_DIR / "projects" / slug
            print(f"\n  📁 Project: {slug}")

            # Fix double-nesting before merging
            double_fixed = fix_double_workspace(remote_proj)
            if double_fixed:
                print(f"    ✂️  Fixed workspace/workspace/ double-nesting ({double_fixed} files)")

            # Fix stray phases
            stray_fixed = fix_stray_phases(remote_proj)
            if stray_fixed:
                print(f"    ✂️  Fixed {stray_fixed} stray phase files")

            # Merge state (smart: keep more advanced)
            remote_state = remote_proj / "state" / "current_idea.json"
            local_state  = local_proj  / "state" / "current_idea.json"
            if remote_state.exists():
                if merge_state(local_state, remote_state):
                    state = json.loads(remote_state.read_text())
                    print(f"    📊 State updated: {state.get('status','?')} phase {state.get('phase','?')}/{state.get('total_phases','?')}")
                else:
                    if local_state.exists():
                        state = json.loads(local_state.read_text())
                        print(f"    📊 State kept (local is ahead): {state.get('status','?')}")

            # Merge workspace files (copy all, newer wins)
            remote_ws = remote_proj / "workspace"
            local_ws  = local_proj  / "workspace"
            proj_files = 0
            if remote_ws.exists():
                for src in remote_ws.rglob("*"):
                    if src.is_file() and ".pytest_cache" not in str(src) and "__pycache__" not in str(src):
                        rel = src.relative_to(remote_ws)
                        dst = local_ws / rel
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        if not dst.exists():
                            shutil.copy2(str(src), str(dst))
                            proj_files += 1
                        else:
                            # Keep newer
                            if src.stat().st_mtime > dst.stat().st_mtime:
                                shutil.copy2(str(src), str(dst))
                                proj_files += 1

            # Merge phase files (tasks.md, specs, reports)
            remote_phases = remote_proj / "phases"
            local_phases  = local_proj  / "phases"
            if remote_phases.exists():
                for src in remote_phases.rglob("*"):
                    if src.is_file():
                        rel = src.relative_to(remote_phases)
                        dst = local_phases / rel
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        if not dst.exists():
                            shutil.copy2(str(src), str(dst))
                            proj_files += 1

            print(f"    📄 Merged {proj_files} file(s) into workspace/phases")
            total_files_merged += proj_files

        print(f"\n  ✅ Import complete — {total_files_merged} total file(s) merged")

    # Print manifest
    print_manifest()


def print_manifest() -> None:
    """Print a clean manifest of all projects and their key file counts."""
    projects_dir = PIPELINE_DIR / "projects"
    if not projects_dir.exists():
        return

    print(f"\n{'='*60}")
    print(f"  📋 Project Manifest")
    print(f"{'='*60}")

    for proj_dir in sorted(projects_dir.iterdir()):
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
        print(f"    Plan:    {'✅' if has_master_plan else '❌ MISSING'}")
        print(f"    Source:  {len(source_files)} .py files")
        print(f"    Tests:   {len(test_files)} test files")
        if phases_done:
            print(f"    Tasks:   {' | '.join(phases_done)}")

        # Warn about double-nesting
        if (ws / "workspace").exists():
            print(f"    ⚠️  workspace/workspace/ double-nesting detected — run this script to fix")

    print(f"\n{'='*60}\n")


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
