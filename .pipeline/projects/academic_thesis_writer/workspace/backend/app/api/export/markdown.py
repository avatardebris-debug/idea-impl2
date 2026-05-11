"""Markdown exporter for thesis drafts."""

from __future__ import annotations

import logging
from typing import Optional

from ..models import Draft

logger = logging.getLogger(__name__)


class MarkdownExporter:
    """Export a thesis draft as Markdown."""

    @staticmethod
    def export(draft: Draft) -> str:
        """Export the draft as a Markdown string."""
        md = f"# {draft.title}\n\n"
        md += f"**Topic:** {draft.topic}\n\n"
        md += f"**Citation Style:** {draft.citation_style.value}\n\n"

        if draft.abstract:
            md += f"## Abstract\n\n{draft.abstract}\n\n"

        for section in draft.sections:
            md += f"## {section.name}\n\n{section.content}\n\n"

        if draft.bibliography:
            md += "## Bibliography\n\n"
            for entry in draft.bibliography:
                md += f"- {entry.formatted}\n"

        return md

    @staticmethod
    def save(draft: Draft, file_path: str) -> None:
        """Save the draft as a Markdown file."""
        content = MarkdownExporter.export(draft)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Saved Markdown to %s", file_path)
