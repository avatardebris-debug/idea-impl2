"""audiobook2pdf — Amazon audiobook to PDF converter."""

__version__ = "0.1.0"

from audiobook2pdf.extractor import extract_metadata, MetadataExtractError
from audiobook2pdf.pdf_generator import generate_pdf, PDFGenerationError

__all__ = [
    "extract_metadata",
    "generate_pdf",
    "MetadataExtractError",
    "PDFGenerationError",
]
