"""Template Library for multi-agent SOP execution.

Manages registration, listing, and deletion of prompt templates
with category support and builtin templates.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional


class TemplateLibrary:
    """In-memory + filesystem-backed template library."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base = base_dir or Path(os.environ.get("DST_TEMPLATES_DIR", "."))
        self._templates_dir = self._base / "templates"
        self._templates_dir.mkdir(parents=True, exist_ok=True)
        self._builtin_dir = self._templates_dir / "builtin"
        self._builtin_dir.mkdir(parents=True, exist_ok=True)
        # In-memory store (name -> content)
        self._store: Dict[str, str] = {}
        # Category mapping (name -> category)
        self._categories: Dict[str, str] = {}
        # Load existing templates from disk
        self._load_existing_templates()

    # ---- Initialization ----

    def _load_existing_templates(self) -> None:
        """Load existing templates from disk."""
        if not self._templates_dir.exists():
            return
        
        for md_file in self._templates_dir.rglob("*.md"):
            try:
                name = md_file.stem
                content = md_file.read_text(encoding="utf-8")
                self._store[name] = content
                # Determine category from path
                rel_path = md_file.relative_to(self._templates_dir)
                if len(rel_path.parts) > 1:
                    self._categories[name] = rel_path.parts[0]
                else:
                    self._categories[name] = "default"
            except (IOError, OSError):
                continue

    # ---- Registration ----

    def register_template(
        self,
        name: str,
        content: str,
        category: Optional[str] = None,
    ) -> None:
        """Register a template by name."""
        if not name:
            raise ValueError("Template name cannot be empty")
        self._store[name] = content
        if category:
            self._categories[name] = category
        else:
            self._categories[name] = "default"
        # Persist to disk
        if category and category != "default":
            target = self._templates_dir / category / f"{name}.md"
        else:
            target = self._templates_dir / f"{name}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    # ---- Retrieval ----

    def get_template(self, name: str) -> str:
        """Get a template by name.

        Raises:
            FileNotFoundError:  If no template with *name* exists.
        """
        if name in self._store:
            return self._store[name]
        # Check templates subdir and builtin dir
        for root in [self._templates_dir, self._builtin_dir]:
            for sub in root.rglob(f"{name}.md"):
                return sub.read_text(encoding="utf-8")
        # Also check base dir directly (for env-var paths where files are at root)
        direct = self._base / f"{name}.md"
        if direct.exists():
            return direct.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Template '{name}' not found.")

    # ---- Listing ----

    def get_template_categories(self) -> List[str]:
        """Get all unique template categories."""
        return sorted(set(self._categories.values()))

    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """List template names, optionally filtered by *category*."""
        # Scan filesystem for .md files: check templates subdir AND base dir directly
        fs_templates = set()
        scan_roots = [self._templates_dir]
        # Also scan the base dir (one level up from templates/) in case files were
        # written there directly (e.g. via DST_TEMPLATES_DIR env path).
        if self._templates_dir.parent != self._templates_dir:
            scan_roots.append(self._templates_dir.parent)
        for root in scan_roots:
            for md_file in root.glob("*.md"):
                fs_templates.add(md_file.stem)
        for md_file in self._templates_dir.rglob("*.md"):
            fs_templates.add(md_file.stem)
        for md_file in self._builtin_dir.rglob("*.md"):
            fs_templates.add(md_file.stem)

        # Combine in-memory and filesystem templates
        all_templates = set(self._store.keys()) | fs_templates

        if category is None:
            return sorted(all_templates)
        return sorted([n for n in all_templates if self._categories.get(n) == category])

    # ---- Deletion ----

    def delete_template(self, name: str) -> bool:
        """Delete a template. Returns True if deleted, False if not found."""
        deleted = False
        # Remove from in-memory store
        if name in self._store:
            del self._store[name]
            deleted = True
        if name in self._categories:
            del self._categories[name]
        # Remove from templates subdir and builtin dir
        for root in [self._templates_dir, self._builtin_dir]:
            for p in root.rglob(f"{name}.md"):
                p.unlink(missing_ok=True)
                deleted = True
        # Also remove from base dir directly
        direct = self._base / f"{name}.md"
        if direct.exists():
            direct.unlink(missing_ok=True)
            deleted = True
        return deleted

    # ---- Builtin templates ----

    BUILTIN_TEMPLATES: Dict[str, str] = {
        "default_step": (
            "# Step: {{step_name}}\n"
            "{{step_description}}\n\n"
            "## Input\n"
            "{{input_context}}\n\n"
            "## Previous Output\n"
            "{{previous_output}}\n\n"
            "## Output Format\n"
            "{{output_format}}"
        ),
    }

    def load_builtin_templates(self) -> None:
        """Load all builtin templates into the library."""
        for name, content in self.BUILTIN_TEMPLATES.items():
            if name not in self._store:
                self.register_template(name, content, category="builtin")
        # Persist builtin dir
        for name, content in self.BUILTIN_TEMPLATES.items():
            target = self._builtin_dir / f"{name}.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
