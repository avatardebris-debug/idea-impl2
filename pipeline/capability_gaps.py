"""
pipeline/capability_gaps.py
Meta channel: manager/ideator queues capability gaps; runner seeds them as normal projects.
"""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.message_bus import MessageBus
from pipeline.pipeline_config import PIPELINE_DIR
from pipeline.seeding import SEED_BLOCKED, SEED_EMPTY, SEED_SEEDED, _seeded_this_session, seed_idea
from pipeline.slug_util import slugify_title as _slugify

GAPS_PATH = PIPELINE_DIR / "state" / "capability_gaps.md"
_LINE_RE = re.compile(r"- \[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)")


def append_capability_gap(title: str, description: str) -> None:
    GAPS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not GAPS_PATH.exists():
        GAPS_PATH.write_text(
            "# Capability gaps\n\n"
            "Queued by manager/ideator when no verified tool exists.\n"
            "Processed before master_ideas.md during --from-list seeding.\n\n",
            encoding="utf-8",
        )
    line = f"- [ ] **{title.strip()}** — {description.strip()}\n"
    with GAPS_PATH.open("a", encoding="utf-8") as f:
        f.write(line)


def _mark_gap_done(title: str) -> None:
    if not GAPS_PATH.exists():
        return
    content = GAPS_PATH.read_text(encoding="utf-8")
    content = content.replace(f"- [ ] **[{title}]**", f"- [x] **[{title}]**", 1)
    GAPS_PATH.write_text(content, encoding="utf-8")


def seed_next_capability_gap(bus: MessageBus) -> str:
    """
    Seed the first unchecked gap entry. Returns SEED_* constant.
    """
    if not GAPS_PATH.exists():
        return SEED_EMPTY

    for line in GAPS_PATH.read_text(encoding="utf-8").splitlines():
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
        project_state = PIPELINE_DIR / "projects" / slug / "state" / "current_idea.json"
        if project_state.exists():
            return SEED_BLOCKED

        seed_idea(bus, title, f"[capability_gap] {desc}")
        _mark_gap_done(title)
        return SEED_SEEDED

    return SEED_EMPTY
