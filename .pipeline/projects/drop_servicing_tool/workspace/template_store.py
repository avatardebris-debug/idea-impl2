"""
Template store for pre-built SOP templates.

Manages loading, listing, and creating SOPs from templates.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .sop_schema import SOP, SOPStep
from .sop_store import create_sop, get_sop, list_sops as _list_sops


_DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _get_templates_dir() -> Path:
    """Get the templates directory."""
    env_dir = os.environ.get("SOP_TEMPLATES_DIR")
    if env_dir:
        return Path(env_dir)
    return _DEFAULT_TEMPLATES_DIR


class TemplateStore:
    """Manages SOP templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self._templates_dir = templates_dir or _get_templates_dir()
        self._templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[str]:
        """List all available templates."""
        if not self._templates_dir.exists():
            return []
        return [p.stem for p in self._templates_dir.glob("*.yaml")]

    def get_template(self, name: str) -> Optional[Dict]:
        """Get a template by name."""
        template_path = self._templates_dir / f"{name}.yaml"
        if not template_path.exists():
            return None

        import yaml
        with open(template_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def create_from_template(self, name: str, output_name: Optional[str] = None) -> Optional[Path]:
        """Create a new SOP from a template."""
        template = self.get_template(name)
        if template is None:
            return None

        output_name = output_name or template["name"]
        return create_sop(output_name, template)

    def create_from_template_path(
        self,
        template_path: Path,
        output_name: Optional[str] = None,
    ) -> Optional[Path]:
        """Create a new SOP from a template file path."""
        import yaml
        with open(template_path, "r", encoding="utf-8") as f:
            template = yaml.safe_load(f)

        output_name = output_name or template.get("name", template_path.stem)
        return create_sop(output_name, template)


def list_templates() -> List[str]:
    """Convenience function to list all available templates."""
    store = TemplateStore()
    return store.list_templates()


def get_template(name: str) -> Optional[Dict]:
    """Convenience function to get a template by name."""
    store = TemplateStore()
    return store.get_template(name)


def create_from_template(name: str, output_name: Optional[str] = None) -> Optional[Path]:
    """Convenience function to create a SOP from a template."""
    store = TemplateStore()
    return store.create_from_template(name, output_name)
