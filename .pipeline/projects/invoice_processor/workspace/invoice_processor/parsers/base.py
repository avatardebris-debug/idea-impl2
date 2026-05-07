"""Parser interface for invoice files."""

from abc import ABC, abstractmethod
from typing import List, Optional, Union

from invoice_processor.models import Invoice


class BaseParser(ABC):
    """Abstract base class for invoice parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> Union[Invoice, List[Invoice]]:
        """Parse an invoice file and return an Invoice object or list of Invoice objects.

        Returns None if the file cannot be parsed or key fields are missing.
        """
        pass

    @abstractmethod
    def supports_file(self, file_path: str) -> bool:
        """Check if this parser supports the given file type."""
        pass
