#!/usr/bin/env python3
"""
Merge pipeline output from idea impl/.pipeline/ into the canonical output repo.

Use after import_zip.py wrote cloud-style paths into the factory tree instead of
../thepipeline (local sibling output repo).

  python scripts/merge_nested_pipeline.py --dry-run
  python scripts/merge_nested_pipeline.py --yes
  python scripts/merge_nested_pipeline.py --yes --remove-source
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from import_cloud_zip import merge_files, merge_state, status_rank  # noqa: E402
from pipeline.pipeline_config import PROJECT_ROOT, get_pipeline_dir  # noqa: E402


def _nested_pipeline_dir() -> Path:
    return (PROJECT_ROOT / ".pipeline").resolve()


def merge_nested_pipeline(
    *,
    dry_run: bool = False,
    remove_source: bool = False,
) -> int:
    src_root = _nested_pipeline_dir()
    dst_root = get_pipeline_dir().resolve()

    if not src_root.is_dir():
        print(f"Nothing to merge — missing {src_root}")
        return 0
    if src_root == dst_root:
        print(f"Source and destination are the same: {dst_root}")
        return 0

    print(f"  Source:      {src_root}")
    print(f"  Destination: {dst_root}")
    if dry_run:
        print("  [DRY RUN]")

    total_written = 0
    src_projects = src_root / "projects"
    dst_projects = dst_root / "projects"

    if src_projects.is_dir():
        for src_proj in sorted(src_projects.iterdir()):
            if not src_proj.is_dir():
                continue
            slug = src_proj.name
            dst_proj = dst_projects / slug
            print(f"\n  Project: {slug}")

            remote_state = src_proj / "state" / "current_idea.json"
            local_state = dst_proj / "state" / "current_idea.json"
            remote_ahead = False
            if remote_state.exists():
                if dry_run:
                    try:
                        r_data = json.loads(remote_state.read_text(encoding="utf-8"))
                        r_rank = status_rank(r_data.get("status", ""))
                        l_rank = -1
                        if local_state.exists():
                            l_data = json.loads(local_state.read_text(encoding="utf-8"))
                            l_rank = status_rank(l_data.get("status", ""))
                        remote_ahead = r_rank > l_rank
                        print(
                            f"    state: remote={r_data.get('status', '?')} "
                            f"local={'?' if not local_state.exists() else l_data.get('status', '?')} "
                            f"→ {'remote wins' if remote_ahead else 'local wins / new only'}"
                        )
                    except Exception as exc:
                        print(f"    state: (could not compare: {exc})")
                else:
                    updated, delta = merge_state(local_state, remote_state)
                    remote_ahead = delta > 0
                    if updated:
                        state = json.loads(remote_state.read_text(encoding="utf-8"))
                        print(f"    state updated → {state.get('status', '?')}")
                    elif local_state.exists():
                        state = json.loads(local_state.read_text(encoding="utf-8"))
                        print(f"    state kept (local): {state.get('status', '?')}")

            if dry_run:
                for sub in ("workspace", "phases"):
                    sub_src = src_proj / sub
                    if not sub_src.is_dir():
                        continue
                    new = sum(
                        1
                        for f in sub_src.rglob("*")
                        if f.is_file()
                        and not (dst_proj / sub / f.relative_to(sub_src)).exists()
                    )
                    print(f"    would merge {sub}/ ({new} new files under {sub}/)")
                continue

            skip = (".pytest_cache", "__pycache__", "opportunity_pipelines")
            ws_written = merge_files(
                src_proj / "workspace",
                dst_proj / "workspace",
                remote_ahead=remote_ahead,
                skip_patterns=skip,
            )
            ph_written = merge_files(
                src_proj / "phases",
                dst_proj / "phases",
                remote_ahead=remote_ahead,
            )
            proj_written = ws_written + ph_written
            total_written += proj_written
            print(f"    merged {proj_written} file(s)")

    for subdir in ("state", "shared_libs", "queues", "workflows", "memory", "metrics", "logs", "finetune_corpus", "prompt_versions"):
        src_sub = src_root / subdir
        if not src_sub.is_dir():
            continue
        if dry_run:
            count = sum(1 for f in src_sub.rglob("*") if f.is_file())
            print(f"\n  Would merge {subdir}/ ({count} files)")
            continue
        written = merge_files(src_sub, dst_root / subdir, remote_ahead=True)
        total_written += written
        if written:
            print(f"\n  Merged {subdir}/ ({written} files)")

    if dry_run:
        print("\n  [DRY RUN] No files written.")
        return 0

    print(f"\n  Done — merged {total_written} file(s) into {dst_root}")

    if remove_source:
        shutil.rmtree(src_root)
        print(f"  Removed {src_root}")

    try:
        export = dst_root / "state" / "capability_registry_export.json"
        if export.exists():
            from pipeline.capability_sync import merge_snapshot

            stats = merge_snapshot(export)
            print(
                f"  Registry: +{stats.get('inserted_capabilities', 0)} caps, "
                f"~{stats.get('updated_capabilities', 0)} updated"
            )
    except Exception as exc:
        print(f"  [registry] skipped: {exc}")

    return total_written


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge .pipeline/ nested under idea impl into thepipeline")
    parser.add_argument("--dry-run", "-n", action="store_true")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    parser.add_argument("--remove-source", action="store_true", help="Delete idea impl/.pipeline after merge")
    args = parser.parse_args()

    if not args.dry_run and not args.yes:
        confirm = input("Merge nested .pipeline into canonical output? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 1

    merge_nested_pipeline(dry_run=args.dry_run, remove_source=args.remove_source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
