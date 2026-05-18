"""
pdf_schema — Extract and validate complex structures from unstructured PDF documents.

Strategy (zero pip deps for core):
  1. Try pdfminer.six → best text extraction
  2. Try PyPDF2 / pypdf  → fallback
  3. Try pdfplumber     → table-aware fallback
  4. Subprocess → pdftotext (poppler) if installed

Then uses an LLM to identify the schema (key fields, tables, sections)
and validates completeness / extracts structured data.

Usage:
    python -m pdf_schema document.pdf --schema invoice
    python -m pdf_schema document.pdf --discover          # infer schema from content
    python -m pdf_schema document.pdf --schema invoice --output data.json
    python -m pdf_schema document.pdf --text-only         # just extract text
"""
__version__ = "0.1.0"
