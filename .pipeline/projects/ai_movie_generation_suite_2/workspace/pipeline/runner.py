"""
pipeline.runner
Core pipeline logic: seeds ideas from master_ideas.md, resolves dependencies,
and dispatches to agents.
"""

from __future__ import annotations
import json
import pathlib
import re
from typing import Any

# Import Message class for creating messages
from pipeline.message_bus import Message


# ── Globals ────────────────────────────────────────────────────────

PROJECT_ROOT: pathlib.Path = pathlib.Path(".")
PIPELINE_DIR: pathlib.Path = pathlib.Path(".pipeline")
_seeded_this_session: set[str] = set()


# ── Slug helper ─────────────────────────────────────────────────────

def _slugify(title: str) -> str:
    """
    Convert a title to a slug:
    - Strip brackets [...]
    - Lowercase
    - Replace non-alphanumeric with underscores
    - Collapse multiple underscores
    - Strip leading/trailing underscores
    """
    # Strip brackets
    text = re.sub(r'\[([^\]]*)\]', r'\1', title)
    # Lowercase
    text = text.lower()
    # Replace non-alphanumeric (except spaces) with underscores
    text = re.sub(r'[^a-z0-9]+', '_', text)
    # Collapse multiple underscores
    text = re.sub(r'_+', '_', text)
    # Strip leading/trailing underscores
    text = text.strip('_')
    return text


# ── Dependency checking ────────────────────────────────────────────

def _is_dep_complete(dep_slug: str) -> tuple[bool, str]:
    """
    Check if a dependency project is complete.

    Returns:
        (is_complete, workspace_path)
    """
    proj_dir = PIPELINE_DIR / "projects" / dep_slug
    if not proj_dir.exists():
        return False, ""

    state_file = proj_dir / "state" / "current_idea.json"
    if not state_file.exists():
        return False, ""

    try:
        state = json.loads(state_file.read_text())
        status = state.get("status", "")
        # "complete" or "budget_exceeded" counts as done
        is_complete = status in ("complete", "budget_exceeded")
        workspace_path = str(proj_dir / "workspace")
        return is_complete, workspace_path
    except (json.JSONDecodeError, OSError):
        return False, ""


# ── Master ideas parser ────────────────────────────────────────────

def _parse_ideas(master_ideas_path: pathlib.Path) -> list[dict]:
    """
    Parse master_ideas.md and return a list of idea dicts.

    Each line matching:
        - [ ] **[Title]** — [description. requires: dep1, dep2]

    Returns list of dicts with keys:
        title, idea, idea_slug, depends_on
    """
    ideas = []
    content = master_ideas_path.read_text(encoding="utf-8")

    for line in content.splitlines():
        line = line.strip()
        # Match: - [ ] **[Title]** — [description. requires: dep1, dep2]
        match = re.match(
            r'-\s*\[\s*\]\s*\*\*\*(.+?)\*\*\*\s*—\s*\[(.+?)\]',
            line
        )
        if match:
            title = match.group(1).strip()
            desc = match.group(2).strip()

            # Extract requires
            requires_match = re.search(r'requires:\s*(.+)', desc, re.IGNORECASE)
            depends_on = []
            if requires_match:
                deps_str = requires_match.group(1).strip()
                depends_on = [d.strip() for d in deps_str.split(',') if d.strip()]
                # Strip the requires suffix from the description
                idea_text = desc[:requires_match.start()].strip()
            else:
                idea_text = desc

            idea_slug = _slugify(title)
            ideas.append({
                "title": title,
                "idea": idea_text,
                "idea_slug": idea_slug,
                "depends_on": depends_on,
            })

    return ideas


# ── Main seeding function ───────────────────────────────────────────

def seed_from_master_list(bus: Any) -> bool:
    """
    Read master_ideas.md and seed any ideas whose dependencies are met.

    Args:
        bus: Message bus with a send() method.

    Returns:
        True if at least one idea was seeded, False if all are blocked.
    """
    master_ideas_path = PROJECT_ROOT / "master_ideas.md"
    if not master_ideas_path.exists():
        return False

    ideas = _parse_ideas(master_ideas_path)
    seeded_any = False

    for idea in ideas:
        slug = idea["idea_slug"]

        # Skip already-seeded ideas
        if slug in _seeded_this_session:
            continue

        # Check dependencies
        depends_on = idea["depends_on"]
        dep_workspaces: dict[str, str] = {}
        all_complete = True

        if depends_on:
            for dep_slug in depends_on:
                is_complete, ws_path = _is_dep_complete(dep_slug)
                if is_complete:
                    dep_workspaces[dep_slug] = ws_path
                else:
                    all_complete = False
                    break
        else:
            all_complete = True

        if all_complete:
            # Seed this idea
            _seeded_this_session.add(slug)

            payload = {
                "title": idea["title"],
                "idea": idea["idea"],
                "idea_slug": slug,
                "depends_on": depends_on,
                "dep_workspaces": dep_workspaces,
            }

            # Send message to idea_planner
            bus.send(type="seed_idea", payload=payload)
            seeded_any = True

    return seeded_any
