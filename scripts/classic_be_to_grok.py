#!/usr/bin/env python3
"""
Classic budget_exceeded → grok_build conversion canary (thin CLI).

Core logic lives in pipeline.classic_to_grok. This script does NOT run the
factory — it rewrites project state so a serial Grok run can try to finish /
field_prove. Use one slug at a time — do not mass-convert.

Usage:
  set PIPELINE_DIR=C:\\Users\\avata\\aicompete\\thepipeline

  # Inventory BE projects with ladder labels
  python scripts/classic_be_to_grok.py --list

  # Dry-run conversion plan
  python scripts/classic_be_to_grok.py --slug supportagent_workflow_builder --dry-run

  # Apply (park: sticky engine, no ladder focus grab)
  python scripts/classic_be_to_grok.py --slug supportagent_workflow_builder

  # Apply and try run_now (ladder focus if free)
  python scripts/classic_be_to_grok.py --slug supportagent_workflow_builder --run-now

  # Drain converted work overnight (resume in-flight, not fresh-list-only):
  #   .\\scripts\\overnight_grok_from_list.ps1 -NoFreshListOnly

Safety:
  - Refuses test_* / junk unless --force
  - Refuses lifetime-1000 fossils unless --force-lifetime
  - Never commits/pushes
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def cmd_list(root: Path) -> int:
    from pipeline.classic_to_grok import (
        is_junk_slug,
        ladder_stage,
        load_be_projects,
        note_class,
    )

    rows = load_be_projects(root)
    print(f"budget_exceeded projects under {root}: {len(rows)}\n")
    print(
        f"{'slug':<42} {'stage':<5} {'str':>3} {'be1':>4} {'note':<14} "
        f"{'phase':>7} eng  pre"
    )
    print("-" * 100)
    for slug, _sf, st in rows:
        eng = (st.get("engine") or "?")[:10]
        phase = f"{st.get('phase', '?')}/{st.get('total_phases', '?')}"
        strikes = 0
        try:
            strikes = max(0, int(st.get("budget_strikes") or 0))
        except (TypeError, ValueError):
            pass
        junk = " junk" if is_junk_slug(slug) else ""
        print(
            f"{slug:<42} {ladder_stage(st):<5} {strikes:>3} "
            f"{str(bool(st.get('be1_consumed'))):>4} {note_class(st):<14} "
            f"{phase:>7} {eng:<6} {st.get('pre_budget_status') or '-'}{junk}"
        )
    print(
        "\nCanary picks (near-done, non-junk, not lifetime):\n"
        "  prefer pN/N or pre=*reviewing|*validating, note=active_yield\n"
        "  python scripts/classic_be_to_grok.py --slug <slug> --dry-run\n"
        "  Drain path: overnight_grok_from_list.ps1 -NoFreshListOnly"
    )
    return 0


def cmd_convert(
    root: Path,
    slug: str,
    *,
    dry_run: bool,
    force: bool,
    force_lifetime: bool,
    keep_strikes: bool,
    run_now: bool,
) -> int:
    from pipeline.classic_to_grok import apply_classic_to_grok, note_class

    mode = "run_now" if run_now else "park"
    result = apply_classic_to_grok(
        slug,
        dry_run=dry_run,
        force=force,
        force_lifetime=force_lifetime,
        keep_strikes=keep_strikes,
        mode=mode,
        near_done_only=False,  # manual CLI: near-done filter is auto-path only
        projects_root=root,
    )

    new_st = result.get("state") or {}
    from_engine = result.get("from_engine")
    from_status = result.get("from_status")
    print(f"slug:     {slug}")
    print(f"result:   ok={result.get('ok')} reason={result.get('reason')}")
    if result.get("idempotent"):
        print(
            f"idempotent: {result.get('reason')} "
            f"(engine={new_st.get('engine')!r} status={new_st.get('status')!r})"
        )
        return 0
    if not result.get("ok"):
        if result.get("reason") == "junk_slug":
            print(f"REFUSE junk slug {slug!r} (use --force if intentional)")
            return 3
        if result.get("reason") == "lifetime_fossil":
            print(
                f"REFUSE lifetime-retry fossil {slug!r} "
                f"(use --force-lifetime if intentional)"
            )
            return 3
        if str(result.get("reason", "")).startswith("status_not_be"):
            print(
                f"ERROR: {slug} status={from_status!r} (want budget_exceeded)"
            )
            return 2
        if str(result.get("reason", "")).startswith("missing_state"):
            print(f"ERROR: missing state for {slug}")
            return 2
        print(f"ERROR: {result.get('reason')}")
        return 2

    from_snap = (new_st.get("classic_to_grok_from") or {}) if new_st else {}
    nc = from_snap.get("note_class") or note_class(new_st)
    print(
        f"from:     status={from_status!r} engine={from_engine!r} note={nc}"
    )
    print(
        f"to:       status={result.get('to_status') or new_st.get('status')} "
        f"engine=grok_build mode={result.get('mode')} "
        f"parked={bool(new_st.get('classic_to_grok_parked'))}"
    )
    print(f"phase:    {new_st.get('phase')}/{new_st.get('total_phases')}")
    print(
        f"prefer_thin_field: {result.get('prefer_thin_field')} "
        f"(deferred={bool(new_st.get('classic_to_grok_prefer_thin'))})"
    )
    if result.get("focus_blocked"):
        print("note:     run_now requested but serial focus busy → parked")
    if dry_run:
        print("\nDRY-RUN — no write. Re-run without --dry-run to apply.")
        print("Park stays budget_exceeded. Unpark with --run-now or drain:")
        print("  .\\scripts\\overnight_grok_from_list.ps1 -NoFreshListOnly")
        return 0

    if result.get("wrote"):
        print(f"\nWROTE {result.get('project_dir')}/state/current_idea.json")
        if result.get("bak"):
            print(f"BACKUP {result['bak']}")
    if new_st.get("classic_to_grok_parked"):
        print(
            "Parked: sticky engine=grok_build, status=budget_exceeded "
            "(not runnable). Unpark: --run-now or overnight -NoFreshListOnly."
        )
    else:
        print(
            "Next: serial overnight/runner with PIPELINE_ENGINE=grok_build "
            "(project resumed / unparked)."
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Classic BE → grok_build conversion canary"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    ap.add_argument(
        "--list", action="store_true", help="List all budget_exceeded projects"
    )
    ap.add_argument("--slug", default="", help="Project slug to convert")
    ap.add_argument("--dry-run", action="store_true", help="Show plan only")
    ap.add_argument("--force", action="store_true", help="Allow junk test_* slugs")
    ap.add_argument(
        "--force-lifetime",
        action="store_true",
        help="Allow lifetime-1000 retry fossils",
    )
    ap.add_argument(
        "--keep-strikes",
        action="store_true",
        help="Keep budget_strikes / do not fully reset ladder flags",
    )
    ap.add_argument(
        "--run-now",
        action="store_true",
        help="run_now mode: set ladder focus if free (default park)",
    )
    args = ap.parse_args()

    if args.pipeline_dir:
        os.environ["PIPELINE_DIR"] = args.pipeline_dir

    from pipeline.paths import projects_dir

    root = projects_dir()
    if args.list or not args.slug:
        if not args.slug:
            return cmd_list(root)
    if args.list and args.slug:
        cmd_list(root)
        print()
    if not args.slug:
        return 0
    return cmd_convert(
        root,
        args.slug.strip(),
        dry_run=args.dry_run,
        force=args.force,
        force_lifetime=args.force_lifetime,
        keep_strikes=args.keep_strikes,
        run_now=args.run_now,
    )


if __name__ == "__main__":
    raise SystemExit(main())
