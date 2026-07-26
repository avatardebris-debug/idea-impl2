#!/usr/bin/env python3
"""
Connector smoke runner — structural YAML checks + hard-coded process oracle.

Always writes goal_trace.v1 per case under $PIPELINE_DIR/goal_traces/.

Usage:
  set PIPELINE_DIR=C:\\Users\\avata\\aicompete\\thepipeline
  python scripts/connector_smoke.py
  python scripts/connector_smoke.py --slug movie_chain_n8n
  python scripts/connector_smoke.py --execute
  python scripts/connector_smoke.py --oracle-only
  python scripts/connector_smoke.py --json

Exit 0 = all HARD cases pass (process oracle + structural).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _maybe_bind_pipeline_dir(explicit: str) -> None:
    """Prefer explicit --pipeline-dir; else if default worktree .pipeline has no connectors,
    try ~/aicompete/thepipeline (same multi-root idea as truth_density)."""
    if explicit:
        os.environ["PIPELINE_DIR"] = explicit
        return
    if os.environ.get("PIPELINE_DIR", "").strip():
        return
    from pipeline.paths import connectors_dir

    cdir = connectors_dir()
    if cdir.is_dir() and any(cdir.glob("*.yaml")):
        return
    home_factory = Path.home() / "aicompete" / "thepipeline"
    if (home_factory / "workflows" / "connectors").is_dir():
        os.environ["PIPELINE_DIR"] = str(home_factory)
        try:
            from pipeline.paths import reload_pipeline_dir

            reload_pipeline_dir()
        except Exception:
            pass
        print(f"Using pipeline dir: {home_factory}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Connector structural smoke + hard-coded process oracle + goal_trace"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    ap.add_argument("--slug", default="", help="Only this connector slug (+ still runs process oracle)")
    ap.add_argument(
        "--execute",
        action="store_true",
        help="Also attempt run_workflow (force, native) per connector (soft)",
    )
    ap.add_argument(
        "--require-execute",
        action="store_true",
        help="Treat execute smoke as HARD (implies --execute)",
    )
    ap.add_argument(
        "--oracle-only",
        action="store_true",
        help="Only run the hard-coded process oracle",
    )
    ap.add_argument("--json", action="store_true", help="Print JSON report to stdout")
    ap.add_argument(
        "--work-dir",
        default="",
        help="Work dir for process oracle artifacts (default under metrics/)",
    )
    args = ap.parse_args()

    _maybe_bind_pipeline_dir(args.pipeline_dir)

    from pipeline.connector_smoke import run_connector_smoke, write_smoke_report
    from pipeline.paths import get_pipeline_dir

    pipeline_dir = get_pipeline_dir()
    if not pipeline_dir.is_dir():
        print(f"ERROR: pipeline dir missing: {pipeline_dir}", file=sys.stderr)
        return 2

    execute = bool(args.execute or args.require_execute)
    report = run_connector_smoke(
        slug=args.slug or None,
        execute=execute,
        require_execute=bool(args.require_execute),
        oracle_only=bool(args.oracle_only),
        work_dir=Path(args.work_dir) if args.work_dir else None,
    )
    paths = write_smoke_report(report)

    if args.json:
        payload = {
            "ok": report.ok,
            "ts": report.ts,
            "pipeline_dir": report.pipeline_dir,
            "cases": [
                {
                    "id": c.id,
                    "slug": c.slug,
                    "mode": c.mode,
                    "hard": c.hard,
                    "ok": c.ok,
                    "status": c.status,
                    "goal_id": c.goal_id,
                    "detail": c.detail,
                }
                for c in report.cases
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Report: {paths['markdown']}")
        print(f"JSON:   {paths['json']}")
        print(f"Overall HARD: {'PASS' if report.ok else 'FAIL'}")
        for c in report.cases:
            tag = "PASS" if c.ok else "FAIL"
            hard = "HARD" if c.hard else "soft"
            print(f"  [{tag}/{hard}] {c.id} status={c.status} goal={c.goal_id or '-'}")
            print(f"           {c.detail[:160]}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
