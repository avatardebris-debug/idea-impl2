"""Tests for audiobook2pdf library."""

import io
import os
import struct
import tempfile

import pytest

# Ensure the src directory is importable
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audiobook2pdf import extract_metadata, generate_pdf
from audiobook2pdf.extractor import MetadataExtractError
from audiobook2pdf.pdf_generator import PDFGenerationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_m4b():
    """Create a minimal valid MP4/m4b file in memory.

    Builds a tiny MP4 with:
    - ftyp box (brand: M4B)
    - moov box with minimal atoms for title, artist, narrator
    """
    buf = io.BytesIO()

    # ftyp box
    ftyp_size = 20  # 8 (header) + 12 (data)
    ftyp_data = b'M4B ' + b'isom' + b'\x00\x00\x00\x00'
    buf.write(struct.pack('>I', ftyp_size))
    buf.write(b'ftyp')
    buf.write(ftyp_data)

    # moov box (minimal — just enough to not crash mutagen)
    # We'll write a minimal moov with a minf box
    moov_children = b''

    # mdia box
    mdia = b''
    # hdlr box
    hdlr_size = 36
    hdlr_data = b'\x00' * 8 + b'soun' + b'\x00' * 12 + b'Mutagen Handler\x00'
    mdia += struct.pack('>I', hdlr_size + 8)
    mdia += b'hdlr'
    mdia += hdlr_data

    # minf box
    minf = b''
    # smh box
    smh_size = 20
    smh_data = b'\x00' * 4 + b'smhd' + b'\x00' * 16
    minf += struct.pack('>I', smh_size + 8)
    minf += b'smhd'
    minf += smh_data
    # dinf box
    dinf_size = 24
    dinf_data = b'\x00' * 8 + b'dref' + b'\x00\x00\x00\x01' + b'\x00\x00\x00\x00'
    minf += struct.pack('>I', dinf_size + 8)
    minf += b'dinf'
    minf += dinf_data
    # stbl box (minimal)
    stbl = b''
    stsd_size = 28
    stsd_data = b'\x00\x00\x00\x00' + b'\x00\x00\x00\x01' + b'mp4a' + b'\x00' * 6 + b'\x00\x02\x00\x10' + b'\x00\x00\x00\x00'
    stbl += struct.pack('>I', stsd_size + 8)
    stbl += b'stsd'
    stbl += stsd_data
    minf += struct.pack('>I', len(stbl) + 8)
    minf += b'stbl'
    minf += stbl
    mdia += struct.pack('>I', len(minf) + 8)
    mdia += b'minf'
    mdia += minf
    moov_children += struct.pack('>I', len(mdia) + 8)
    moov_children += b'mdia'
    moov_children += mdia

    # Write moov
    moov_size = len(moov_children) + 8
    buf.write(struct.pack('>I', moov_size))
    buf.write(b'moov')
    buf.write(moov_children)

    buf.seek(0)
    return buf


def _make_m4b_with_metadata():
    """Create an m4b file with title, author, narrator, and cover art."""
    buf = io.BytesIO()

    # ftyp box
    ftyp_size = 20
    ftyp_data = b'M4B ' + b'isom' + b'\x00\x00\x00\x00'
    buf.write(struct.pack('>I', ftyp_size))
    buf.write(b'ftyp')
    buf.write(ftyp_data)

    # moov with metadata atoms
    moov_children = b''

    # title atom (\xa9nam)
    title_str = b'Test Audiobook\x00'
    nam_atom = b'\xa9nam' + b'\x00\x00\x00\x00' + struct.pack('>I', len(title_str) + 8) + title_str
    moov_children += nam_atom

    # artist atom (\xa9ART)
    artist_str = b'Test Author\x00'
    art_atom = b'\xa9ART' + b'\x00\x00\x00\x00' + struct.pack('>I', len(artist_str) + 8) + artist_str
    moov_children += art_atom

    # performer atom (prf)
    perf_str = b'Test Narrator\x00'
    prf_atom = b'prf' + b'\x00\x00\x00\x00' + struct.pack('>I', len(perf_str) + 8) + perf_str
    moov_children += prf_atom

    # cover art (covr)
    cover_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # fake PNG header
    covr_atom = b'covr' + b'\x00\x00\x00\x00' + struct.pack('>I', len(cover_data) + 8) + cover_data
    moov_children += covr_atom

    # mdia/hdlr/minf/stbl (minimal audio track)
    hdlr_size = 36
    hdlr_data = b'\x00' * 8 + b'soun' + b'\x00' * 12 + b'Mutagen Handler\x00'
    mdia = struct.pack('>I', hdlr_size + 8) + b'hdlr' + hdlr_data

    minf = b''
    smh_size = 20
    smh_data = b'\x00' * 4 + b'smhd' + b'\x00' * 16
    minf += struct.pack('>I', smh_size + 8) + b'smhd' + smh_data
    dinf_size = 24
    dinf_data = b'\x00' * 8 + b'dref' + b'\x00\x00\x00\x01' + b'\x00\x00\x00\x00'
    minf += struct.pack('>I', dinf_size + 8) + b'dinf' + dinf_data
    stbl = b''
    stsd_size = 28
    stsd_data = b'\x00\x00\x00\x00' + b'\x00\x00\x00\x01' + b'mp4a' + b'\x00' * 6 + b'\x00\x02\x00\x10' + b'\x00\x00\x00\x00'
    stbl += struct.pack('>I', stsd_size + 8) + b'stsd' + stsd_data
    minf += struct.pack('>I', len(stbl) + 8) + b'stbl' + stbl
    mdia += struct.pack('>I', len(minf) + 8) + b'minf' + minf
    moov_children += struct.pack('>I', len(mdia) + 8) + b'mdia' + mdia

    moov_size = len(moov_children) + 8
    buf.write(struct.pack('>I', moov_size))
    buf.write(b'moov')
    buf.write(moov_children)

    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Tests: extract_metadata
# ---------------------------------------------------------------------------

class TestExtractMetadata:
    """Tests for extract_metadata function."""

    def test_extract_metadata_returns_dict(self, tmp_path):
        """extract_metadata returns a dict with expected keys."""
        m4b_path = str(tmp_path / 'test.m4b')
        with open(m4b_path, 'wb') as f:
            f.write(_make_m4b_with_metadata().getvalue())

        result = extract_metadata(m4b_path)

        assert isinstance(result, dict)
        assert 'title' in result
        assert 'author' in result
        assert 'narrator' in result
        assert 'cover_art_bytes' in result
        assert 'chapters' in result
        assert 'duration' in result

    def test_extract_metadata_title(self, tmp_path):
        """extract_metadata extracts the title correctly."""
        m4b_path = str(tmp_path / 'test.m4b')
        with open(m4b_path, 'wb') as f:
            f.write(_make_m4b_with_metadata().getvalue())

        result = extract_metadata(m4b_path)
        assert result['title'] == 'Test Audiobook'

    def test_extract_metadata_author(self, tmp_path):
        """extract_metadata extracts the author correctly."""
        m4b_path = str(tmp_path / 'test.m4b')
        with open(m4b_path, 'wb') as f:
            f.write(_make_m4b_with_metadata().getvalue())

        result = extract_metadata(m4b_path)
        assert result['author'] == 'Test Author'

    def test_extract_metadata_narrator(self, tmp_path):
        """extract_metadata extracts the narrator correctly."""
        m4b_path = str(tmp_path / 'test.m4b')
        with open(m4b_path, 'wb') as f:
            f.write(_make_m4b_with_metadata().getvalue())

        result = extract_metadata(m4b_path)
        assert result['narrator'] == 'Test Narrator'

    def test_extract_metadata_cover_art(self, tmp_path):
        """extract_metadata extracts cover art bytes."""
        m4b_path = str(tmp_path / 'test.m4b')
        with open(m4b_path, 'wb') as f:
            f.write(_make_m4b_with_metadata().getvalue())

        result = extract_metadata(m4b_path)
        assert result['cover_art_bytes'] is not None
        assert len(result['cover_art_bytes']) > 0

    def test_extract_metadata_no_cover(self, tmp_path):
        """extract_metadata returns None for cover when not present."""
        m4b_path = str(tmp_path / 'test.m4b')
        with open(m4b_path, 'wb') as f:
            f.write(_make_minimal_m4b().getvalue())

        result = extract_metadata(m4b_path)
        assert result['cover_art_bytes'] is None

    def test_extract_metadata_empty_path(self):
        """extract_metadata raises MetadataExtractError for empty path."""
        with pytest.raises(MetadataExtractError, match="file_path cannot be empty"):
            extract_metadata("")

    def test_extract_metadata_nonexistent_file(self):
        """extract_metadata raises MetadataExtractError for nonexistent file."""
        with pytest.raises(MetadataExtractError):
            extract_metadata("/nonexistent/path/to/file.m4b")

    def test_extract_metadata_invalid_file(self, tmp_path):
        """extract_metadata raises MetadataExtractError for invalid file."""
        m4b_path = str(tmp_path / 'invalid.m4b')
        with open(m4b_path, 'wb') as f:
            f.write(b'this is not a valid mp4 file')

        with pytest.raises(MetadataExtractError):
            extract_metadata(m4b_path)


# ---------------------------------------------------------------------------
# Tests: generate_pdf
# ---------------------------------------------------------------------------

class TestGeneratePdf:
    """Tests for generate_pdf function."""

    def _make_metadata(self, **overrides):
        """Create a default metadata dict with optional overrides."""
        base = {
            "title": "Test Audiobook",
            "author": "Test Author",
            "narrator": "Test Narrator",
            "cover_art_bytes": b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
            "chapters": ["Chapter 1", "Chapter 2", "Chapter 3"],
            "duration": 3661,  # 1h 1m 1s
        }
        base.update(overrides)
        return base

    def test_generate_pdf_returns_path(self, tmp_path):
        """generate_pdf returns the output path."""
        output = str(tmp_path / 'output.pdf')
        metadata = self._make_metadata()
        result = generate_pdf(metadata, output)
        assert result == output

    def test_generate_pdf_file_exists(self, tmp_path):
        """generate_pdf creates a file at the output path."""
        output = str(tmp_path / 'output.pdf')
        metadata = self._make_metadata()
        generate_pdf(metadata, output)
        assert os.path.isfile(output)
        assert os.path.getsize(output) > 0

    def test_generate_pdf_with_cover(self, tmp_path):
        """generate_pdf creates PDF with cover art page."""
        output = str(tmp_path / 'with_cover.pdf')
        metadata = self._make_metadata()
        generate_pdf(metadata, output)
        # PDF should have at least 2 pages (cover + metadata)
        with open(output, 'rb') as f:
            content = f.read()
        # Check for PDF structure
        assert content.startswith(b'%PDF')

    def test_generate_pdf_without_cover(self, tmp_path):
        """generate_pdf works without cover art."""
        output = str(tmp_path / 'no_cover.pdf')
        metadata = self._make_metadata(cover_art_bytes=None)
        generate_pdf(metadata, output)
        assert os.path.isfile(output)
        assert os.path.getsize(output) > 0

    def test_generate_pdf_without_chapters(self, tmp_path):
        """generate_pdf works without chapters."""
        output = str(tmp_path / 'no_chapters.pdf')
        metadata = self._make_metadata(chapters=[])
        generate_pdf(metadata, output)
        assert os.path.isfile(output)
        assert os.path.getsize(output) > 0

    def test_generate_pdf_empty_metadata(self):
        """generate_pdf raises PDFGenerationError for empty metadata."""
        with pytest.raises(PDFGenerationError, match="metadata cannot be empty"):
            generate_pdf({}, "/tmp/output.pdf")

    def test_generate_pdf_empty_output_path(self):
        """generate_pdf raises PDFGenerationError for empty output path."""
        metadata = self._make_metadata()
        with pytest.raises(PDFGenerationError, match="output_path cannot be empty"):
            generate_pdf(metadata, "")

    def test_generate_pdf_nested_output_dir(self, tmp_path):
        """generate_pdf creates nested output directories."""
        output = str(tmp_path / 'a' / 'b' / 'c' / 'output.pdf')
        metadata = self._make_metadata()
        result = generate_pdf(metadata, output)
        assert result == output
        assert os.path.isfile(output)

    def test_generate_pdf_metadata_content(self, tmp_path):
        """generate_pdf PDF contains metadata text."""
        output = str(tmp_path / 'content.pdf')
        metadata = self._make_metadata()
        generate_pdf(metadata, output)
        with open(output, 'rb') as f:
            content = f.read()
        assert b'Test Audiobook' in content
        assert b'Test Author' in content
        assert b'Test Narrator' in content


# ---------------------------------------------------------------------------
# Tests: format_duration
# ---------------------------------------------------------------------------

class TestFormatDuration:
    """Tests for format_duration helper."""

    def test_format_duration_zero(self):
        """format_duration handles zero seconds."""
        from audiobook2pdf.pdf_generator import format_duration
        assert format_duration(0) == "00:00:00"

    def test_format_duration_seconds(self):
        """format_duration handles seconds correctly."""
        from audiobook2pdf.pdf_generator import format_duration
        assert format_duration(5) == "00:00:05"

    def test_format_duration_minutes(self):
        """format_duration handles minutes correctly."""
        from audiobook2pdf.pdf_generator import format_duration
        assert format_duration(65) == "00:01:05"

    def test_format_duration_hours(self):
        """format_duration handles hours correctly."""
        from audiobook2pdf.pdf_generator import format_duration
        assert format_duration(3661) == "01:01:01"

    def test_format_duration_large(self):
        """format_duration handles large durations."""
        from audiobook2pdf.pdf_generator import format_duration
        assert format_duration(7261) == "02:01:01"


# ---------------------------------------------------------------------------
# Tests: Public API
# ---------------------------------------------------------------------------

class TestPublicAPI:
    """Tests for the public API surface."""

    def test_import_all(self):
        """All public symbols are importable."""
        from audiobook2pdf import extract_metadata, generate_pdf
        from audiobook2pdf import MetadataExtractError, PDFGenerationError
        assert callable(extract_metadata)
        assert callable(generate_pdf)
        assert issubclass(MetadataExtractError, Exception)
        assert issubclass(PDFGenerationError, Exception)

    def test_version(self):
        """Package has a version."""
        import audiobook2pdf
        assert hasattr(audiobook2pdf, '__version__')
        assert audiobook2pdf.__version__ == "0.1.0"
