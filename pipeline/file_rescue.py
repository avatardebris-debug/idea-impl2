"""
Persist executor file-rescue actions and format prompt hints for the next run.

When the LLM writes files outside the project workspace, the executor moves them
into the real workspace. That must be visible to the model (and validators) or
it keeps writing to the wrong place.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RESCUE_STATE_REL = "state/file_rescue.json"
RESCUE_PROMPT_REL = "state/file_rescue_hint.md"


def rescue_state_path(project_dir: Path) -> Path:
    return project_dir / RESCUE_STATE_REL


def rescue_prompt_path(project_dir: Path) -> Path:
    return project_dir / RESCUE_PROMPT_REL


def save_rescue_record(
    project_dir: Path,
    *,
    moves: list[dict[str, str]],
    pruned: list[str] | None = None,
    workspace: str = "",
    phase: int | None = None,
    idea_slug: str = "",
) -> dict[str, Any]:
    """Write state/file_rescue.json + human-readable hint markdown."""
    project_dir = Path(project_dir)
    record: dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "idea_slug": idea_slug,
        "phase": phase,
        "workspace": workspace,
        "move_count": len(moves),
        "moves": moves[:200],
        "pruned": (pruned or [])[:50],
        "canonical_workspace": workspace,
    }
    state_dir = project_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    try:
        rescue_state_path(project_dir).write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
    except OSError:
        pass

    hint = format_rescue_prompt_block(record, for_persist=True)
    try:
        rescue_prompt_path(project_dir).write_text(hint, encoding="utf-8")
    except OSError:
        pass
    return record


def load_rescue_record(project_dir: Path) -> dict[str, Any] | None:
    path = rescue_state_path(project_dir)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def format_rescue_prompt_block(
    record: dict[str, Any] | None,
    *,
    for_persist: bool = False,
    max_moves: int = 25,
) -> str:
    """Markdown block injected into the executor (and optionally validator) prompt."""
    if not record:
        return ""
    moves = record.get("moves") or []
    pruned = record.get("pruned") or []
    if not moves and not pruned:
        return ""

    ws = record.get("workspace") or record.get("canonical_workspace") or ""
    lines = [
        "## System file rescue (authoritative — read before writing files)",
        "",
        "The pipeline **moved or cleaned files** that were written outside the real project workspace.",
        "The **canonical workspace** (use this EXACT path for ALL new files):",
        f"",
        f"  `{ws}`",
        "",
        "Rules:",
        "- Do **NOT** create a nested `workspace/` directory under the workspace.",
        "- Do **NOT** write under the factory repo root or `projects/<slug>/` outside `workspace/`.",
        "- Prefer paths that start with the canonical workspace path above.",
        "- Treat files listed under **Rescued to** as the live sources of truth.",
        "",
    ]
    if moves:
        lines.append(f"### Rescued ({len(moves)} file(s))")
        for m in moves[:max_moves]:
            src = m.get("src", "?")
            dest = m.get("dest", "?")
            lab = m.get("label", "")
            tag = f" ({lab})" if lab else ""
            lines.append(f"- `{src}` → `{dest}`{tag}")
        if len(moves) > max_moves:
            lines.append(f"- … and {len(moves) - max_moves} more (see `state/file_rescue.json`)")
        lines.append("")
    if pruned:
        lines.append("### Pruned path leaks")
        for p in pruned[:15]:
            lines.append(f"- {p}")
        lines.append("")
    if not for_persist:
        lines.append(
            f"_Details: `{RESCUE_STATE_REL}` — update code only under the canonical workspace._"
        )
        lines.append("")
    return "\n".join(lines)


def load_rescue_prompt_for_executor(project_dir: Path) -> str:
    """Prefer fresh markdown hint; fall back to rebuilding from JSON."""
    project_dir = Path(project_dir)
    md = rescue_prompt_path(project_dir)
    if md.is_file():
        try:
            text = md.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                return text + "\n"
        except OSError:
            pass
    rec = load_rescue_record(project_dir)
    block = format_rescue_prompt_block(rec)
    return (block + "\n") if block else ""
