#!/usr/bin/env python3
"""Print capability registry usage summary from capability_metrics.jsonl."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.capability_metrics import METRICS_LOG, summarize_metrics  # noqa: E402


def main() -> None:
    summary = summarize_metrics()
    print(f"Metrics log: {METRICS_LOG}")
    print(f"Total events: {summary['total_events']}")
    print("\nBy event:")
    for ev, n in sorted(summary.get("by_event", {}).items(), key=lambda x: -x[1]):
        print(f"  {ev:12} {n}")

    print("\nTop invoke:")
    for slug, counts in summary.get("top_invoke", []):
        fail = counts.get("invoke_fail", 0)
        extra = f" ({fail} fail)" if fail else ""
        print(f"  {slug:40} invoke={counts.get('invoke', 0)}{extra}")

    top_fail = summary.get("top_fail", [])
    if top_fail:
        print("\nHighest invoke failures:")
        for slug, counts in top_fail:
            print(f"  {slug:40} fail={counts.get('invoke_fail', 0)}")

    if "--json" in sys.argv:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
