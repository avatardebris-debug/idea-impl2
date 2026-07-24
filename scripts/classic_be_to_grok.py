#!/usr/bin/env python3
"""
Classic budget_exceeded → grok_build conversion canary.

Does NOT run the factory. It rewrites project state so a serial Grok run can try
to finish / field_prove. Use one slug at a time — do not mass-convert.

Usage:
  set PIPELINE_DIR=C:\\Users\\avata\\aicompete\\thepipeline

  # Inventory BE projects with ladder labels
  python scripts/classic_be_to_grok.py --list

  # Dry-run conversion plan
  python scripts/classic_be_to_grok.py --slug supportagent_workflow_builder --dry-run

  # Apply: engine=grok_build, resume pre_budget status, fresh clocks
  python scripts/classic_be_to_grok.py --slug supportagent_workflow_builder

  # Then run factory focused on that project (example):
  #   set PIPELINE_ENGINE=grok_build
  #   python -m pipeline.runner --from-list --fresh-list-only ...
  # Or polish / ship for near-complete work.

Safety:
  - Refuses test_* / junk unless --force
  - Refuses lifetime-1000 fossils unless --force-lifetime
  - Never commits/pushes
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

JUNK_PREFIXES = ("test_", "smoke_", "fake_", "tmp_")
JUNK_SLUGS = frozenset({"test_idea", "test_exec", "proj", "plan_first"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _note_class(state: dict) -> str:
    note = str(state.get("budget_note") or "").lower()
    if "total retries across all phases" in note:
        return "lifetime"
    if "active-min" in note:
        return "active_yield"
    if "force-completed after" in note:
        return "wall_or_force_min"
    if note.strip():
        return "other"
    return "empty"


def _strikes(state: dict) -> int:
    try:
        return max(0, int(state.get("budget_strikes") or 0))
    except (TypeError, ValueError):
        return 0


def _ladder_stage(state: dict) -> str:
    if (state.get("status") or "") != "budget_exceeded":
        return "-"
    st = state.get("budget_strikes")
    if st is None or _strikes(state) < 1:
        return "BE0"
    s = _strikes(state)
    if s == 1:
        return "BE1"
    if s == 2:
        return "BE2"
    return "BE3"


def _is_junk(slug: str) -> bool:
    if slug in JUNK_SLUGS:
        return True
    return any(slug.startswith(p) for p in JUNK_PREFIXES)


def _load_be_projects(root: Path) -> list[tuple[str, Path, dict]]:
    out: list[tuple[str, Path, dict]] = []
    if not root.is_dir():
        return out
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        sf = d / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if (st.get("status") or "") != "budget_exceeded":
            continue
        out.append((d.name, sf, st))
    return out


def cmd_list(root: Path) -> int:
    rows = _load_be_projects(root)
    print(f"budget_exceeded projects under {root}: {len(rows)}\n")
    print(
        f"{'slug':<42} {'stage':<5} {'str':>3} {'be1':>4} {'note':<14} "
        f"{'phase':>7} eng  pre"
    )
    print("-" * 100)
    for slug, _sf, st in rows:
        eng = (st.get("engine") or "?")[:10]
        phase = f"{st.get('phase', '?')}/{st.get('total_phases', '?')}"
        print(
            f"{slug:<42} {_ladder_stage(st):<5} {_strikes(st):>3} "
            f"{str(bool(st.get('be1_consumed'))):>4} {_note_class(st):<14} "
            f"{phase:>7} {eng:<6} {st.get('pre_budget_status') or '-'}"
        )
    print(
        "\nCanary picks (near-done, non-junk, not lifetime):\n"
        "  prefer pN/N or pre=*reviewing|*validating, note=active_yield\n"
        "  python scripts/classic_be_to_grok.py --slug <slug> --dry-run"
    )
    return 0


def convert_state(
    st: dict,
    *,
    clear_ladder_flags: bool = True,
    keep_strikes: bool = False,
) -> dict:
    """Mutate copy of state for grok_build resume."""
    out = dict(st)
    pre = out.get("pre_budget_status") or ""
    phase = out.get("phase") or 1
    if not (isinstance(pre, str) and pre.startswith("phase_")):
        pre = f"phase_{phase}_executing"

    out["engine"] = "grok_build"
    out["status"] = pre
    out["session_started_at"] = _now()
    out["last_active_work_at"] = _now()
    out["budget_yielded"] = False
    out.pop("budget_note", None)
    out["last_decision"] = "CLASSIC_TO_GROK"
    out["classic_to_grok_at"] = _now()
    out["classic_to_grok_from"] = {
        "status": "budget_exceeded",
        "pre_budget_status": st.get("pre_budget_status"),
        "budget_strikes": st.get("budget_strikes"),
        "note_class": _note_class(st),
    }

    if not keep_strikes:
        # Fresh Grok attempt: don't inherit BE1-done lockout mid-ladder
        out["budget_strikes"] = 0
        out.pop("be1_consumed", None)
        out.pop("be2_consumed", None)
        out.pop("be3_consumed", None)
        out.pop("be2_path", None)
        out.pop("be2_pending", None)
        out.pop("prefer_thin_field", None)
        out.pop("prefer_thin_field_shipped", None)
        out.pop("lifetime_retry_capped", None)
        out.pop("ladder_focus", None)

    if clear_ladder_flags and keep_strikes:
        # keep strikes but allow another BE1 if they yield under Grok
        out.pop("be1_consumed", None)

    # Prefer thin field when already near complete phases
    try:
        ph = int(out.get("phase") or 0)
        tot = int(out.get("total_phases") or 1)
        if ph >= tot:
            out["prefer_thin_field"] = True
    except (TypeError, ValueError):
        pass

    return out


def cmd_convert(
    root: Path,
    slug: str,
    *,
    dry_run: bool,
    force: bool,
    force_lifetime: bool,
    keep_strikes: bool,
) -> int:
    sf = root / slug / "state" / "current_idea.json"
    if not sf.is_file():
        print(f"ERROR: missing {sf}")
        return 2
    try:
        st = json.loads(sf.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"ERROR: unreadable state: {e}")
        return 2

    status = (st.get("status") or "").strip()
    if status != "budget_exceeded":
        print(f"ERROR: {slug} status={status!r} (want budget_exceeded)")
        return 2

    if _is_junk(slug) and not force:
        print(f"REFUSE junk slug {slug!r} (use --force if intentional)")
        return 3

    nc = _note_class(st)
    if nc == "lifetime" and not force_lifetime:
        print(
            f"REFUSE lifetime-retry fossil {slug!r} note_class={nc} "
            f"(use --force-lifetime if intentional)"
        )
        return 3

    new_st = convert_state(st, keep_strikes=keep_strikes)
    print(f"slug:     {slug}")
    print(f"from:     status={status} engine={st.get('engine') or '?'} "
          f"stage={_ladder_stage(st)} note={nc}")
    print(f"to:       status={new_st['status']} engine={new_st['engine']}")
    print(f"phase:    {new_st.get('phase')}/{new_st.get('total_phases')}")
    print(f"prefer_thin_field: {new_st.get('prefer_thin_field')}")
    print(f"strikes reset: {not keep_strikes}")

    if dry_run:
        print("\nDRY-RUN — no write. Re-run without --dry-run to apply.")
        print("Then run serial Grok on this project, e.g.:")
        print("  set PIPELINE_ENGINE=grok_build")
        print("  python -m pipeline.runner --from-list --fresh-list-only ...")
        print("  # or focus mechanisms your runner supports for a single slug")
        return 0

    # backup
    bak = sf.with_suffix(sf.suffix + f".bak_classic_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    bak.write_text(sf.read_text(encoding="utf-8-sig"), encoding="utf-8")
    sf.write_text(json.dumps(new_st, indent=2) + "\n", encoding="utf-8")
    print(f"\nWROTE {sf}")
    print(f"BACKUP {bak}")
    print("Next: serial overnight/runner with PIPELINE_ENGINE=grok_build; "
          "prefer one project focus so this can complete + thin field.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Classic BE → grok_build conversion canary")
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    ap.add_argument("--list", action="store_true", help="List all budget_exceeded projects")
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
    args = ap.parse_args()

    if args.pipeline_dir:
        os.environ["PIPELINE_DIR"] = args.pipeline_dir

    from pipeline.paths import projects_dir

    root = projects_dir()
    if args.list or not args.slug:
        if not args.slug:
            return cmd_list(root)
        # list + slug ignored falls through
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
    )


if __name__ == "__main__":
    raise SystemExit(main())
