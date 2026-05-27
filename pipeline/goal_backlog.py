"""Track decomposed-but-unachieved goals in pipeline output goals/backlog.md."""

from __future__ import annotations

import pathlib
import re
from datetime import datetime, timezone

from pipeline.goal_tree import goals_dir


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _backlog_path() -> pathlib.Path:
    return goals_dir() / "backlog.md"


def append_decomposed_goal(
    goal_id: str,
    goal_text: str,
    *,
    branch_count: int,
    tree_path: pathlib.Path | None = None,
) -> None:
    goals_dir().mkdir(parents=True, exist_ok=True)
    header = "## Active goals (decomposed, not achieved)\n"
    line = (
        f"- [ ] **{goal_text[:80]}** — goal:{goal_id} "
        f"decomposed branches:{branch_count} at {_now()}\n"
    )
    backlog = _backlog_path()
    if backlog.exists():
        content = backlog.read_text(encoding="utf-8")
    else:
        content = (
            "# Goal backlog\n\n"
            "Parent goals stay unchecked until `--attempt-goal` marks them achieved.\n\n"
        )
    if header.strip() not in content:
        content += f"\n{header}\n"
    marker = f"goal:{goal_id}"
    if marker not in content:
        content += line
        backlog.write_text(content, encoding="utf-8")


def mark_goal_achieved(goal_id: str) -> None:
    backlog = _backlog_path()
    if not backlog.exists():
        return
    escaped = re.escape(goal_id)
    line_pat = re.compile(rf"^(- \[ \].*?goal:{escaped}(?:\s|$|\]))", re.MULTILINE)
    content = backlog.read_text(encoding="utf-8")
    content = line_pat.sub(
        lambda m: m.group(1).replace("- [ ]", "- [x]", 1),
        content,
        count=1,
    )
    backlog.write_text(content, encoding="utf-8")
