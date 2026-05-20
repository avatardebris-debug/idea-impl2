"""
skill_store.py — Save and manage extracted skills.

A skill is a structured extraction result (recipe/steps/SOP) that a user
wants to keep for later use. Skills are stored as JSON files in a configurable
directory.

Usage:
    from extraction.skill_store import SkillStore
    store = SkillStore()
    store.save(skill_dict, name="sourdough-bread")
    skills = store.list()
    skill = store.get("sourdough-bread")
    store.delete("sourdough-bread")
"""
from __future__ import annotations
import json
import pathlib
import shutil
from datetime import datetime
from typing import Any


class SkillStore:
    """Persist extracted skills to disk as JSON files."""

    DEFAULT_DIR = pathlib.Path.home() / ".extraction_skills"

    def __init__(self, dir: pathlib.Path | str | None = None) -> None:
        self._dir = pathlib.Path(dir) if dir else self.DEFAULT_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    # ---- public API ----

    def save(self, skill: dict[str, Any], name: str | None = None) -> pathlib.Path:
        """Save a skill dict to disk. Returns the path written."""
        if name is None:
            name = skill.get("title", "untitled")
        # Sanitise name for filesystem safety
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        path = self._dir / f"{safe_name}.json"
        payload = {
            **skill,
            "_saved_at": datetime.now(timezone.utc).isoformat(),
            "_version": "1.0",
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def get(self, name: str) -> dict[str, Any] | None:
        """Load a skill by name. Returns None if not found."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        path = self._dir / f"{safe_name}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self) -> list[dict[str, Any]]:
        """Return all saved skills as a list of dicts."""
        skills = []
        for path in sorted(self._dir.glob("*.json")):
            try:
                skills.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return skills

    def delete(self, name: str) -> bool:
        """Delete a skill by name. Returns True if deleted, False if not found."""
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        path = self._dir / f"{safe_name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Remove all saved skills. Returns count of removed skills."""
        count = 0
        for path in self._dir.glob("*.json"):
            path.unlink()
            count += 1
        return count
