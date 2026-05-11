"""Reusable ExportEngine with plugin registration pattern.

Extracted from multi_format_export_engine.
Provides a base ExportEngine class with register_exporter / export dispatch.
"""

from typing import Any, Dict, Optional


class ExportEngine:
    """Manages export of documents to various formats via registered exporters.

    Usage:
        engine = ExportEngine()
        engine.register_exporter("epub", EPUBExporter())
        engine.register_exporter("pdf", PDFExporter())
        engine.export("epub", document, output_path="output.epub")
    """

    def __init__(self):
        self._exporters: Dict[str, Any] = {}

    def register_exporter(self, fmt: str, exporter: Any) -> None:
        """Register an exporter for a given format string."""
        self._exporters[fmt.lower()] = exporter

    def export(
        self,
        fmt: str,
        document: Any,
        output_path: Optional[str] = None,
        **options: Any,
    ) -> str:
        """Export the document to the given format.

        Args:
            fmt: Format string, e.g. 'epub', 'pdf', 'mobi'.
            document: The document to export.
            output_path: Optional output file path. If None, a default
                         name is generated in the current directory.
            **options: Format-specific export options.

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
            base_name = getattr(document, "title", "output").strip().replace(" ", "_")
            output_path = f"{base_name}.{fmt_lower}"

        return exporter.export(document, output_path=output_path, **options)
