#!/usr/bin/env python3
"""Morning report after overnight Grok from-list (P0).

Usage:
  set PIPELINE_DIR=C:\\Users\\avata\\aicompete\\thepipeline
  python scripts/overnight_report.py --since 2026-07-22T02:00:00
  python scripts/overnight_report.py --log-dir logs/overnight_20260722_0200
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


def _parse_since(s: str | None) -> float | None:
    if not s:
        return None
    s = s.strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).timestamp()
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Overnight Grok field/build morning report")
    ap.add_argument("--since", default="", help="ISO time; only projects with newer state mtime")
    ap.add_argument("--log-dir", default="", help="Write MORNING.md here")
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    args = ap.parse_args()

    if args.pipeline_dir:
        os.environ["PIPELINE_DIR"] = args.pipeline_dir

    from pipeline.paths import projects_dir

    root = projects_dir()
    since_ts = _parse_since(args.since) if args.since else None

    counts: dict[str, int] = {}
    rows: list[dict] = []
    for proj in sorted(root.iterdir()) if root.is_dir() else []:
        if not proj.is_dir():
            continue
        sf = proj / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            mtime = sf.stat().st_mtime
        except OSError:
            continue
        if since_ts is not None and mtime < since_ts:
            continue
        try:
            state = json.loads(sf.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        status = (state.get("status") or "").strip() or "EMPTY"
        eng = (state.get("engine") or "").strip() or "classic?"
        counts[status] = counts.get(status, 0) + 1
        rows.append(
            {
                "slug": proj.name,
                "status": status,
                "engine": eng,
                "mtime": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
            }
        )

    proven = counts.get("field_proven", 0)
    insuff = counts.get("ship_insufficient", 0)
    deeper = counts.get("deeper_work_needed", 0)
    complete = counts.get("complete", 0) + counts.get("complete_with_bugs", 0)
    inflight = sum(
        c
        for st, c in counts.items()
        if "phase_" in st or st in ("field_testing", "field_planning", "field_test_planning")
    )
    grok_rows = [r for r in rows if "grok" in (r.get("engine") or "").lower()]

    lines = [
        f"# Overnight morning report",
        f"",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Projects dir: `{root}`",
        f"- Since filter: `{args.since or 'all projects with state'}`",
        f"- Matched projects: **{len(rows)}** (grok_build engine: {len(grok_rows)})",
        f"",
        f"## Headline",
        f"",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| field_proven | {proven} |",
        f"| ship_insufficient | {insuff} |",
        f"| deeper_work_needed | {deeper} |",
        f"| complete / complete_with_bugs | {complete} |",
        f"| in-flight (phase_*/field_*) | {inflight} |",
        f"",
        f"## Status histogram",
        f"",
    ]
    for st, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{st}`: {c}")

    lines.extend(["", "## Projects (matched)", ""])
    for r in rows[:80]:
        lines.append(
            f"- `{r['slug']}` - {r['status']} (engine={r['engine']}) {r['mtime']}"
        )
    if len(rows) > 80:
        lines.append(f"- … +{len(rows) - 80} more")

    lines.extend(
        [
            "",
            "## Ops checklist",
            "",
            "1. Host stayed awake? No zombie `grok.exe`?",
            "2. `GROK_BUILD_CMD` was set in the launcher process?",
            "3. Run `python extract.py` if on Vast / before reboot",
            "4. Inspect `ship_insufficient` evaluations under `phases/ship/`",
            "",
        ]
    )

    text = "\n".join(lines) + "\n"
    print(text)

    if args.log_dir:
        out = Path(args.log_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "MORNING.md").write_text(text, encoding="utf-8")
        (out / "morning_rows.json").write_text(
            json.dumps(rows, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Wrote {out / 'MORNING.md'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
