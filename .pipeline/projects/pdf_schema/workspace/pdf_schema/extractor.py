"""
extractor.py — Multi-backend PDF text extraction.

Tries backends in priority order and returns the best result.
No backend is required — all failures gracefully degrade.
"""
from __future__ import annotations
import subprocess
import sys
from typing import NamedTuple


class ExtractionResult(NamedTuple):
    text:    str
    backend: str
    pages:   int


def _try_pdfminer(path: str) -> ExtractionResult | None:
    try:
        from pdfminer.high_level import extract_text as pm_extract  # type: ignore
        from pdfminer.high_level import extract_pages
        pages = sum(1 for _ in extract_pages(path))
        text  = pm_extract(path) or ""
        if text.strip():
            return ExtractionResult(text=text, backend="pdfminer", pages=pages)
    except Exception:
        pass
    return None


def _try_pypdf(path: str) -> ExtractionResult | None:
    for mod_name in ["pypdf", "PyPDF2"]:
        try:
            mod = __import__(mod_name)
            reader = mod.PdfReader(path)
            pages  = len(reader.pages)
            texts  = [p.extract_text() or "" for p in reader.pages]
            text   = "\n".join(texts)
            if text.strip():
                return ExtractionResult(text=text, backend=mod_name, pages=pages)
        except Exception:
            pass
    return None


def _try_pdfplumber(path: str) -> ExtractionResult | None:
    try:
        import pdfplumber  # type: ignore
        with pdfplumber.open(path) as pdf:
            pages = len(pdf.pages)
            texts = [p.extract_text() or "" for p in pdf.pages]
        text = "\n".join(texts)
        if text.strip():
            return ExtractionResult(text=text, backend="pdfplumber", pages=pages)
    except Exception:
        pass
    return None


def _try_pdftotext(path: str) -> ExtractionResult | None:
    try:
        result = subprocess.run(
            ["pdftotext", path, "-"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            pages = result.stdout.count("\x0c") + 1  # form feed = page break
            return ExtractionResult(text=result.stdout, backend="pdftotext", pages=pages)
    except Exception:
        pass
    return None


def extract_text(pdf_path: str) -> ExtractionResult:
    """Extract text from a PDF file using the best available backend.

    Returns ExtractionResult with text, backend name, and page count.
    Raises RuntimeError if no backend can read the file.
    """
    for fn in [_try_pdfminer, _try_pypdf, _try_pdfplumber, _try_pdftotext]:
        result = fn(pdf_path)
        if result is not None:
            return result
    raise RuntimeError(
        f"Could not extract text from {pdf_path}. "
        "Install at least one of: pdfminer.six, pypdf, pdfplumber, or poppler pdftotext."
    )
