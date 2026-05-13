"""Jinja2-based template engine for README and changelog generation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from jinja2 import Environment, FileSystemLoader, BaseLoader
except ImportError:
    raise ImportError("pip install jinja2  # required for README template engine")


DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "readme_templates" / "default"
DEFAULT_CHANGELOG_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


class TemplateEngine:
    """Load and render Jinja2 markdown templates with variable substitution."""

    def __init__(
        self,
        template_dir: Optional[str | Path] = None,
        template_file: str = "readme.md.j2",
    ):
        """Initialize the template engine.

        Args:
            template_dir: Directory containing template files. Defaults to the
                          built-in default directory.
            template_file: Name of the template file to render.
        """
        self.template_file = template_file
        if template_dir:
            self._env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self._env = Environment(
                loader=FileSystemLoader(str(DEFAULT_TEMPLATE_DIR)),
                trim_blocks=True,
                lstrip_blocks=True,
            )

    def render(self, template_name: Optional[str] = None, **context: Any) -> str:
        """Render a template with the given context variables.

        Args:
            template_name: Optional template filename to override the default.
            **context: Variables to substitute into the template.

        Returns:
            The rendered template string.
        """
        name = template_name or self.template_file
        template = self._env.get_template(name)
        return template.render(**context)

    def render_string(self, template_string: str, **context: Any) -> str:
        """Render a template from a raw string.

        Args:
            template_string: Jinja2 template source.
            **context: Variables to substitute.

        Returns:
            The rendered template string.
        """
        template = self._env.from_string(template_string)
        return template.render(**context)
