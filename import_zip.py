#!/usr/bin/env python3
"""
import_zip.py — Smart selective importer for pipeline_extract_*.zip files.

Only imports files that are NEW or CHANGED vs what's already on disk.
Skips files that are identical. Shows a summary before writing.

Usage:
    python import_zip.py                              # auto-finds latest zip in Downloads
    python import_zip.py path/to/pipeline_extract.zip
    python import_zip.py --dry-run                    # preview without writing
    python import_zip.py --project newsletter         # one project only
    python import_zip.py --only-state                 # state + phases only, no workspace code
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
import zipfile

from pipeline.pipeline_config import PROJECT_ROOT, get_pipeline_dir


# Locations to search for zips when no path is given (newest match wins)
_AUTO_SEARCH_DIRS = [
    pathlib.Path.home() / "Downloads",
    pathlib.Path.home() / "Desktop",
    pathlib.Path("."),
]



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_latest_zip() -> pathlib.Path | None:
    """Find the most recently modified pipeline_extract_*.zip across search dirs."""
    candidates = []
    for d in _AUTO_SEARCH_DIRS:
        if d.is_dir():
            candidates.extend(d.glob("pipeline_extract_*.zip"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def file_hash(path: pathlib.Path) -> str:
    """MD5 of a file, empty string if unreadable."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def zip_entry_hash(zf: zipfile.ZipFile, name: str) -> str:
    try:
        return hashlib.md5(zf.read(name)).hexdigest()
    except Exception:
        return ""


def should_skip(name: str) -> bool:
    """Skip files we never want to import."""
    parts = pathlib.PurePosixPath(name).parts
    skip_dirs = {"__pycache__", ".pytest_cache", "node_modules", ".venv", ".git"}
    if any(p in skip_dirs for p in parts):
        return True
    if name.endswith((".pyc", ".pyo", ".log")):
        return True
    if "MANIFEST.json" == pathlib.PurePosixPath(name).name:
        return True
    # Do not re-import repo infrastructure leaked into project workspaces
    try:
        from pipeline.path_health import should_skip_zip_workspace_path
        if should_skip_zip_workspace_path(name):
            return True
    except ImportError:
        pass
    return False


def resolve_import_dest(explicit: str) -> tuple[pathlib.Path, bool, pathlib.Path]:
    """
    Return (dest_root, strip_pipeline_prefix, factory_root).

    Cloud zips use paths like `.pipeline/projects/...` under the factory root.
    Local output lives in ../thepipeline with `projects/` at repo root (no .pipeline/).
    """
    factory = PROJECT_ROOT.resolve()
    pipeline_dir = get_pipeline_dir().resolve()
    nested = (factory / ".pipeline").resolve()

    if explicit and explicit not in (".", ""):
        dest = pathlib.Path(explicit).expanduser().resolve()
        if dest == factory:
            return dest, False, factory
        if dest == pipeline_dir or (dest / "projects").is_dir():
            return dest, True, factory
        return dest, False, factory

    if pipeline_dir == nested:
        return factory, False, factory
    return pipeline_dir, True, factory


def dest_path_for_entry(
    name: str,
    dest_root: pathlib.Path,
    strip_pipeline_prefix: bool,
    factory_root: pathlib.Path,
) -> pathlib.Path:
    """Map a zip entry path to the on-disk destination."""
    if name in ("polish_queue.md", "master_ideas.md"):
        return factory_root / name
    parts = pathlib.PurePosixPath(name).parts
    if strip_pipeline_prefix and parts and parts[0] == ".pipeline":
        return dest_root.joinpath(*parts[1:])
    return dest_root / name


def project_slug_from_entry(name: str) -> str | None:
    parts = pathlib.PurePosixPath(name).parts
    if len(parts) >= 3 and parts[0] == ".pipeline" and parts[1] == "projects":
        return parts[2]
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smart selective importer for pipeline zip files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("zip_file", nargs="?", default=None,
                        help="Path to pipeline_extract_*.zip (auto-detects latest in Downloads if omitted)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Show what would be imported without writing anything")
    parser.add_argument("--project", "-p", default="",
                        help="Only import files for a specific project slug (partial match ok)")
    parser.add_argument("--only-state", action="store_true",
                        help="Only import state/ and phases/ files (skip workspace code)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip importing files for projects that already exist on disk")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt and import immediately")
    parser.add_argument(
        "--dest",
        default="",
        help="Destination root (default: auto — ../thepipeline locally, idea impl/.pipeline on cloud)",
    )
    args = parser.parse_args()

    zip_path: pathlib.Path | None = None
    if args.zip_file:
        zip_path = pathlib.Path(args.zip_file).resolve()
        if not zip_path.exists():
            # Try glob in cwd
            matches = sorted(pathlib.Path(".").glob(args.zip_file))
            if matches:
                zip_path = max(matches, key=lambda p: p.stat().st_mtime)
                print(f"  Using: {zip_path.name}")
            else:
                print(f"ERROR: File not found: {args.zip_file}")
                sys.exit(1)
    else:
        zip_path = find_latest_zip()
        if not zip_path:
            print("ERROR: No pipeline_extract_*.zip found in Downloads, Desktop, or current directory.")
            print("       Pass the path explicitly: python import_zip.py /path/to/file.zip")
            sys.exit(1)
        print(f"  Auto-detected: {zip_path}")

    dest_root, strip_prefix, factory_root = resolve_import_dest(args.dest)
    layout = "thepipeline (strip .pipeline/)" if strip_prefix else "nested .pipeline under dest"
    print(f"  Layout:   {layout}")

    new_files     = []
    changed_files = []
    skipped_same  = []
    skipped_filter = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        all_names = [n for n in zf.namelist() if not n.endswith("/")]

        for name in all_names:
            if should_skip(name):
                continue

            # Project filter
            if args.project and args.project.lower() not in name.lower():
                skipped_filter.append(name)
                continue

            # Skip-existing filter: skip any file belonging to a project
            # that already has a directory on disk
            if args.skip_existing:
                slug = project_slug_from_entry(name)
                if slug:
                    if strip_prefix:
                        existing_proj_dir = dest_root / "projects" / slug
                    else:
                        existing_proj_dir = dest_root / ".pipeline" / "projects" / slug
                    if existing_proj_dir.is_dir():
                        skipped_filter.append(name)
                        continue

            # Only-state filter: skip workspace/ files
            if args.only_state:
                p = pathlib.PurePosixPath(name)
                # Keep: state/, phases/, shared_libs/, queues/, master_ideas.md
                # Skip: projects/<slug>/workspace/
                parts = p.parts
                is_workspace = (
                    len(parts) >= 4
                    and parts[0] == ".pipeline"
                    and parts[1] == "projects"
                    and parts[3] == "workspace"
                )
                if is_workspace:
                    skipped_filter.append(name)
                    continue

            dest_file = dest_path_for_entry(name, dest_root, strip_prefix, factory_root)
            if not dest_file.exists():
                new_files.append(name)
            else:
                zh = zip_entry_hash(zf, name)
                fh = file_hash(dest_file)
                if zh != fh:
                    changed_files.append(name)
                else:
                    skipped_same.append(name)

        # Summary
        print(f"\n  Zip:      {zip_path.name}")
        print(f"  Dest:     {dest_root}")
        if args.project:
            print(f"  Filter:   --project '{args.project}'")
        if args.only_state:
            print(f"  Filter:   --only-state (skipping workspace code)")
        if args.skip_existing:
            print(f"  Filter:   --skip-existing (skipping projects already on disk)")
        print(f"\n  New files:      {len(new_files):4d}")
        print(f"  Changed files:  {len(changed_files):4d}")
        print(f"  Unchanged:      {len(skipped_same):4d}  (skipped)")
        print(f"  Filtered out:   {len(skipped_filter):4d}  (skipped)")

        if not new_files and not changed_files:
            print("\n  Nothing to import — everything is already up to date.")
            return

        print(f"\n  Files to import ({len(new_files) + len(changed_files)}):")
        for name in (new_files + changed_files)[:40]:
            tag = " NEW" if name in new_files else "CHNG"
            print(f"    [{tag}] {name}")
        if len(new_files) + len(changed_files) > 40:
            print(f"    ... and {len(new_files)+len(changed_files)-40} more")

        if args.dry_run:
            print(f"\n  [DRY RUN] No files written. Remove --dry-run to import.")
            return

        if not args.yes:
            confirm = input(f"\n  Import {len(new_files)+len(changed_files)} files? [y/N] ").strip().lower()
            if confirm != "y":
                print("  Aborted.")
                return

        written = 0
        for name in new_files + changed_files:
            dest_file = dest_path_for_entry(name, dest_root, strip_prefix, factory_root)
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(zf.read(name))
            written += 1

        print(f"\n  Imported {written} files to {dest_root}")
        ps = (dest_root / "state" / "polish_status.json") if strip_prefix else (
            dest_root / ".pipeline" / "state" / "polish_status.json"
        )
        pq = factory_root / "polish_queue.md"
        if pq.exists():
            print(f"  Polish queue imported: {pq.name}")
        if ps.exists():
            try:
                import json as _json
                st = _json.loads(ps.read_text(encoding="utf-8"))
                print(f"  Last polish run: {st.get('run_state', '?')} — {st.get('reason', '')}")
            except Exception:
                pass
        print("  After import: python reset_budget_exceeded.py --generate-polish")
        print("                python pipeline/runner.py --polish ...")
        try:
            sys.path.insert(0, str(factory_root))
            from pipeline.pipeline_mode import legacy_mode

            if not legacy_mode():
                from pathlib import Path as _Path

                export_candidates = [
                    dest_root / "state/capability_registry_export.json",
                    dest_root / ".pipeline/state/capability_registry_export.json",
                    factory_root / "capability_registry_export.json",
                ]
                merged = False
                for exp in export_candidates:
                    if exp.exists():
                        from pipeline.capability_sync import merge_snapshot

                        mstats = merge_snapshot(exp)
                        print(
                            f"  Registry merged from {exp.name}: "
                            f"+{mstats.get('inserted_capabilities', 0)} caps, "
                            f"~{mstats.get('updated_capabilities', 0)} updated, "
                            f"from {mstats.get('from_instance', '?')}"
                        )
                        merged = True
                        break
                if not merged:
                    from pipeline.capability_registry import rebuild_registry

                    stats = rebuild_registry()
                    print(
                        f"  Registry rebuilt: {stats.get('total', 0)} capabilities, "
                        f"{stats.get('edges', 0)} edges, fts={stats.get('fts_indexed', 0)}"
                    )
        except Exception as _reg_err:
            print(f"  [registry] rebuild skipped: {_reg_err}")
        print(f"  Done.")


if __name__ == "__main__":
    main()
