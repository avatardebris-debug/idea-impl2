"""
pipeline/capability_gaps.py
Meta channel: manager/ideator queues capability gaps; runner seeds them as normal projects.
"""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.message_bus import MessageBus
from pipeline.paths import projects_dir, state_dir
from pipeline.seeding import SEED_BLOCKED, SEED_EMPTY, SEED_SEEDED, _seeded_this_session, seed_idea
from pipeline.slug_util import slugify_title as _slugify


def _gaps_path() -> Path:
    return state_dir() / "capability_gaps.md"
_LINE_RE = re.compile(r"- \[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)")


def append_capability_gap(title: str, description: str) -> None:
    _gaps_path().parent.mkdir(parents=True, exist_ok=True)
    if not _gaps_path().exists():
        _gaps_path().write_text(
            "# Capability gaps\n\n"
            "Queued by manager/ideator when no verified tool exists.\n"
            "Processed before master_ideas.md during --from-list seeding.\n\n",
            encoding="utf-8",
        )
    line = f"- [ ] **{title.strip()}** — {description.strip()}\n"
    with _gaps_path().open("a", encoding="utf-8") as f:
        f.write(line)


def _mark_gap_done(title: str) -> None:
    if not _gaps_path().exists():
        return
    content = _gaps_path().read_text(encoding="utf-8")
    content = content.replace(f"- [ ] **[{title}]**", f"- [x] **[{title}]**", 1)
    _gaps_path().write_text(content, encoding="utf-8")


def seed_next_capability_gap(bus: MessageBus) -> str:
    """
    Seed the first unchecked gap entry. Returns SEED_* constant.
    """
    if not _gaps_path().exists():
        return SEED_EMPTY

    for line in _gaps_path().read_text(encoding="utf-8").splitlines():
        m = _LINE_RE.match(line)
        if not m:
            continue
        title = m.group(1).strip()
        if title in _seeded_this_session:
            continue
        desc = m.group(2).strip()
        if desc.startswith("[") and desc.endswith("]"):
            desc = desc[1:-1].strip()

        print(f"  [capability_gap] Seeding gap: {title}")
        _seeded_this_session.add(title)
        slug = _slugify(title)
        project_state = projects_dir() / slug / "state" / "current_idea.json"
        if project_state.exists():
            return SEED_BLOCKED

        seed_idea(bus, title, f"[capability_gap] {desc}")
        _mark_gap_done(title)
        return SEED_SEEDED

    return SEED_EMPTY
