"""Response generator — creates draft responses from templates and tone styles."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml

from supportagent.models import DraftResponse, Ticket


class ResponseGeneratorError(Exception):
    """Raised when response generation fails."""


class ResponseGenerator:
    """Generates draft responses using templates and tone styles."""

    def __init__(
        self,
        config_dir: Optional[str] = None,
    ):
        """Initialize the response generator.

        Args:
            config_dir: Directory containing config YAML files.
        """
        if config_dir is None:
            config_dir = os.path.join(
                os.path.dirname(__file__), "config"
            )
        self.config_dir = config_dir
        self._templates: Dict[str, str] = {}
        self._tone_styles: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load templates and tone styles from config files."""
        # Load templates
        templates_path = os.path.join(self.config_dir, "templates.yaml")
        if os.path.exists(templates_path):
            with open(templates_path, "r") as f:
                data = yaml.safe_load(f)
                self._templates = data.get("templates", {})

        # Load tone styles
        tones_path = os.path.join(self.config_dir, "tone_styles.yaml")
        if os.path.exists(tones_path):
            with open(tones_path, "r") as f:
                data = yaml.safe_load(f)
                self._tone_styles = data.get("tone_styles", {})

    def generate_response(
        self,
        ticket: Ticket,
        template_name: str = "general_response",
        tone: str = "professional",
        team: str = "general_team",
    ) -> DraftResponse:
        """Generate a draft response for a ticket.

        Args:
            ticket: The ticket to respond to.
            template_name: Name of the template to use.
            tone: Tone style to apply.
            team: Team generating the response.

        Returns:
            A DraftResponse object.

        Raises:
            ResponseGeneratorError: If template or tone is not found.
        """
        template = self._get_template(template_name)
        tone_style = self._get_tone_style(tone)

        content = self._fill_template(template, ticket, tone_style)

        draft = DraftResponse(
            ticket=ticket,
            content=content,
            tone=tone,
            template_used=template_name,
            team=team,
        )

        return draft

    def _get_template(self, name: str) -> str:
        """Get a template by name."""
        if name in self._templates:
            return self._templates[name]
        raise ResponseGeneratorError(f"Template not found: {name}")

    def _get_tone_style(self, tone: str) -> Any:
        """Get a tone style by name."""
        if tone in self._tone_styles:
            return self._tone_styles[tone]
        raise ResponseGeneratorError(f"Tone style not found: {tone}")

    def _fill_template(
        self,
        template: str,
        ticket: Ticket,
        tone_style: Any,
    ) -> str:
        """Fill a template with ticket data and tone adjustments."""
        content = template

        # Replace placeholders
        content = content.replace("{ticket_id}", ticket.ticket_id)
        content = content.replace("{subject}", ticket.subject)
        content = content.replace("{body}", ticket.body)
        content = content.replace("{category}", ticket.category.value if ticket.category else "general")
        content = content.replace("{priority}", str(ticket.priority_score))
        content = content.replace("{created_at}", ticket.created_at)

        # Apply tone adjustments
        content = self._apply_tone(content, tone_style)

        return content

    def _apply_tone(self, content: str, tone_style: Any) -> str:
        """Apply tone adjustments to content."""
        # Add greeting based on tone
        greeting = tone_style.get("greeting", "Hello")
        closing = tone_style.get("closing", "Best regards")
        formality = tone_style.get("formality", "medium")

        # Insert greeting at the beginning
        if content.startswith("{"):
            content = f"{greeting},\n\n{content}"
        else:
            content = f"{greeting},\n\n{content}"

        # Add closing at the end
        content = f"{content}\n\n{closing}"

        return content

    def list_templates(self) -> list:
        """List all available templates."""
        return list(self._templates.keys())

    def list_tone_styles(self) -> list:
        """List all available tone styles."""
        return list(self._tone_styles.keys())
