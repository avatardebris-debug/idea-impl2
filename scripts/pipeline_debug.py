#!/usr/bin/env python3
"""
Pipeline stall diagnostics — run from idea impl repo root.

  export PIPELINE_CLOUD=1   # on cloud
  python scripts/pipeline_debug.py
  python scripts/pipeline_debug.py --slug movie_player
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.message_bus import MessageBus
from pipeline.paths import get_pipeline_dir, projects_dir
from pipeline.pipeline_config import AGENT_ROLES
from pipeline.review_artifacts import review_artifacts_complete, validation_passed


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline stall diagnostics")
    parser.add_argument("--slug", default="", help="Focus one project slug")
    parser.add_argument("--all", action="store_true", help="List every project (default: in-progress only)")
    args = parser.parse_args()

    pipe = get_pipeline_dir()
    _section("Paths")
    print(f"PIPELINE_CLOUD={__import__('os').environ.get('PIPELINE_CLOUD', '')}")
    print(f"PIPELINE_DIR={__import__('os').environ.get('PIPELINE_DIR', '')}")
    print(f"get_pipeline_dir()={pipe}")
    print(f"projects exist={projects_dir().exists()}")

    bus = MessageBus()
    _section("Message bus")
    shutdowns = bus.discard_stale_shutdowns()
    if shutdowns:
        print(f"discarded stale SHUTDOWN signals: {shutdowns}")
    print(f"has_active_work={bus.has_active_work()}")
    stuck = bus.get_processing_messages()
    print(f"processing={[(m.id, m.to_agent, m.type) for m in stuck]}")
    for role in AGENT_ROLES:
        depth = bus.queue_depth(role)
        if depth:
            print(f"  {role}: pending={depth}")

    _section("Projects")
    proot = projects_dir()
    if not proot.exists():
        print("No projects/ directory")
        return 1

    slugs = [args.slug] if args.slug else sorted(p.name for p in proot.iterdir() if p.is_dir())
    for slug in slugs:
        state_file = proot / slug / "state" / "current_idea.json"
        if not state_file.exists():
            print(f"  {slug}: (no state)")
            continue
        state = json.loads(state_file.read_text(encoding="utf-8"))
        status = state.get("status", "?")
        phase = state.get("phase", "?")
        if not args.all and status in ("complete", "budget_exceeded", ""):
            continue
        print(f"  {slug}: status={status} phase={phase} title={state.get('title', slug)!r}")

        phase_num = state.get("phase", 1)
        val_path = proot / slug / f"phases/phase_{phase_num}/validation_report.md"
        rev_path = proot / slug / f"phases/phase_{phase_num}/review.md"
        if val_path.exists():
            val = val_path.read_text(encoding="utf-8", errors="replace")
            print(f"    validation PASS={validation_passed(val)}")
        if rev_path.exists():
            rev = rev_path.read_text(encoding="utf-8", errors="replace")
            print(f"    review complete={review_artifacts_complete(rev)}")
        if status.endswith("_reviewing") and val_path.exists() and rev_path.exists():
            val = val_path.read_text(encoding="utf-8", errors="replace")
            rev = rev_path.read_text(encoding="utf-8", errors="replace")
            if validation_passed(val) and review_artifacts_complete(rev):
                print("    ⚠ skip-review eligible — pull 903dca0+ and restart runner")

    _section("Throughput")
    tp = pipe / "state" / "throughput.json"
    if tp.exists():
        data = json.loads(tp.read_text(encoding="utf-8"))
        print(f"  call_count={data.get('call_count', 0)} tps={data.get('tps', 0)}")
        print(f"  updated_at={data.get('updated_at', '?')}")
    else:
        print("  (no throughput.json — no completed LLM calls this session)")

    _section("master_ideas.md (first unchecked)")
    mi = ROOT / "master_ideas.md"
    if mi.exists():
        for line in mi.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("[ ]"):
                print(f"  {line.strip()[:100]}")
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
