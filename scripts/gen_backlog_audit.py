#!/usr/bin/env python3
"""Regenerate BACKLOG_AUDIT.md. Run from repo root: python scripts/gen_backlog_audit.py"""
from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECTS = ROOT / ".pipeline" / "projects"


def slugify(title: str) -> str:
    t = title.strip("[] ").lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")[:60]


def parse_unchecked(path: pathlib.Path) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r"[*-]?\s*\[ \]\s+\*\*(.+?)\*\*\s*[—–-]", line)
        if not m:
            m = re.match(r"[*-]?\s*\[ \]\s+\[([^\]]+)\]", line)
        if m:
            items.append((m.group(1).strip(), slugify(m.group(1))))
    return items


def main() -> None:
    complete: set[str] = set()
    partial: dict[str, str] = {}
    for d in PROJECTS.iterdir():
        if not d.is_dir():
            continue
        sf = d / "state" / "current_idea.json"
        if not sf.exists():
            continue
        st = json.loads(sf.read_text(encoding="utf-8"))
        slug = d.name
        phase = int(st.get("phase", 0))
        total = int(st.get("total_phases", 1))
        if st.get("status") == "complete" and phase >= total:
            complete.add(slug)
        else:
            partial[slug] = f"{st.get('status')} (phase {phase}/{total})"

    files = [
        ROOT / "master_ideas.md",
        ROOT / "master_ideas_consolidated.md",
        ROOT / "unstarted_projects_backlog.md",
    ]
    files.extend(sorted(ROOT.glob("master ideas backup sort/**/*.md")))
    files = [f for f in files if f.is_file()]

    by_slug: dict[str, dict] = {}
    for f in files:
        rel = str(f.relative_to(ROOT))
        for title, slug in parse_unchecked(f):
            e = by_slug.setdefault(slug, {"title": title, "sources": set(), "disk": "none"})
            e["sources"].add(rel)
            if slug in complete:
                e["disk"] = "complete"
            elif slug in partial:
                e["disk"] = partial[slug]

    not_started = [e for s, e in sorted(by_slug.items()) if e["disk"] == "none"]
    in_progress = [e for s, e in sorted(by_slug.items()) if e["disk"] not in ("none", "complete")]
    stale = [e for s, e in sorted(by_slug.items()) if e["disk"] == "complete"]
    mi_rows = [
        {"title": t, "slug": s, "disk": by_slug.get(s, {}).get("disk", "none")}
        for t, s in parse_unchecked(ROOT / "master_ideas.md")
    ]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L: list[str] = [
        "# Backlog audit",
        "",
        f"Generated: **{now}**",
        "",
        "Regenerate: `python scripts/gen_backlog_audit.py`",
        "",
        "Compares unchecked backlog lines against `.pipeline/projects/*/state/current_idea.json`.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Markdown files scanned | {len(files)} |",
        f"| Projects complete on disk | {len(complete)} |",
        f"| Unique unchecked titles | {len(by_slug)} |",
        f"| **Not started** | {len(not_started)} |",
        f"| **In progress** | {len(in_progress)} |",
        f"| **Stale** (complete on disk, still `[ ]`) | {len(stale)} |",
        "",
        "**Runner queue:** `master_ideas.md` only.",
        "",
        "```bash",
        "python extract.py --rebuild-truth",
        "python extract.py --sync-ideas",
        "```",
        "",
        "---",
        "",
        "## Active queue: `master_ideas.md`",
        "",
        "| # | Title | Slug | Disk status |",
        "|--:|-------|------|-------------|",
    ]
    for i, r in enumerate(mi_rows, 1):
        L.append(f"| {i} | {r['title']} | `{r['slug']}` | {r['disk']} |")

    L += ["", "---", "", f"## In progress ({len(in_progress)})", ""]
    for e in sorted(in_progress, key=lambda x: x["title"].lower()):
        src = sorted(e["sources"])[0]
        extra = f" (+{len(e['sources']) - 1})" if len(e["sources"]) > 1 else ""
        L.append(f"- **{e['title']}** — `{e['disk']}` — `{src}`{extra}")

    L += ["", "---", "", f"## Not started ({len(not_started)})", ""]
    for e in sorted(not_started, key=lambda x: x["title"].lower()):
        L.append(f"- **{e['title']}** — `{slugify(e['title'])}`")

    L += ["", "---", "", f"## Stale checkboxes ({len(stale)})", ""]
    for e in sorted(stale, key=lambda x: x["title"].lower()):
        L.append(f"- **{e['title']}** — `{slugify(e['title'])}`")

    blocked: list[dict] = []
    try:
        from pipeline.capability_graph import blocked_unchecked_ideas

        blocked = blocked_unchecked_ideas(ROOT / "master_ideas.md")
    except Exception:
        pass

    L += ["", "---", "", f"## Blocked downstream ({len(blocked)})", ""]
    L.append("")
    L.append("Unchecked in `master_ideas.md` but `requires:` prerequisites are not verified on disk.")
    L.append("")
    for b in sorted(blocked, key=lambda x: x["slug"]):
        miss = ", ".join(f"`{m}`" for m in b["missing"])
        req = ", ".join(f"`{r}`" for r in b["requires"])
        L.append(f"- **{b['slug']}** — needs {req}; missing verified: {miss}")

    (ROOT / "BACKLOG_AUDIT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote BACKLOG_AUDIT.md ({len(not_started)} not started, {len(stale)} stale)")


if __name__ == "__main__":
    main()
