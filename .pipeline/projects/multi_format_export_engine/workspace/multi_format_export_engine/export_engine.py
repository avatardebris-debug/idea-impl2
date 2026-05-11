"""Base export engine with support for multiple export formats."""

import os
from typing import Any, Dict, Optional

from .models import Manuscript


class ExportEngine:
    """Manages export of a Manuscript to various formats.

    Subclass and register exporters for new formats.
    """

    def __init__(self):
        self._exporters: Dict[str, Any] = {}

    def register_exporter(self, fmt: str, exporter: Any) -> None:
        """Register an exporter for a given format string."""
        self._exporters[fmt.lower()] = exporter

    def export(
        self,
        fmt: str,
        manuscript: Manuscript,
        output_path: Optional[str] = None,
        **options: Any,
    ) -> str:
        """Export the manuscript to the given format.

        Args:
            fmt: Format string, e.g. 'epub', 'pdf', 'mobi'.
            manuscript: The Manuscript to export.
            output_path: Optional output file path. If None, a default
                         name is generated in the current directory.
            **options: Format-specific export options (margins, fonts, etc.).

        Returns:
            The path to the generated export file.
        """
        fmt_lower = fmt.lower()
        if fmt_lower not in self._exporters:
            raise ValueError(
                f"Unsupported format '{fmt}'. "
                f"Available formats: {list(self._exporters.keys())}"
            )

        exporter = self._exporters[fmt_lower]

        if output_path is None:
            base_name = manuscript.title.strip().replace(" ", "_")
            output_path = f"{base_name}.{fmt_lower}"

        return exporter.export(manuscript, output_path=output_path, **options)
