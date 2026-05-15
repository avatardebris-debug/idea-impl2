"""sec_importer parsers stub for the forensic suite."""

from __future__ import annotations

from typing import List
from sec_importer.models import FilingItemModel


class FilingParser:
    """Stub filing parser for import compatibility."""

    def parse(self, filing_text: str, filing_type: str = "10-K") -> List[FilingItemModel]:
        """Parse filing text into FilingItemModel objects.
        
        This stub returns an empty list. The real parser lives in the
        sec_importer pipeline project.
        """
        return []
