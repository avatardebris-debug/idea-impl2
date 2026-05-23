#!/usr/bin/env python3
"""
Multi-instance capability registry sync.

Examples:
  # Export for git or zip handoff
  python scripts/sync_capability_registry.py export
  python scripts/sync_capability_registry.py export --out capability_registry_export.json

  # Merge remote export into this machine (after git pull or scp)
  python scripts/sync_capability_registry.py merge
  python scripts/sync_capability_registry.py merge --from /path/to/export.json

  # Full replace from another machine's sqlite (destructive)
  python scripts/sync_capability_registry.py replace --sqlite .pipeline/state/capability_registry.sqlite

  # Export + commit workflow helper
  CAPABILITY_SYNC_INSTANCE=vast-1 python scripts/sync_capability_registry.py export --metrics
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.pipeline_mode import set_legacy_mode  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync capability registry across instances")
    parser.add_argument("--legacy", action="store_true", help="No-op (registry disabled)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_exp = sub.add_parser("export", help="Write capability_registry_export.json")
    p_exp.add_argument(
        "--out",
        default=None,
        help="Output path (default: .pipeline/state/capability_registry_export.json)",
    )
    p_exp.add_argument(
        "--metrics",
        action="store_true",
        help="Include last 2000 capability_metrics.jsonl events",
    )
    p_exp.add_argument(
        "--copy-root",
        action="store_true",
        help="Also write capability_registry_export.json at repo root for git",
    )

    p_merge = sub.add_parser("merge", help="Merge export JSON into local sqlite")
    p_merge.add_argument(
        "--from",
        dest="from_path",
        default=None,
        help="Export JSON path (default: search standard locations)",
    )
    p_merge.add_argument(
        "--no-rebuild",
        action="store_true",
        help="Skip FTS/graph rebuild after merge",
    )

    p_rep = sub.add_parser("replace", help="Replace local DB from remote sqlite file")
    p_rep.add_argument(
        "--sqlite",
        required=True,
        help="Path to capability_registry.sqlite from other instance",
    )

    args = parser.parse_args()
    set_legacy_mode(args.legacy)

    if args.legacy:
        print("Legacy mode — sync skipped.")
        return

    from pipeline.capability_sync import (
        EXPORT_JSON,
        EXPORT_JSON_ALT,
        export_snapshot,
        find_export_file,
        merge_snapshot,
        replace_from_sqlite,
    )

    if args.cmd == "export":
        out = Path(args.out).resolve() if args.out else None
        path = export_snapshot(out, include_metrics=args.metrics)
        print(f"Exported: {path}")
        import json

        meta = json.loads(path.read_text(encoding="utf-8")).get("meta", {})
        print(f"  instance: {meta.get('instance')}")
        print(f"  capabilities: {meta.get('capabilities')}")
        print(f"  edges: {meta.get('edges')}")
        if args.copy_root:
            EXPORT_JSON_ALT.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  copy: {EXPORT_JSON_ALT}")
        return

    if args.cmd == "merge":
        src = Path(args.from_path).resolve() if args.from_path else find_export_file()
        if not src:
            print("No export file found. Run export on source instance first.")
            print(f"  Expected: {EXPORT_JSON} or capability_registry_export.json at repo root")
            sys.exit(1)
        stats = merge_snapshot(src, rebuild_fts=not args.no_rebuild)
        print(f"Merged from: {src}")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return

    if args.cmd == "replace":
        db = Path(args.sqlite).resolve()
        replace_from_sqlite(db)
        from pipeline.capability_registry import rebuild_registry

        stats = rebuild_registry()
        print(f"Replaced registry from {db}")
        print(f"  rebuild: {stats}")
        return


if __name__ == "__main__":
    main()
