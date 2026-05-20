#!/usr/bin/env python3
"""
extract.py — Pipeline output extractor.

Creates a timestamped zip of all built projects from .pipeline/projects/.
Run from any directory; will auto-locate the pipeline.

Usage:
    python extract.py                   # zip everything, save next to .pipeline/
    python extract.py --out ~/Desktop  # custom output directory
    python extract.py --workspace-only  # only include generated code (not state/phases)
    python extract.py --list            # just print a summary, don't zip

Example:
    python /workspace/idea\\ impl/extract.py
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import zipfile
from datetime import datetime


# ---------------------------------------------------------------------------
# Locate .pipeline/
# ---------------------------------------------------------------------------

def find_pipeline_dir() -> pathlib.Path:
    """Search upward from cwd and common locations for .pipeline/"""
    candidates = [
        pathlib.Path.cwd() / ".pipeline",
        pathlib.Path("/workspace") / ".pipeline",
        pathlib.Path("/workspace/idea impl") / ".pipeline",
    ]
    # Also search cwd parents
    for parent in pathlib.Path.cwd().parents:
        candidates.append(parent / ".pipeline")

    for c in candidates:
        if c.is_dir() and (c / "projects").is_dir():
            return c

    print("ERROR: Could not find .pipeline/projects/ directory.")
    print("Run this script from your workspace, or check that the pipeline has run at least once.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def read_idea_state(project_dir: pathlib.Path) -> dict:
    state_file = project_dir / "state" / "current_idea.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def count_phases(project_dir: pathlib.Path) -> int:
    phases_dir = project_dir / "phases"
    if not phases_dir.exists():
        return 0
    return len([d for d in phases_dir.iterdir() if d.is_dir()])


def count_workspace_files(project_dir: pathlib.Path) -> int:
    ws = project_dir / "workspace"
    if not ws.exists():
        return 0
    return sum(1 for f in ws.rglob("*") if f.is_file() and not f.name.startswith("."))


def get_project_summary(project_dir: pathlib.Path) -> dict:
    state = read_idea_state(project_dir)
    return {
        "slug":           project_dir.name,
        "title":          state.get("title", project_dir.name),
        "status":         state.get("status", "?"),
        "total_phases":   state.get("total_phases", "?"),
        "phases_built":   count_phases(project_dir),
        "workspace_files": count_workspace_files(project_dir),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def print_summary(projects_dir: pathlib.Path) -> list[dict]:
    projects = sorted(projects_dir.iterdir()) if projects_dir.exists() else []
    summaries = []
    print(f"\n{'─'*65}")
    print(f"  {'SLUG':<30} {'STATUS':<22} {'PHASES':>6} {'FILES':>5}")
    print(f"{'─'*65}")
    for p in projects:
        if not p.is_dir():
            continue
        s = get_project_summary(p)
        summaries.append(s)
        print(f"  {s['slug']:<30} {s['status']:<22} {s['phases_built']:>6} {s['workspace_files']:>5}")
    print(f"{'─'*65}")
    print(f"  {len(summaries)} projects total\n")
    return summaries


def _normalize_queue_line(line: str) -> str:
    """Reset 'processing' status to 'pending' so restored queues are immediately ready."""
    try:
        d = json.loads(line)
        if d.get("status") == "processing":
            d["status"] = "pending"
            return json.dumps(d)
    except Exception:
        pass
    return line


def build_zip(
    pipeline_dir: pathlib.Path,
    out_dir: pathlib.Path,
    workspace_only: bool,
) -> tuple[pathlib.Path, int]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"pipeline_extract_{timestamp}.zip"
    zip_path = out_dir / zip_name

    projects_dir = pipeline_dir / "projects"
    included = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:

        # --- Project files ---
        for project_dir in sorted(projects_dir.iterdir()):
            if not project_dir.is_dir():
                continue

            roots = [project_dir / "workspace"] if workspace_only else [project_dir]

            for root in roots:
                if not root.exists():
                    continue
                for file in root.rglob("*"):
                    if not file.is_file():
                        continue
                    if file.name.startswith(".") and file.suffix not in (".md", ".json"):
                        continue
                    arcname = file.relative_to(pipeline_dir.parent)
                    zf.write(file, arcname)
                    included += 1

        # --- Queues (normalize processing→pending for clean resume) ---
        if not workspace_only:
            queues_dir = pipeline_dir / "queues"
            if queues_dir.exists():
                for qfile in queues_dir.glob("*.jsonl"):
                    lines = qfile.read_text(encoding="utf-8", errors="ignore").splitlines()
                    normalized = "\n".join(_normalize_queue_line(l) for l in lines if l.strip())
                    arcname = str(qfile.relative_to(pipeline_dir.parent))
                    zf.writestr(arcname, normalized + "\n" if normalized else "")
                    included += 1

            # --- Global state ---
            state_dir = pipeline_dir / "state"
            if state_dir.exists():
                for sf in state_dir.glob("*.json"):
                    arcname = sf.relative_to(pipeline_dir.parent)
                    zf.write(sf, arcname)
                    included += 1
                # Also include reusable_tools.md (the shared library index)
                rtmd = state_dir / "reusable_tools.md"
                if rtmd.exists():
                    zf.write(rtmd, rtmd.relative_to(pipeline_dir.parent))
                    included += 1

            # --- Shared libs (reusable tool library accumulated across projects) ---
            shared_libs_dir = pipeline_dir / "shared_libs"
            if shared_libs_dir.exists():
                for file in shared_libs_dir.rglob("*"):
                    if not file.is_file():
                        continue
                    if file.name.startswith("."):
                        continue
                    arcname = file.relative_to(pipeline_dir.parent)
                    zf.write(file, arcname)
                    included += 1

        # --- master_ideas.md ---
        mi = pipeline_dir.parent / "master_ideas.md"
        if mi.exists():
            zf.write(mi, mi.name)

        # --- Manifest ---
        # Count shared_libs files for manifest
        shared_libs_count = 0
        shared_libs_dir = pipeline_dir / "shared_libs"
        if shared_libs_dir.exists():
            shared_libs_count = sum(1 for f in shared_libs_dir.rglob("*") if f.is_file())

        summaries = [
            get_project_summary(p)
            for p in sorted(projects_dir.iterdir())
            if p.is_dir()
        ]
        manifest = {
            "extracted_at": datetime.now().isoformat(),
            "workspace_only": workspace_only,
            "files_included": included,
            "shared_libs_included": shared_libs_count,
            "resume_instructions": (
                "1. git pull on new instance\n"
                "2. unzip this file into /workspace/idea\\ impl/\n"
                "3. python pipeline/runner.py --from-list --provider ollama --model qwen3.5:35b\n"
                "   Runner will auto-detect in-progress projects and re-queue them.\n"
                "   Shared libs are in .pipeline/shared_libs/ — executor uses them automatically."
            ),
            "projects": summaries,
        }
        zf.writestr("MANIFEST.json", json.dumps(manifest, indent=2))

    return zip_path, included



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract pipeline output to a zip file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--out", "-o",
        default=None,
        help="Output directory for the zip (default: same directory as .pipeline/)",
    )
    parser.add_argument(
        "--workspace-only", "-w",
        action="store_true",
        help="Only include generated code (workspace/), skip phases and state files",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Print a project summary and exit without creating a zip",
    )
    parser.add_argument(
        "--pipeline-dir",
        default=None,
        help="Explicit path to .pipeline/ directory (auto-detected if omitted)",
    )
    parser.add_argument(
        "--snapshot", "-s",
        action="store_true",
        help="Include prompt snapshot, metrics report, and diff from baseline in the zip",
    )
    parser.add_argument(
        "--sync-ideas",
        action="store_true",
        help="Trim completed ideas from master_ideas.md using truth.md / completions.jsonl (no zip)",
    )
    parser.add_argument(
        "--rebuild-truth",
        action="store_true",
        help="Regenerate truth.md from completions registry and complete projects",
    )
    parser.add_argument(
        "--ideas-file",
        default=None,
        help="Ideas markdown to sync (default: master_ideas.md next to .pipeline/)",
    )
    args = parser.parse_args()

    # Locate pipeline
    if args.pipeline_dir:
        pipeline_dir = pathlib.Path(args.pipeline_dir).resolve()
    else:
        pipeline_dir = find_pipeline_dir()

    print(f"\n  Pipeline dir : {pipeline_dir}")
    projects_dir = pipeline_dir / "projects"

    sys.path.insert(0, str(pipeline_dir.parent))

    if args.rebuild_truth:
        from pipeline.ideas_sync import rebuild_truth_from_registry
        n = rebuild_truth_from_registry(projects_dir=projects_dir)
        print(f"\n  Rebuilt truth.md with {n} completion(s)\n")
        return

    if args.sync_ideas:
        ideas_path = (
            pathlib.Path(args.ideas_file).resolve()
            if args.ideas_file
            else pipeline_dir.parent / "master_ideas.md"
        )
        from pipeline.ideas_sync import trim_completed_from_master_ideas
        n = trim_completed_from_master_ideas(ideas_path, projects_dir=projects_dir)
        print(f"\n  Done — {n} completed idea(s) trimmed from {ideas_path.name}\n")
        return

    summaries = print_summary(projects_dir)

    if args.list:
        return

    if not summaries:
        print("  No projects found — nothing to extract.")
        return

    out_dir = pathlib.Path(args.out).resolve() if args.out else pipeline_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    label = "workspace only" if args.workspace_only else "full (workspace + phases + state)"
    if args.snapshot:
        label += " + audit snapshot"
    print(f"  Extracting   : {label}")
    print(f"  Output dir   : {out_dir}")
    print(f"  Building zip ", end="", flush=True)

    zip_path, count = build_zip(pipeline_dir, out_dir, args.workspace_only)

    # Inject audit snapshot into the zip
    if args.snapshot:
        with zipfile.ZipFile(zip_path, "a", zipfile.ZIP_DEFLATED) as zf:
            # Include current prompt files
            prompts_dir = pipeline_dir.parent / "pipeline" / "prompts"
            if prompts_dir.exists():
                for f in sorted(prompts_dir.glob("*.md")):
                    zf.write(f, f"_audit/prompts/{f.name}")

            # Include constitution
            const = pipeline_dir.parent / "constitution.yaml"
            if const.exists():
                zf.write(const, "_audit/prompts/constitution.yaml")

            # Include prompt version metadata + diff from baseline
            versions_dir = pipeline_dir / "prompt_versions"
            if versions_dir.exists():
                # Find latest version
                versions = sorted(p for p in versions_dir.iterdir() if p.is_dir() and p.name.startswith("v"))
                if versions:
                    latest = versions[-1]
                    for f in latest.iterdir():
                        zf.write(f, f"_audit/prompt_version/{f.name}")

            # Include latest metrics report
            metrics_dir = pipeline_dir / "metrics"
            if metrics_dir.exists():
                runs = sorted(p for p in metrics_dir.iterdir() if p.is_dir())
                if runs:
                    latest_run = runs[-1]
                    for f in latest_run.iterdir():
                        zf.write(f, f"_audit/metrics/{f.name}")

    print(f"done.")
    snapshot_note = " (with audit snapshot)" if args.snapshot else ""
    print(f"\n  ✅  {zip_path.name}{snapshot_note}")
    print(f"      {count:,} files  |  {zip_path.stat().st_size / 1024 / 1024:.1f} MB\n")

    # Optional trim after extract (keeps master_ideas queue clean vs truth)
    ideas_path = pipeline_dir.parent / "master_ideas.md"
    if ideas_path.exists():
        try:
            from pipeline.ideas_sync import trim_completed_from_master_ideas
            n = trim_completed_from_master_ideas(ideas_path, projects_dir=projects_dir, verbose=False)
            if n:
                print(f"  [truth] trimmed {n} completed idea(s) from {ideas_path.name}\n")
        except Exception:
            pass


if __name__ == "__main__":
    main()
