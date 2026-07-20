#!/usr/bin/env python3
"""
Bulk thin field ship for projects already at complete (or other statuses).

Does **not** re-run full grok_build review/thermo. Plan + run field tests only.
On FAIL → ship_insufficient (record evidence); does not auto-retry implement.

Usage (from factory repo):
  set PIPELINE_DIR=C:\\Users\\avata\\aicompete\\thepipeline
  set FIELD_SHIP_ALLOW_CLASSIC=1
  set FIELD_PLAN_ENGINE=heuristic
  python scripts/bulk_thin_field_ship.py --limit 5
  python scripts/bulk_thin_field_ship.py --status complete,ship_insufficient --limit 20
  python scripts/bulk_thin_field_ship.py --slug business_plan --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Factory root on path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk thin field ship")
    parser.add_argument("--limit", type=int, default=0, help="Max projects (0=all)")
    parser.add_argument(
        "--status",
        default=os.environ.get("FIELD_SHIP_STATUSES", "complete"),
        help="Comma statuses to include (default: complete)",
    )
    parser.add_argument("--slug", default="", help="Substring filter on slug")
    parser.add_argument(
        "--plan-engine",
        default=os.environ.get("FIELD_PLAN_ENGINE", "auto"),
        help="auto|grok|pipeline_llm|heuristic|none",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List candidates only",
    )
    parser.add_argument(
        "--include-classic",
        action="store_true",
        help="Allow classic engine (sets FIELD_SHIP_ALLOW_CLASSIC)",
    )
    parser.add_argument(
        "--retry-insufficient",
        action="store_true",
        help="Also include ship_insufficient (re-field)",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Enable field repair bridge on FAIL (FIELD_SHIP_REPAIR=1)",
    )
    parser.add_argument(
        "--no-repair",
        action="store_true",
        help="Disable repair bridge (fast bulk smoke only)",
    )
    parser.add_argument(
        "--prefer-existing-plan",
        action="store_true",
        help="Use FIELD_PLAN_ENGINE=none when field_tests.md already exists",
    )
    args = parser.parse_args()

    os.environ.setdefault("FIELD_SHIP_BULK", "1")
    if args.include_classic:
        os.environ["FIELD_SHIP_ALLOW_CLASSIC"] = "1"
    os.environ["FIELD_PLAN_ENGINE"] = args.plan_engine
    # Bulk defaults to NO repair (cheap plan+run). Opt in with --repair.
    if args.repair:
        os.environ["FIELD_SHIP_REPAIR"] = "1"
    elif args.no_repair or "FIELD_SHIP_REPAIR" not in os.environ:
        os.environ["FIELD_SHIP_REPAIR"] = "0"
    if args.prefer_existing_plan:
        # Per-project override applied in loop when plan file exists
        pass
    statuses = [s.strip() for s in args.status.split(",") if s.strip()]
    if args.retry_insufficient and "ship_insufficient" not in statuses:
        statuses.append("ship_insufficient")
    os.environ["FIELD_SHIP_STATUSES"] = ",".join(statuses)

    from pipeline.engines.field_ship import run_thin_field_ship, thin_ship_enabled
    from pipeline.paths import projects_dir

    root = projects_dir()
    if not root.is_dir():
        print(f"projects dir missing: {root}")
        return 1

    candidates: list[Path] = []
    for project_dir in sorted(root.iterdir()):
        if not project_dir.is_dir():
            continue
        slug = project_dir.name
        if args.slug and args.slug not in slug:
            continue
        sf = project_dir / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            state = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = (state.get("status") or "").strip()
        if status not in statuses:
            continue
        if not thin_ship_enabled(state, force=True):
            continue
        # Skip already field_proven unless re-running insufficient only
        if status == "field_proven":
            continue
        candidates.append(project_dir)

    print(f"Candidates: {len(candidates)} (statuses={statuses}, plan={args.plan_engine})")
    if args.dry_run:
        for p in candidates[: args.limit or len(candidates)]:
            st = json.loads((p / "state/current_idea.json").read_text(encoding="utf-8"))
            print(f"  {p.name}  status={st.get('status')} engine={st.get('engine', 'classic')}")
        return 0

    done = 0
    proven = 0
    insuff = 0
    for project_dir in candidates:
        if args.limit and done >= args.limit:
            break
        sf = project_dir / "state" / "current_idea.json"
        state = json.loads(sf.read_text(encoding="utf-8"))
        slug = project_dir.name
        print(f"--- {slug} ---")
        plan_eng = args.plan_engine
        if args.prefer_existing_plan:
            existing = project_dir / "phases" / "ship" / "field_tests.md"
            if existing.is_file() and existing.stat().st_size > 40:
                plan_eng = "none"
        r = run_thin_field_ship(
            project_dir,
            state,
            slug=slug,
            plan_engine=plan_eng,
            skip_if_terminal=False,
        )
        done += 1
        if r.status == "field_proven":
            proven += 1
        elif r.status == "ship_insufficient":
            insuff += 1
        print(f"  → {r.status} plan={r.plan_engine} pass={r.passed} fail={r.failed}")

    print(f"Done: {done}  field_proven={proven}  ship_insufficient={insuff}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
