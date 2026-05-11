"""Unit tests for EPUBExporter: ZIP structure, required files, XHTML content, multi-chapter."""

import os
import tempfile
import zipfile

import pytest
from multi_format_export_engine.models import Manuscript, Chapter, Heading, Paragraph
from multi_format_export_engine.exporters.epub_exporter import EPUBExporter


class TestEPUBExporter:
    @pytest.fixture
    def exporter(self):
        return EPUBExporter()

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
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            assert os.path.isfile(path)
        finally:
            os.unlink(path)

    def test_export_returns_path(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            result = exporter.export(simple_manuscript, output_path=path)
            assert result == path
        finally:
            os.unlink(path)

    # ── ZIP structure ──

    def test_output_is_valid_zip(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                assert zf.testzip() is None  # no corruption
        finally:
            os.unlink(path)

    def test_mimetype_is_first_and_stored(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                assert names[0] == "mimetype"
                info = zf.getinfo("mimetype")
                assert info.compress_type == zipfile.ZIP_STORED
                content = zf.read("mimetype").decode()
                assert content == "application/epub+zip"
        finally:
            os.unlink(path)

    # ── Required EPUB3 files ──

    def test_contains_required_files(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = set(zf.namelist())
                assert "mimetype" in names
                assert "META-INF/container.xml" in names
                assert "content.opf" in names
                assert "nav.xhtml" in names
                assert "style.css" in names
        finally:
            os.unlink(path)

    def test_container_xml_valid(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("META-INF/container.xml").decode()
                assert 'full-path="content.opf"' in content
                assert 'media-type="application/oebps-package+xml"' in content
        finally:
            os.unlink(path)

    # ── content.opf ──

    def test_opf_contains_title(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("content.opf").decode()
                assert "Test Book" in content
        finally:
            os.unlink(path)

    def test_opf_contains_author(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("content.opf").decode()
                assert "Test Author" in content
        finally:
            os.unlink(path)

    def test_opf_contains_spine(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("content.opf").decode()
                assert "<spine" in content
                assert "xhtml" in content
        finally:
            os.unlink(path)

    def test_opf_contains_manifest(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("content.opf").decode()
                assert "<manifest" in content
        finally:
            os.unlink(path)

    # ── nav.xhtml ──

    def test_nav_contains_chapter_titles(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("nav.xhtml").decode()
                assert "First" in content
                assert "Second" in content
        finally:
            os.unlink(path)

    def test_nav_has_ol_structure(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("nav.xhtml").decode()
                assert "<ol" in content
                assert "</ol>" in content
        finally:
            os.unlink(path)

    # ── Chapter XHTML files ──

    def test_chapter_xhtml_exists(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                # Chapter files should exist
                chapter_files = [n for n in names if n.endswith(".xhtml") and n != "nav.xhtml"]
                assert len(chapter_files) == 2
        finally:
            os.unlink(path)

    def test_chapter_xhtml_contains_paragraph_text(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                chapter_files = [n for n in names if n.endswith(".xhtml") and n != "nav.xhtml"]
                assert len(chapter_files) == 1
                content = zf.read(chapter_files[0]).decode()
                assert "Hello world." in content
        finally:
            os.unlink(path)

    def test_chapter_xhtml_contains_heading(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                chapter_files = [n for n in names if n.endswith(".xhtml") and n != "nav.xhtml"]
                for cf in chapter_files:
                    content = zf.read(cf).decode()
                    if "Second" in cf:
                        assert "Section" in content
        finally:
            os.unlink(path)

    # ── style.css ──

    def test_css_exists(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                assert "style.css" in zf.namelist()
        finally:
            os.unlink(path)

    def test_css_contains_paragraph_styles(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("style.css").decode()
                assert "p {" in content
        finally:
            os.unlink(path)

    def test_css_contains_heading_styles(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("style.css").decode()
                assert "h1 {" in content
        finally:
            os.unlink(path)

    # ── XHTML structure ──

    def test_xhtml_has_namespace(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                chapter_files = [n for n in names if n.endswith(".xhtml") and n != "nav.xhtml"]
                content = zf.read(chapter_files[0]).decode()
                assert 'xmlns="http://www.w3.org/1999/xhtml"' in content
        finally:
            os.unlink(path)

    def test_xhtml_has_html5_doctype(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                chapter_files = [n for n in names if n.endswith(".xhtml") and n != "nav.xhtml"]
                content = zf.read(chapter_files[0]).decode()
                assert "<!DOCTYPE html" in content or "xhtml11" in content.lower()
        finally:
            os.unlink(path)

    def test_xhtml_has_body(self, exporter, simple_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(simple_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                chapter_files = [n for n in names if n.endswith(".xhtml") and n != "nav.xhtml"]
                content = zf.read(chapter_files[0]).decode()
                assert "<body>" in content
        finally:
            os.unlink(path)

    # ── Multi-chapter ──

    def test_multi_chapter_opf_spine_order(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("content.opf").decode()
                # Both chapters should appear in spine via idref
                assert "chapter_1" in content
                assert "chapter_2" in content
                # Verify order: chapter_1 before chapter_2
                assert content.find("chapter_1") < content.find("chapter_2")
        finally:
            os.unlink(path)

    def test_multi_chapter_nav_order(self, exporter, multi_chapter_manuscript):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(multi_chapter_manuscript, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                content = zf.read("nav.xhtml").decode()
                # First should appear before Second in the TOC
                first_pos = content.find("First")
                second_pos = content.find("Second")
                assert first_pos < second_pos
        finally:
            os.unlink(path)

    # ── Edge cases ──

    def test_empty_manuscript(self, exporter):
        m = Manuscript(title="Empty")
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
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
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(m, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                chapter_files = [n for n in names if n.endswith(".xhtml") and n != "nav.xhtml"]
                assert len(chapter_files) == 1
        finally:
            os.unlink(path)

    def test_paragraph_with_style(self, exporter):
        m = Manuscript(title="Styled")
        ch = m.add_chapter_title("Styled Chapter")
        ch.add_paragraph("Bold text", style="bold")
        ch.add_paragraph("Italic text", style="italic")
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            path = f.name
        try:
            exporter.export(m, output_path=path)
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                chapter_files = [n for n in names if n.endswith(".xhtml") and n != "nav.xhtml"]
                content = zf.read(chapter_files[0]).decode()
                assert "Bold text" in content
                assert "Italic text" in content
        finally:
            os.unlink(path)
