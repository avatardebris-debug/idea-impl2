"""Template engine — renders text templates with variable substitution."""

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Renders text templates by substituting {{ variable }} placeholders."""

    def render(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a template file with the given context.

        Args:
            template_path: Path to the template file.
            context: Dictionary of variable names to values.

        Returns:
            The rendered template string.
        """
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        rendered = template
        for key, value in context.items():
            placeholder = "{{ " + key + " }}"
            rendered = rendered.replace(placeholder, str(value))

        # Clean up any remaining unresolved placeholders
        import re
        remaining = re.findall(r"\{\{ \w+ \}\}", rendered)
        if remaining:
            logger.warning("Unresolved placeholders: %s", remaining)

        return rendered
