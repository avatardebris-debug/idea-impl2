"""Invoice file parsers package."""

from invoice_processor.parsers.base import BaseParser
from invoice_processor.parsers.csv_parser import CSVParser
from invoice_processor.parsers.pdf_parser import PDFParser

__all__ = ['BaseParser', 'PDFParser', 'CSVParser']


def get_parser(file_path: str) -> BaseParser:
    """Get the appropriate parser for a given file path."""
    if file_path.lower().endswith('.pdf'):
        return PDFParser()
    elif file_path.lower().endswith('.csv'):
        return CSVParser()
    else:
        raise ValueError(f"No parser available for file type: {file_path}")
