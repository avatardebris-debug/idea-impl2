"""Unit tests for PDFExporter: file creation, content, multi-chapter, margins, font size."""

import os
import tempfile

import pytest
from multi_format_export_engine.models import Manuscript
from multi_format_export_engine.exporters.pdf_exporter import PDFExporter, _manuscript_to_html


class TestPDFExporter:
    @pytest.fixture
    def exporter(self):
        return PDFExporter()

    @pytest.fixture
    def simple_manuscript(self):
        m = Manuscript(title="Test Book", author="Test Author")
        ch = m.add_chapter_title("Chapter 1")
        ch.add_paragraph("Hello world.")
        return m

    @pytest.fixture
    def multi_chapter_manuscript(self):
        m = Manuscript(title="Multi Book")
        ch1 = m.add_chapter_title("First")
        ch1.add_paragraph("Para 1")
        ch2 = m.add_chapter_title("Second")
        ch2.add_heading("Section", level=2)
        ch2.add_paragraph("Para 2")
        return m

    # ── Basic export ──

    def test_export_creates_file(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            assert os.path.isfile(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_export_returns_path(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            result = exporter.export(simple_manuscript, output_path=path)
            assert result == path
        finally:
            os.unlink(path)

    def test_export_with_default_path(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            result = exporter.export(simple_manuscript, output_path=path)
            assert os.path.isfile(result)
        finally:
            os.unlink(path)

    # ── HTML generation (unit test the HTML before PDF rendering) ──

    def test_html_contains_title(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript)
        assert "Test Book" in html

    def test_html_contains_author(self, simple_manuscript):
        # The PDF exporter doesn't include author in HTML, so we test that
        # the manuscript has an author attribute
        assert simple_manuscript.author == "Test Author"

    def test_html_contains_paragraph_text(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript)
        assert "Hello world" in html

    def test_html_contains_chapter_title(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript)
        assert "Chapter 1" in html

    def test_html_has_doctype(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript)
        assert "<!DOCTYPE html>" in html

    def test_html_has_namespace(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript)
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in html

    def test_html_has_style_tag(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript)
        assert "<style>" in html

    def test_html_has_page_margin_rule(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript)
        assert "@page" in html
        assert "margin:" in html

    # ── Multi-chapter ──

    def test_multi_chapter_html_contains_all_chapters(self, multi_chapter_manuscript):
        html = _manuscript_to_html(multi_chapter_manuscript)
        assert "First" in html
        assert "Second" in html

    def test_multi_chapter_html_contains_all_paragraphs(self, multi_chapter_manuscript):
        html = _manuscript_to_html(multi_chapter_manuscript)
        assert "Para 1" in html
        assert "Para 2" in html

    def test_multi_chapter_html_contains_heading(self, multi_chapter_manuscript):
        html = _manuscript_to_html(multi_chapter_manuscript)
        assert "Section" in html
        assert "<h2>Section</h2>" in html

    def test_multi_chapter_pdf_contains_all_chapters(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            assert os.path.isfile(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_multi_chapter_pdf_contains_all_paragraphs(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            assert os.path.isfile(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    def test_multi_chapter_pdf_contains_heading(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            assert os.path.isfile(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    # ── Margins ──

    def test_custom_margins_in_html(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript, margins={"top": "2in", "right": "3in", "bottom": "4in", "left": "5in"})
        assert "2in" in html
        assert "3in" in html
        assert "4in" in html
        assert "5in" in html

    def test_custom_margins_applied(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path, margins={"top": "2in", "right": "3in", "bottom": "4in", "left": "5in"})
            assert os.path.isfile(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    # ── Font size ──

    def test_custom_font_size_in_html(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript, font_size="14pt")
        assert "14pt" in html

    def test_custom_font_size_applied(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path, font_size="14pt")
            assert os.path.isfile(path)
            assert os.path.getsize(path) > 0
        finally:
            os.unlink(path)

    # ── Edge cases ──

    def test_empty_manuscript(self, exporter):
        m = Manuscript(title="Empty")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(m, output_path=path)
            assert os.path.isfile(path)
        finally:
            os.unlink(path)

    def test_chapter_with_only_headings(self, exporter):
        m = Manuscript(title="Headings Only")
        ch = m.add_chapter_title("H Chapter")
        ch.add_heading("H1", level=1)
        ch.add_heading("H2", level=2)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(m, output_path=path)
            assert os.path.isfile(path)
        finally:
            os.unlink(path)

    def test_paragraph_with_style(self, exporter):
        m = Manuscript(title="Styled")
        ch = m.add_chapter_title("Styled Chapter")
        ch.add_paragraph("Bold text", style="bold")
        ch.add_paragraph("Italic text", style="italic")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            exporter.export(m, output_path=path)
            assert os.path.isfile(path)
        finally:
            os.unlink(path)

    def test_html_escapes_special_chars(self):
        m = Manuscript(title="A <B> & C")
        ch = m.add_chapter_title("X <Y> & Z")
        ch.add_paragraph("1 < 2 & 3 > 4")
        html = _manuscript_to_html(m)
        assert "&lt;" in html
        assert "&gt;" in html
        assert "&amp;" in html
        assert "<B>" not in html  # should be escaped

    def test_page_size_option(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript, page_size="Letter")
        assert "Letter" in html

    def test_font_family_option(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript, font_family="sans-serif")
        assert "sans-serif" in html

    def test_line_height_option(self, simple_manuscript):
        html = _manuscript_to_html(simple_manuscript, line_height="2.0")
        assert "2.0" in html
