"""
Template Versioning Module

Extends the template system with version control, A/B testing, and
custom template creation.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TemplateVersion:
    """A single version of a template."""
    version: int
    content: Dict[str, Any]
    created_at: str = ""
    author: str = "system"
    changelog: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class ABTestResult:
    """Result of an A/B test between two template versions."""
    template_name: str
    version_a: int
    version_b: int
    winner: Optional[int] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    tested_at: str = ""

    def __post_init__(self):
        if not self.tested_at:
            self.tested_at = datetime.now().isoformat()


class TemplateVersionManager:
    """Manages template versions, history, and A/B testing."""

    def __init__(self, storage_dir: Optional[str] = None):
        self._templates: Dict[str, List[TemplateVersion]] = {}
        self._ab_tests: List[ABTestResult] = []
        self._storage_dir = Path(storage_dir) if storage_dir else None
        if self._storage_dir:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()

    # ── Version management ───────────────────────────────────────────

    def create_template(self, name: str, content: Dict[str, Any],
                        author: str = "system", changelog: str = "Initial version") -> TemplateVersion:
        """Create a new template (version 1)."""
        if name in self._templates:
            raise ValueError(f"Template '{name}' already exists. Use save_version().")
        ver = TemplateVersion(version=1, content=content, author=author, changelog=changelog)
        self._templates[name] = [ver]
        self._persist(name)
        return ver

    def save_version(self, name: str, content: Dict[str, Any],
                     author: str = "system", changelog: str = "") -> TemplateVersion:
        """Save a new version of an existing template."""
        if name not in self._templates:
            return self.create_template(name, content, author, changelog)
        history = self._templates[name]
        new_ver = TemplateVersion(
            version=history[-1].version + 1,
            content=content, author=author, changelog=changelog,
        )
        history.append(new_ver)
        self._persist(name)
        return new_ver

    def get_version(self, name: str, version: Optional[int] = None) -> Optional[TemplateVersion]:
        """Get a specific version (latest if version is None)."""
        history = self._templates.get(name)
        if not history:
            return None
        if version is None:
            return history[-1]
        for v in history:
            if v.version == version:
                return v
        return None

    def get_latest(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the latest version's content."""
        ver = self.get_version(name)
        return ver.content if ver else None

    def get_history(self, name: str) -> List[Dict[str, Any]]:
        """Get the full version history for a template."""
        history = self._templates.get(name, [])
        return [
            {"version": v.version, "author": v.author,
             "changelog": v.changelog, "created_at": v.created_at}
            for v in history
        ]

    def rollback(self, name: str, to_version: int) -> Optional[TemplateVersion]:
        """Rollback by saving a copy of an older version as the newest."""
        old = self.get_version(name, to_version)
        if not old:
            return None
        return self.save_version(
            name, copy.deepcopy(old.content),
            changelog=f"Rollback to version {to_version}",
        )

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates with their latest version info."""
        result = []
        for name, history in self._templates.items():
            latest = history[-1]
            result.append({
                "name": name,
                "latest_version": latest.version,
                "total_versions": len(history),
                "last_updated": latest.created_at,
            })
        return result

    def delete_template(self, name: str) -> bool:
        """Delete a template and all its versions."""
        if name not in self._templates:
            return False
        del self._templates[name]
        if self._storage_dir:
            f = self._storage_dir / f"{name}.json"
            f.unlink(missing_ok=True)
        return True

    # ── A/B Testing ──────────────────────────────────────────────────

    def create_ab_test(self, name: str, version_a: int, version_b: int) -> ABTestResult:
        """Create an A/B test between two versions."""
        va = self.get_version(name, version_a)
        vb = self.get_version(name, version_b)
        if not va or not vb:
            raise ValueError("Both versions must exist.")
        result = ABTestResult(template_name=name, version_a=version_a, version_b=version_b)
        self._ab_tests.append(result)
        return result

    def record_ab_result(self, test_index: int, winner: int,
                         metrics: Optional[Dict[str, Any]] = None,
                         notes: str = "") -> ABTestResult:
        """Record the result of an A/B test."""
        if test_index >= len(self._ab_tests):
            raise IndexError("Invalid test index.")
        test = self._ab_tests[test_index]
        test.winner = winner
        test.metrics = metrics or {}
        test.notes = notes
        return test

    def get_ab_tests(self, name: Optional[str] = None) -> List[ABTestResult]:
        """Get A/B test results, optionally filtered by template name."""
        if name:
            return [t for t in self._ab_tests if t.template_name == name]
        return list(self._ab_tests)

    # ── Persistence ──────────────────────────────────────────────────

    def _persist(self, name: str):
        if not self._storage_dir:
            return
        history = self._templates.get(name, [])
        data = [{"version": v.version, "content": v.content,
                 "created_at": v.created_at, "author": v.author,
                 "changelog": v.changelog} for v in history]
        f = self._storage_dir / f"{name}.json"
        f.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_from_disk(self):
        if not self._storage_dir:
            return
        for f in self._storage_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                name = f.stem
                self._templates[name] = [
                    TemplateVersion(
                        version=d["version"], content=d["content"],
                        created_at=d.get("created_at", ""),
                        author=d.get("author", "system"),
                        changelog=d.get("changelog", ""),
                    ) for d in data
                ]
            except (json.JSONDecodeError, KeyError):
                continue
