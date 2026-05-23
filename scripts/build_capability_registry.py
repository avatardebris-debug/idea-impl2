#!/usr/bin/env python3
"""Build or refresh .pipeline/state/capability_registry.sqlite and CAPABILITIES.md."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.capability_registry import (  # noqa: E402
    REGISTRY_DB,
    list_capabilities,
    rebuild_registry,
)
from pipeline.pipeline_mode import legacy_mode, set_legacy_mode  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pipeline capability registry")
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Skip build (registry disabled; same as runner --legacy)",
    )
    parser.add_argument("--list", action="store_true", help="List verified capabilities")
    parser.add_argument("--domain", default=None, help="Filter --list by domain substring")
    parser.add_argument(
        "--graph",
        action="store_true",
        help="Write scripts/capability_graph.dot (Graphviz) after rebuild",
    )
    parser.add_argument(
        "--blocked",
        action="store_true",
        help="List master_ideas entries blocked by unmet requires:",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Print capability usage summary from capability_metrics.jsonl",
    )
    args = parser.parse_args()

    if args.legacy:
        set_legacy_mode(True)
        print("Legacy mode: capability registry build skipped.")
        return

    set_legacy_mode(False)
    stats = rebuild_registry()
    if stats.get("skipped"):
        print("Skipped:", stats.get("reason"))
        return

    print(f"Registry: {REGISTRY_DB}")
    print(
        f"  projects={stats.get('projects', 0)} "
        f"shared_libs={stats.get('shared_libs', 0)} "
        f"scripts={stats.get('pipeline_scripts', 0)} "
        f"workflows={stats.get('workflows', 0)} "
        f"edges={stats.get('edges', 0)} "
        f"pruned={stats.get('pruned', 0)} "
        f"fts={stats.get('fts_indexed', 0)} "
        f"total={stats.get('total', 0)}"
    )

    if args.metrics:
        from pipeline.capability_metrics import summarize_metrics

        m = summarize_metrics()
        print(f"  Metrics events: {m.get('total_events', 0)}")

    if args.graph:
        from pipeline.capability_graph import write_graphviz_dot

        dot = write_graphviz_dot()
        print(f"  Graphviz: {dot}")

    if args.blocked:
        from pipeline.capability_graph import blocked_unchecked_ideas

        for b in blocked_unchecked_ideas():
            print(f"  BLOCKED {b['slug']}: missing {b['missing']}")

    if args.list:
        for row in list_capabilities(domain=args.domain):
            ep = row.get("entrypoint") or ""
            print(f"  {row['slug']:40} {row['kind']:16} {ep}")


if __name__ == "__main__":
    main()
