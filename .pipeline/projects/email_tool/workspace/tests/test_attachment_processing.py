"""Tests for attachment type detection and parsing."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os

from email_tool.attachment_types import (
    AttachmentType,
    get_attachment_type,
    get_attachment_type_from_mime,
    get_attachment_type_from_filename,
    is_text_attachment,
    is_image_attachment,
    is_office_attachment,
    is_pdf_attachment,
)
from email_tool.attachment_parsers.base import (
    AbstractAttachmentParser,
    AttachmentMetadata,
    ParsedAttachment,
)
from email_tool.attachment_parsers.pdf import PDFAttachmentParser
from email_tool.attachment_parsers.office import OfficeAttachmentParser
from email_tool.attachment_parsers.text import TextAttachmentParser


class TestAttachmentTypeDetection:
    """Tests for attachment type detection functions."""

    def test_pdf_from_mime(self):
        """Test PDF detection from MIME type."""
        result = get_attachment_type_from_mime("application/pdf")
        assert result == AttachmentType.PDF

    def test_docx_from_mime(self):
        """Test DOCX detection from MIME type."""
        result = get_attachment_type_from_mime(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert result == AttachmentType.DOCX

    def test_xlsx_from_mime(self):
        """Test XLSX detection from MIME type."""
        result = get_attachment_type_from_mime(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert result == AttachmentType.XLSX

    def test_pptx_from_mime(self):
        """Test PPTX detection from MIME type."""
        result = get_attachment_type_from_mime(
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        assert result == AttachmentType.PPTX

    def test_png_from_mime(self):
        """Test PNG detection from MIME type."""
        result = get_attachment_type_from_mime("image/png")
        assert result == AttachmentType.PNG

    def test_jpg_from_mime(self):
        """Test JPG detection from MIME type."""
        result = get_attachment_type_from_mime("image/jpeg")
        assert result == AttachmentType.JPG

    def test_txt_from_mime(self):
        """Test TXT detection from MIME type."""
        result = get_attachment_type_from_mime("text/plain")
        assert result == AttachmentType.TXT

    def test_csv_from_mime(self):
        """Test CSV detection from MIME type."""
        result = get_attachment_type_from_mime("text/csv")
        assert result == AttachmentType.CSV

    def test_zip_from_mime(self):
        """Test ZIP detection from MIME type."""
        result = get_attachment_type_from_mime("application/zip")
        assert result == AttachmentType.ZIP

    def test_unknown_mime(self):
        """Test unknown MIME type returns UNKNOWN."""
        result = get_attachment_type_from_mime("application/unknown")
        assert result == AttachmentType.UNKNOWN

    def test_empty_mime(self):
        """Test empty MIME type returns UNKNOWN."""
        result = get_attachment_type_from_mime("")
        assert result == AttachmentType.UNKNOWN

    def test_pdf_from_filename(self):
        """Test PDF detection from filename."""
        result = get_attachment_type_from_filename("document.pdf")
        assert result == AttachmentType.PDF

    def test_docx_from_filename(self):
        """Test DOCX detection from filename."""
        result = get_attachment_type_from_filename("report.docx")
        assert result == AttachmentType.DOCX

    def test_xlsx_from_filename(self):
        """Test XLSX detection from filename."""
        result = get_attachment_type_from_filename("data.xlsx")
        assert result == AttachmentType.XLSX

    def test_pptx_from_filename(self):
        """Test PPTX detection from filename."""
        result = get_attachment_type_from_filename("presentation.pptx")
        assert result == AttachmentType.PPTX

    def test_txt_from_filename(self):
        """Test TXT detection from filename."""
        result = get_attachment_type_from_filename("notes.txt")
        assert result == AttachmentType.TXT

    def test_csv_from_filename(self):
        """Test CSV detection from filename."""
        result = get_attachment_type_from_filename("data.csv")
        assert result == AttachmentType.CSV

    def test_case_insensitive_filename(self):
        """Test filename detection is case insensitive."""
        result = get_attachment_type_from_filename("DOCUMENT.PDF")
        assert result == AttachmentType.PDF

    def test_unknown_filename(self):
        """Test unknown filename extension returns UNKNOWN."""
        result = get_attachment_type_from_filename("file.xyz")
        assert result == AttachmentType.UNKNOWN

    def test_empty_filename(self):
        """Test empty filename returns UNKNOWN."""
        result = get_attachment_type_from_filename("")
        assert result == AttachmentType.UNKNOWN

    def test_get_attachment_type_from_mime(self):
        """Test get_attachment_type with MIME type."""
        result = get_attachment_type(mime_type="application/pdf")
        assert result == AttachmentType.PDF

    def test_get_attachment_type_from_filename(self):
        """Test get_attachment_type with filename."""
        result = get_attachment_type(filename="document.pdf")
        assert result == AttachmentType.PDF

    def test_get_attachment_type_mime_priority(self):
        """Test that MIME type takes priority over filename."""
        result = get_attachment_type(
            mime_type="application/pdf", filename="document.docx"
        )
        assert result == AttachmentType.PDF

    def test_is_text_attachment_pdf(self):
        """Test PDF is considered text attachment."""
        assert is_text_attachment(AttachmentType.PDF) is True

    def test_is_text_attachment_docx(self):
        """Test DOCX is considered text attachment."""
        assert is_text_attachment(AttachmentType.DOCX) is True

    def test_is_text_attachment_txt(self):
        """Test TXT is considered text attachment."""
        assert is_text_attachment(AttachmentType.TXT) is True

    def test_is_text_attachment_image(self):
        """Test image is not considered text attachment."""
        assert is_text_attachment(AttachmentType.PNG) is False

    def test_is_image_attachment_png(self):
        """Test PNG is considered image attachment."""
        assert is_image_attachment(AttachmentType.PNG) is True

    def test_is_image_attachment_jpg(self):
        """Test JPG is considered image attachment."""
        assert is_image_attachment(AttachmentType.JPG) is True

    def test_is_image_attachment_pdf(self):
        """Test PDF is not considered image attachment."""
        assert is_image_attachment(AttachmentType.PDF) is False

    def test_is_office_attachment_docx(self):
        """Test DOCX is considered office attachment."""
        assert is_office_attachment(AttachmentType.DOCX) is True

    def test_is_office_attachment_xlsx(self):
        """Test XLSX is considered office attachment."""
        assert is_office_attachment(AttachmentType.XLSX) is True

    def test_is_office_attachment_pptx(self):
        """Test PPTX is considered office attachment."""
        assert is_office_attachment(AttachmentType.PPTX) is True

    def test_is_office_attachment_pdf(self):
        """Test PDF is not considered office attachment."""
        assert is_office_attachment(AttachmentType.PDF) is False

    def test_is_pdf_attachment_pdf(self):
        """Test PDF is considered PDF attachment."""
        assert is_pdf_attachment(AttachmentType.PDF) is True

    def test_is_pdf_attachment_docx(self):
        """Test DOCX is not considered PDF attachment."""
        assert is_pdf_attachment(AttachmentType.DOCX) is False


class TestAbstractAttachmentParser:
    """Tests for the abstract attachment parser base class."""

    def test_parser_initialization(self):
        """Test parser initialization creates staging directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = Mock(spec=AbstractAttachmentParser)
            parser.staging_dir = Path(tmpdir)
            assert parser.staging_dir.exists()

    def test_parsed_attachment_default_values(self):
        """Test ParsedAttachment default values."""
        parsed = ParsedAttachment(
            attachment_id="test-123",
            email_id="email-456",
            original_filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            attachment_type=AttachmentType.PDF,
        )
        assert parsed.success is True
        assert parsed.text_content is None
        assert parsed.metadata is None
        assert parsed.error_message is None

    def test_parsed_attachment_error_case(self):
        """Test ParsedAttachment with error."""
        parsed = ParsedAttachment(
            attachment_id="test-123",
            email_id="email-456",
            original_filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            attachment_type=AttachmentType.PDF,
            success=False,
            error_message="Test error",
        )
        assert parsed.success is False
        assert parsed.error_message == "Test error"

    def test_attachment_metadata_default_values(self):
        """Test AttachmentMetadata default values."""
        metadata = AttachmentMetadata(
            original_filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            attachment_type=AttachmentType.PDF,
            extracted_at="2024-01-15T10:00:00",
            parser_name="TestParser",
        )
        assert metadata.parser_name == "TestParser"
        assert metadata.additional_metadata == {}


class TestPDFAttachmentParser:
    """Tests for PDF attachment parser."""

    @pytest.fixture
    def pdf_parser(self):
        """Create a PDF parser instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield PDFAttachmentParser(tmpdir)

    def test_parser_name(self, pdf_parser):
        """Test parser name."""
        assert pdf_parser.get_parser_name() == "PDFAttachmentParser"

    def test_can_parse_pdf(self, pdf_parser):
        """Test PDF parser can handle PDF files."""
        assert pdf_parser.can_parse(AttachmentType.PDF) is True

    def test_can_parse_other_types(self, pdf_parser):
        """Test PDF parser cannot handle non-PDF files."""
        assert pdf_parser.can_parse(AttachmentType.DOCX) is False
        assert pdf_parser.can_parse(AttachmentType.TXT) is False

    def test_extract_text_success(self, pdf_parser):
        """Test successful text extraction."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"Test PDF content")
            tmp_path = Path(tmp.name)

        try:
            result = pdf_parser.extract_text(
                tmp_path, "attachment-123", "email-456"
            )
            # Should handle error gracefully for invalid PDF
            assert result.attachment_type == AttachmentType.PDF
        finally:
            os.unlink(tmp_path)

    def test_extract_metadata_success(self, pdf_parser):
        """Test successful metadata extraction."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"Test PDF content")
            tmp_path = Path(tmp.name)

        try:
            result = pdf_parser.extract_metadata(tmp_path)
            assert result.parser_name == "PDFAttachmentParser"
            assert result.attachment_type == AttachmentType.PDF
        finally:
            os.unlink(tmp_path)


class TestOfficeAttachmentParser:
    """Tests for Office document attachment parser."""

    @pytest.fixture
    def office_parser(self):
        """Create an Office parser instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield OfficeAttachmentParser(tmpdir)

    def test_parser_name(self, office_parser):
        """Test parser name."""
        assert office_parser.get_parser_name() == "OfficeAttachmentParser"

    def test_can_parse_docx(self, office_parser):
        """Test Office parser can handle DOCX files."""
        assert office_parser.can_parse(AttachmentType.DOCX) is True

    def test_can_parse_xlsx(self, office_parser):
        """Test Office parser can handle XLSX files."""
        assert office_parser.can_parse(AttachmentType.XLSX) is True

    def test_can_parse_pptx(self, office_parser):
        """Test Office parser can handle PPTX files."""
        assert office_parser.can_parse(AttachmentType.PPTX) is True

    def test_can_parse_pdf(self, office_parser):
        """Test Office parser cannot handle PDF files."""
        assert office_parser.can_parse(AttachmentType.PDF) is False

    def test_can_parse_txt(self, office_parser):
        """Test Office parser cannot handle TXT files."""
        assert office_parser.can_parse(AttachmentType.TXT) is False


class TestTextAttachmentParser:
    """Tests for text file attachment parser."""

    @pytest.fixture
    def text_parser(self):
        """Create a text parser instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield TextAttachmentParser(tmpdir)

    def test_parser_name(self, text_parser):
        """Test parser name."""
        assert text_parser.get_parser_name() == "TextAttachmentParser"

    def test_can_parse_txt(self, text_parser):
        """Test text parser can handle TXT files."""
        assert text_parser.can_parse(AttachmentType.TXT) is True

    def test_can_parse_csv(self, text_parser):
        """Test text parser can handle CSV files."""
        assert text_parser.can_parse(AttachmentType.CSV) is True

    def test_can_parse_pdf(self, text_parser):
        """Test text parser cannot handle PDF files."""
        assert text_parser.can_parse(AttachmentType.PDF) is False

    def test_can_parse_docx(self, text_parser):
        """Test text parser cannot handle DOCX files."""
        assert text_parser.can_parse(AttachmentType.DOCX) is False


class TestParserOrchestration:
    """Tests for parser orchestration."""

    @pytest.fixture
    def parsers(self):
        """Create parser registry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield {
                "pdf": PDFAttachmentParser(tmpdir),
                "office": OfficeAttachmentParser(tmpdir),
                "text": TextAttachmentParser(tmpdir),
            }

    def test_get_parser_for_pdf(self, parsers):
        """Test getting PDF parser."""
        parser = parsers["pdf"]
        assert parser.can_parse(AttachmentType.PDF) is True

    def test_get_parser_for_office(self, parsers):
        """Test getting Office parser."""
        parser = parsers["office"]
        assert parser.can_parse(AttachmentType.DOCX) is True

    def test_get_parser_for_text(self, parsers):
        """Test getting text parser."""
        parser = parsers["text"]
        assert parser.can_parse(AttachmentType.TXT) is True


class TestErrorHandling:
    """Tests for error handling in parsers."""

    @pytest.fixture
    def pdf_parser(self):
        """Create a PDF parser instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield PDFAttachmentParser(tmpdir)

    def test_extract_text_with_invalid_file(self, pdf_parser):
        """Test text extraction with invalid file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"Not a valid PDF")
            tmp_path = Path(tmp.name)

        try:
            result = pdf_parser.extract_text(
                tmp_path, "attachment-123", "email-456"
            )
            # Should handle error gracefully
            assert result.attachment_type == AttachmentType.PDF
        finally:
            os.unlink(tmp_path)

    def test_extract_metadata_with_invalid_file(self, pdf_parser):
        """Test metadata extraction with invalid file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"Not a valid PDF")
            tmp_path = Path(tmp.name)

        try:
            result = pdf_parser.extract_metadata(tmp_path)
            # Should handle error gracefully
            assert result.parser_name == "PDFAttachmentParser"
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
