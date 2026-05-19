"""Tests for pdf_schema.extractor — multi-backend text extraction."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pdf_schema.extractor import (
    ExtractionResult,
    _try_pdfminer,
    _try_pdfplumber,
    _try_pypdf,
    _try_pdftotext,
    extract_text,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_pdf(tmp_path: Path, name: str = "doc.pdf") -> Path:
    """Write a dummy file that won't actually be read by real backends."""
    p = tmp_path / name
    p.write_bytes(b"%PDF-1.4 fake")
    return p


# ---------------------------------------------------------------------------
# ExtractionResult namedtuple
# ---------------------------------------------------------------------------

class TestExtractionResult:
    def test_fields(self):
        r = ExtractionResult(text="hello", backend="pdfminer", pages=3)
        assert r.text == "hello"
        assert r.backend == "pdfminer"
        assert r.pages == 3

    def test_is_namedtuple(self):
        r = ExtractionResult(text="x", backend="pypdf", pages=1)
        assert r._fields == ("text", "backend", "pages")


# ---------------------------------------------------------------------------
# Individual backend helpers (unit — mock the real libs)
# ---------------------------------------------------------------------------

class TestTryPdfminer:
    def test_returns_none_when_import_fails(self, tmp_path):
        p = _fake_pdf(tmp_path)
        with patch.dict(sys.modules, {"pdfminer": None, "pdfminer.high_level": None}):
            result = _try_pdfminer(str(p))
        assert result is None

    def test_returns_none_on_exception(self, tmp_path):
        p = _fake_pdf(tmp_path)
        mock_mod = MagicMock()
        mock_mod.extract_text.side_effect = Exception("read error")
        with patch.dict(sys.modules, {"pdfminer.high_level": mock_mod}):
            result = _try_pdfminer(str(p))
        assert result is None

    def test_returns_result_on_success(self, tmp_path):
        p = _fake_pdf(tmp_path)
        mock_hl = MagicMock()
        mock_hl.extract_text.return_value = "Invoice total: $500"
        mock_hl.extract_pages.return_value = [object(), object()]  # 2 pages
        with patch.dict(sys.modules, {"pdfminer": MagicMock(), "pdfminer.high_level": mock_hl}):
            with patch("pdf_schema.extractor._try_pdfminer") as mock_fn:
                mock_fn.return_value = ExtractionResult(
                    text="Invoice total: $500", backend="pdfminer", pages=2
                )
                result = mock_fn(str(p))
        assert result is not None
        assert result.backend == "pdfminer"
        assert result.pages == 2


class TestTryPypdf:
    def test_returns_none_when_import_fails(self, tmp_path):
        p = _fake_pdf(tmp_path)
        with patch.dict(sys.modules, {"pypdf": None, "PyPDF2": None}):
            result = _try_pypdf(str(p))
        assert result is None

    def test_returns_none_on_empty_text(self, tmp_path):
        """Should return None when extracted text is blank (scanned/image PDF)."""
        p = _fake_pdf(tmp_path)
        mock_pypdf = MagicMock()
        page = MagicMock()
        page.extract_text.return_value = ""
        mock_pypdf.PdfReader.return_value.pages = [page]
        with patch.dict(sys.modules, {"pypdf": mock_pypdf}):
            result = _try_pypdf(str(p))
        assert result is None


class TestTryPdfplumber:
    def test_returns_none_when_import_fails(self, tmp_path):
        p = _fake_pdf(tmp_path)
        with patch.dict(sys.modules, {"pdfplumber": None}):
            result = _try_pdfplumber(str(p))
        assert result is None


class TestTryPdftotext:
    def test_returns_none_on_missing_binary(self, tmp_path):
        p = _fake_pdf(tmp_path)
        with patch("subprocess.run", side_effect=FileNotFoundError("pdftotext not found")):
            result = _try_pdftotext(str(p))
        assert result is None

    def test_returns_none_on_nonzero_returncode(self, tmp_path):
        p = _fake_pdf(tmp_path)
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        with patch("subprocess.run", return_value=mock_proc):
            result = _try_pdftotext(str(p))
        assert result is None

    def test_returns_result_on_success(self, tmp_path):
        p = _fake_pdf(tmp_path)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Page one content\x0cPage two content"
        with patch("subprocess.run", return_value=mock_proc):
            result = _try_pdftotext(str(p))
        assert result is not None
        assert result.backend == "pdftotext"
        assert result.pages == 2
        assert "Page one" in result.text


# ---------------------------------------------------------------------------
# extract_text — integration (mock all backends)
# ---------------------------------------------------------------------------

class TestExtractText:
    def test_raises_when_all_backends_fail(self, tmp_path):
        p = _fake_pdf(tmp_path)
        with (
            patch("pdf_schema.extractor._try_pdfminer", return_value=None),
            patch("pdf_schema.extractor._try_pypdf", return_value=None),
            patch("pdf_schema.extractor._try_pdfplumber", return_value=None),
            patch("pdf_schema.extractor._try_pdftotext", return_value=None),
        ):
            with pytest.raises(RuntimeError, match="Could not extract"):
                extract_text(str(p))

    def test_uses_first_successful_backend(self, tmp_path):
        p = _fake_pdf(tmp_path)
        expected = ExtractionResult(text="Contract text", backend="pdfminer", pages=5)
        with (
            patch("pdf_schema.extractor._try_pdfminer", return_value=expected),
            patch("pdf_schema.extractor._try_pypdf", return_value=None),
        ):
            result = extract_text(str(p))
        assert result.backend == "pdfminer"
        assert result.text == "Contract text"

    def test_falls_through_to_second_backend(self, tmp_path):
        p = _fake_pdf(tmp_path)
        fallback = ExtractionResult(text="Resume text", backend="pypdf", pages=2)
        with (
            patch("pdf_schema.extractor._try_pdfminer", return_value=None),
            patch("pdf_schema.extractor._try_pypdf", return_value=fallback),
            patch("pdf_schema.extractor._try_pdfplumber", return_value=None),
            patch("pdf_schema.extractor._try_pdftotext", return_value=None),
        ):
            result = extract_text(str(p))
        assert result.backend == "pypdf"
        assert result.pages == 2

    def test_returns_extraction_result_type(self, tmp_path):
        p = _fake_pdf(tmp_path)
        ok = ExtractionResult(text="Some text", backend="pdftotext", pages=1)
        with (
            patch("pdf_schema.extractor._try_pdfminer", return_value=None),
            patch("pdf_schema.extractor._try_pypdf", return_value=None),
            patch("pdf_schema.extractor._try_pdfplumber", return_value=None),
            patch("pdf_schema.extractor._try_pdftotext", return_value=ok),
        ):
            result = extract_text(str(p))
        assert isinstance(result, ExtractionResult)
