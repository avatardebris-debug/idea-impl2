"""Citation engine.

Coordinates formatting, key generation, and bibliography assembly
for a thesis draft.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ..models import BibliographyEntry, CitationStyle, Source
from .formatters import APAFormatter, ChicagoFormatter, IEEEFormatter, MLAFormatter
from .key_generator import KeyGenerator

logger = logging.getLogger(__name__)

# Map styles to formatters
_FORMATTERS = {
    CitationStyle.APA: APAFormatter,
    CitationStyle.MLA: MLAFormatter,
    CitationStyle.CHICAGO: ChicagoFormatter,
    CitationStyle.IEEE: IEEEFormatter,
}


class CitationEngine:
    """Orchestrates citation formatting for a thesis."""

    def __init__(self, style: CitationStyle = CitationStyle.APA):
        self.style = style
        self.formatter = _FORMATTERS[style]
        self.key_gen = KeyGenerator()
        self._entries: List[BibliographyEntry] = []

    def format_source(self, source: Source) -> BibliographyEntry:
        """Format a single source according to the configured style."""
        key = self.key_gen.generate_key(source)
        entry = self.formatter.format(source, key)
        self._entries.append(entry)
        return entry

    def format_all(self, sources: List[Source]) -> List[BibliographyEntry]:
        """Format all sources and return bibliography entries."""
        self._entries = []
        for source in sources:
            self.format_source(source)
        return self._entries

    def format_inline(self, source: Source, page: Optional[str] = None) -> str:
        """Get an inline citation for a source."""
        if hasattr(self.formatter, "format_inline"):
            return self.formatter.format_inline(source, page)
        key = self.key_gen.generate_key(source)
        return f"[{key}]"

    def get_bibliography(self) -> List[BibliographyEntry]:
        """Return the formatted bibliography."""
        return self._entries

    def get_bibliography_text(self) -> str:
        """Return the bibliography as plain text."""
        lines = []
        for entry in self._entries:
            lines.append(entry.formatted)
        return "\n".join(lines)
