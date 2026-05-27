"""Track decomposed-but-unachieved goals in PIPELINE_DIR/goals/backlog.md."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

from pipeline.pipeline_config import PIPELINE_DIR

GOALS_DIR = PIPELINE_DIR / "goals"
BACKLOG_PATH = GOALS_DIR / "backlog.md"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_decomposed_goal(
    goal_id: str,
    goal_text: str,
    *,
    branch_count: int,
    tree_path: pathlib.Path | None = None,
) -> None:
    GOALS_DIR.mkdir(parents=True, exist_ok=True)
    header = "## Active goals (decomposed, not achieved)\n"
    line = (
        f"- [ ] **{goal_text[:80]}** — goal:{goal_id} "
        f"decomposed branches:{branch_count} at {_now()}\n"
    )
    if BACKLOG_PATH.exists():
        content = BACKLOG_PATH.read_text(encoding="utf-8")
    else:
        content = (
            "# Goal backlog\n\n"
            "Parent goals stay unchecked until `--attempt-goal` marks them achieved.\n\n"
        )
    if header.strip() not in content:
        content += f"\n{header}\n"
    if f"goal:{goal_id}" not in content:
        content += line
        BACKLOG_PATH.write_text(content, encoding="utf-8")


def mark_goal_achieved(goal_id: str) -> None:
    if not BACKLOG_PATH.exists():
        return
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    content = content.replace(f"goal:{goal_id}", f"goal:{goal_id} achieved")
    import re

    content = re.sub(
        rf"(- \[ \].*?goal:{re.escape(goal_id)}.*?)\n",
        lambda m: m.group(0).replace("- [ ]", "- [x]", 1),
        content,
        count=1,
    )
    BACKLOG_PATH.write_text(content, encoding="utf-8")


def load_goal_tree(goal_id: str) -> dict | None:
    path = GOALS_DIR / f"{goal_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
