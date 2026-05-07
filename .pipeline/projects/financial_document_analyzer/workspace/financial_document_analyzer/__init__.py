"""Financial Document Analyzer — reads financial PDFs and CSVs,
extracts key metrics and produces structured summary reports."""

__version__ = "0.1.0"

from financial_document_analyzer.parsers import parse_csv, parse_pdf
from financial_document_analyzer.reporters import generate_report

__all__ = ["parse_csv", "parse_pdf", "generate_report"]
