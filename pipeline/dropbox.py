"""
pipeline/dropbox.py
User steering inbox (dropbox.md) — polled by runner, triaged by manager.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.message_bus import Message, MessageBus
from pipeline.pipeline_config import PROJECT_ROOT
from pipeline.paths import get_pipeline_dir, project_dir, state_dir

DROPBOX_PATH = PROJECT_ROOT / "dropbox.md"


def _dropbox_state_path():
    return state_dir() / "dropbox_state.json"
USER_MSG_RE = re.compile(
    r"^###\s+USER\s+(?P<id>msg-[\w-]+)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
TARGET_RE = re.compile(r"^target:\s*(\S+)\s*$", re.MULTILINE | re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def ensure_dropbox() -> Path:
    """Create dropbox.md template if missing."""
    if not DROPBOX_PATH.exists():
        DROPBOX_PATH.write_text(
            """# Pipeline Dropbox

Steer the running pipeline, revise active projects, or add details while the runner is up.
The runner checks this file every **10 minutes**. The manager triages new entries and may reply below.

## How to post

Add a block like this at the **bottom** of the file:

```
### USER msg-20260520-001
target: project_slug_optional
Your message: steer, revise, add requirements, pause, reprioritize, etc.
```

- `target:` optional — project slug under `.pipeline/projects/<slug>/`
- Use unique ids: `msg-YYYYMMDD-NNN`

Manager replies appear as `### MANAGER msg-...-r1` blocks.
If the manager needs clarification, it will ask in a MANAGER block — reply with a new USER block referencing the same target.

---

""",
            encoding="utf-8",
        )
    _dropbox_state_path().parent.mkdir(parents=True, exist_ok=True)
    return DROPBOX_PATH


def _load_state() -> dict[str, Any]:
    ensure_dropbox()
    if not _dropbox_state_path().exists():
        return {"processed_user_ids": [], "queued_user_ids": [], "last_check": ""}
    try:
        return json.loads(_dropbox_state_path().read_text(encoding="utf-8"))
    except Exception:
        return {"processed_user_ids": [], "queued_user_ids": [], "last_check": ""}


def _save_state(state: dict[str, Any]) -> None:
    _dropbox_state_path().parent.mkdir(parents=True, exist_ok=True)
    _dropbox_state_path().write_text(json.dumps(state, indent=2), encoding="utf-8")


def parse_user_messages(text: str) -> list[dict[str, str]]:
    """Extract USER message blocks from dropbox.md."""
    messages: list[dict[str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^###\s+USER\s+(msg-[\w-]+)\s*$", lines[i], re.IGNORECASE)
        if not m:
            i += 1
            continue
        msg_id = m.group(1)
        i += 1
        target = ""
        body_lines: list[str] = []
        while i < len(lines) and not lines[i].startswith("### "):
            tm = TARGET_RE.match(lines[i])
            if tm and not body_lines:
                target = tm.group(1).strip()
                i += 1
                continue
            body_lines.append(lines[i])
            i += 1
        body = "\n".join(body_lines).strip()
        if body:
            messages.append({"id": msg_id, "target": target, "body": body})
    return messages


def append_manager_reply(
    user_msg_id: str,
    body: str,
    *,
    status: str = "ok",
) -> str:
    """Append a MANAGER response block to dropbox.md. Returns reply id."""
    ensure_dropbox()
    reply_id = f"{user_msg_id}-r{datetime.now(timezone.utc).strftime('%H%M%S')}"
    block = (
        f"\n### MANAGER {reply_id}\n"
        f"status: {status}\n"
        f"ts: {_now()}\n\n"
        f"{body.strip()}\n"
    )
    with DROPBOX_PATH.open("a", encoding="utf-8") as f:
        f.write(block)
    return reply_id


def mark_user_processed(msg_id: str, *, queued: bool = False) -> None:
    state = _load_state()
    ids = state.setdefault("processed_user_ids", [])
    if msg_id not in ids:
        ids.append(msg_id)
    if queued:
        q = state.setdefault("queued_user_ids", [])
        if msg_id not in q:
            q.append(msg_id)
    state["last_check"] = _now()
    _save_state(state)


def get_pending_user_messages() -> list[dict[str, str]]:
    ensure_dropbox()
    text = DROPBOX_PATH.read_text(encoding="utf-8")
    state = _load_state()
    processed = set(state.get("processed_user_ids") or [])
    return [m for m in parse_user_messages(text) if m["id"] not in processed]


def check_dropbox(bus: MessageBus, ideas_path: Path | None = None) -> int:
    """
    Poll dropbox.md; queue new USER messages to the manager agent.
    Returns count of messages queued this tick.
    """
    pending = get_pending_user_messages()
    if not pending:
        _load_state()  # touch last_check via mark on empty? skip
        state = _load_state()
        state["last_check"] = _now()
        _save_state(state)
        return 0

    from pipeline.pipeline_status import _get_active_idea_state as get_active_idea_state

    active = get_active_idea_state(get_pipeline_dir())
    active_slug = active.get("_slug", "")

    queued = 0
    for msg in pending:
        mark_user_processed(msg["id"], queued=True)
        bus.send(
            Message.create(
                from_agent="runner",
                to_agent="manager",
                type="dropbox_user",
                payload={
                    "msg_id": msg["id"],
                    "body": msg["body"],
                    "target_slug": msg.get("target") or active_slug,
                    "active_slug": active_slug,
                    "ideas_path": str(ideas_path or PROJECT_ROOT / "master_ideas.md"),
                    "source": "dropbox",
                },
                priority=0,
            )
        )
        queued += 1
    return queued


def apply_project_steer(slug: str, notes: str, *, source_msg_id: str = "") -> Path:
    """Append user steering notes to a project's state directory."""
    proj = project_dir(slug)
    proj.mkdir(parents=True, exist_ok=True)
    path = proj / "state" / "user_steer.md"
    header = f"\n\n## {_now()} (dropbox {source_msg_id})\n"
    if path.exists():
        path.write_text(path.read_text(encoding="utf-8") + header + notes.strip() + "\n", encoding="utf-8")
    else:
        path.write_text(f"# User steering notes\n{header}{notes.strip()}\n", encoding="utf-8")
    return path
