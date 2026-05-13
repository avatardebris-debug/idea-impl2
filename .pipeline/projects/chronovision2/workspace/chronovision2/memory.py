"""
memory.py
Persistent memory system for the agent.

Stores facts, decisions, and task lists in markdown files under .agent/.
"""

from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Any


class MemorySystem:
    """Manages persistent memory files."""

    def __init__(self, base_dir: str = ".agent"):
        self.base_dir = pathlib.Path(base_dir)
        self.facts_file = self.base_dir / "memory" / "facts.md"
        self.decisions_file = self.base_dir / "memory" / "decisions.md"
        self.tasks_file = self.base_dir / "tasks.md"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create memory directories if they don't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "memory").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Facts
    # ------------------------------------------------------------------

    def add_fact(self, fact: str) -> str:
        """Add a persistent fact."""
        entry = f"\n- {fact}"
        return self._append(self.facts_file, entry)

    def read_facts(self) -> str:
        """Read all stored facts."""
        return self._read_file(self.facts_file)

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------

    def add_decision(self, decision: str, reason: str) -> str:
        """Record a decision with its rationale."""
        timestamp = datetime.now().isoformat()
        entry = f"\n## {timestamp}\n- Decision: {decision}\n- Reason: {reason}"
        return self._append(self.decisions_file, entry)

    def read_decisions(self) -> str:
        """Read all stored decisions."""
        return self._read_file(self.decisions_file)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def add_task(self, task: str, priority: int = 5) -> str:
        """Add a task to the task list."""
        entry = f"\n- [{priority}] {task}"
        return self._append(self.tasks_file, entry)

    def read_tasks(self) -> str:
        """Read all tasks."""
        return self._read_file(self.tasks_file)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_file(self, path: pathlib.Path) -> str:
        """Read a file, returning empty string if it doesn't exist."""
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _append(self, path: pathlib.Path, content: str) -> str:
        """Append content to a file, creating it if needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.write_text(path.read_text(encoding="utf-8") + content, encoding="utf-8")
        else:
            path.write_text(content, encoding="utf-8")
        return content
