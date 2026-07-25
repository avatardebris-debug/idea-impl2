#!/usr/bin/env python3
"""Report field_proven per wall-clock hour (and per token when known)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Factory truth-density: field_proven per hour / per million tokens"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    ap.add_argument(
        "--since",
        default="",
        help="ISO start time or path to overnight log directory (with preflight.json)",
    )
    ap.add_argument("--until", default="", help="Optional ISO end time")
    ap.add_argument("--out", default="", help="Markdown output path")
    ap.add_argument(
        "--metrics-summary",
        default="",
        help="Optional path to metrics summary.json for token totals",
    )
    args = ap.parse_args()

    if args.pipeline_dir:
        os.environ["PIPELINE_DIR"] = args.pipeline_dir

    from pipeline.paths import get_pipeline_dir
    from pipeline.truth_density import build_report, write_report_outputs

    pipeline_dir = get_pipeline_dir()
    if not pipeline_dir.is_dir():
        print(f"ERROR: pipeline dir missing: {pipeline_dir}", file=sys.stderr)
        return 2

    report = build_report(
        pipeline_dir,
        since=args.since or None,
        until=args.until or None,
        metrics_summary_path=Path(args.metrics_summary) if args.metrics_summary else None,
    )

    out = Path(args.out) if args.out else None
    # If --since is overnight log dir, default out there
    if out is None and args.since:
        p = Path(args.since)
        if p.is_dir():
            out = p / "truth_density.md"

    paths = write_report_outputs(pipeline_dir, report, out_path=out)
    print(f"Report: {paths['markdown']}")
    print(f"History: {paths['history']}")
    print(
        f"Field proven: {report.field_proven.count} in {report.window.hours:.2f} wall hours"
        + (
            f" ({report.per_wall_hour:.2f}/hour)"
            if report.per_wall_hour is not None
            else ""
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
