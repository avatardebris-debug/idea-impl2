"""Template engine for NDA contract generation using Jinja2."""

import logging
import os
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Renders NDA contracts from templates and clause data."""

    def __init__(self, template_dir: Optional[str] = None):
        """Initialize the template engine.

        Args:
            template_dir: Directory containing template files.
                         Defaults to templates/ in the project root.
        """
        if template_dir is None:
            template_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "templates",
            )
        self._template_dir = template_dir
        self._env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,
        )
        logger.info("Template engine initialized with directory: %s", template_dir)

    def render_contract(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """Render a contract from a template and context data.

        Args:
            template_name: Name of the template file (e.g., 'nda_california.txt').
            context: Dictionary of variables to inject into the template.

        Returns:
            The rendered contract text.

        Raises:
            TemplateNotFound: If the template file does not exist.
            ValueError: If required context variables are missing.
        """
        try:
            template = self._env.get_template(template_name)
        except TemplateNotFound:
            logger.error("Template not found: %s in %s", template_name, self._template_dir)
            raise

        # Validate required variables
        required_vars = self._get_required_vars(template)
        missing = [v for v in required_vars if v not in context or context[v] is None]
        if missing:
            raise ValueError(f"Missing required context variables: {', '.join(missing)}")

        rendered = template.render(**context)
        logger.info("Successfully rendered template '%s'", template_name)
        return rendered

    def list_templates(self) -> List[str]:
        """List all available templates.

        Returns:
            List of template file names.
        """
        try:
            templates = self._env.list_templates()
            logger.info("Found %d templates", len(templates))
            return templates
        except Exception as e:
            logger.warning("Could not list templates: %s", e)
            return []

    def _get_required_vars(self, template: "Template") -> List[str]:
        """Extract required variable names from a template.

        Args:
            template: A Jinja2 Template object.

        Returns:
            List of variable names used in the template.
        """
        # Parse the template to find all variable references
        required_vars = set()
        for node in template.root_node.iter_nodes():
            from jinja2.nodes import Name, Getitem, Getattr

            if isinstance(node, Name):
                required_vars.add(node.name)
            elif isinstance(node, Getitem):
                if isinstance(node.node, Name):
                    required_vars.add(node.node.name)
            elif isinstance(node, Getattr):
                if isinstance(node.node, Name):
                    required_vars.add(node.node.name)
        return list(required_vars)

    def validate_template(self, template_name: str) -> Dict[str, Any]:
        """Validate that a template exists and can be parsed.

        Args:
            template_name: Name of the template file to validate.

        Returns:
            Dict with 'valid' (bool), 'error' (str or None), and 'vars' (list).
        """
        try:
            template = self._env.get_template(template_name)
            vars_list = self._get_required_vars(template)
            return {"valid": True, "error": None, "vars": vars_list}
        except TemplateNotFound:
            return {"valid": False, "error": f"Template '{template_name}' not found", "vars": []}
        except Exception as e:
            return {"valid": False, "error": str(e), "vars": []}
