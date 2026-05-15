"""Tests for the formatter module."""

import os
import pytest
from datetime import datetime
from email_tool.models import Email
from email_tool.formatter import Formatter, BatchFormatter


class TestFormatter:
    """Test cases for Formatter class."""
    
    @pytest.fixture
    def sample_email(self):
        """Create a sample email for testing."""
        return Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com", "other@test.com"],
            subject="Test Subject: Hello World!",
            date=datetime(2024, 3, 15, 10, 30, 0),
            body_plain="This is a test email body.\n\nWith multiple lines.",
            body_html="<html><body><p>This is HTML body.</p></body></html>",
            attachments=["file1.pdf", "file2.docx"],
            raw_headers={"Message-ID": "<12345@example.com>", "X-Priority": "1"}
        )
    
    def test_to_eml_basic(self, sample_email):
        """Test basic EML export."""
        formatter = Formatter(sample_email)
        eml = formatter.to_eml()
        
        assert "From: sender@example.com" in eml
        assert "To: recipient@test.com, other@test.com" in eml
        assert "Subject: Test Subject: Hello World!" in eml
        assert "This is a test email body." in eml
    
    def test_to_eml_with_date(self, sample_email):
        """Test EML export includes date."""
        formatter = Formatter(sample_email)
        eml = formatter.to_eml()
        
        assert "2024" in eml
        assert "Mar" in eml
    
    def test_to_eml_empty_body(self):
        """Test EML export with empty body."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain=None,
            body_html=None,
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        eml = formatter.to_eml()
        
        assert "From: sender@example.com" in eml
        assert "Test" in eml
    
    def test_to_eml_attachments(self, sample_email):
        """Test EML export includes attachments."""
        formatter = Formatter(sample_email)
        eml = formatter.to_eml()
        
        assert "Attachments:" in eml
        assert "file1.pdf" in eml
        assert "file2.docx" in eml
    
    def test_to_markdown_basic(self, sample_email):
        """Test basic markdown export."""
        formatter = Formatter(sample_email)
        md = formatter.to_markdown()
        
        assert "# Email: Test Subject: Hello World!" in md
        assert "## Metadata" in md
        assert "## Body" in md
        assert "## Attachments" in md
    
    def test_to_markdown_from_field(self, sample_email):
        """Test markdown includes from field."""
        formatter = Formatter(sample_email)
        md = formatter.to_markdown()
        
        assert "**From:** sender@example.com" in md
    
    def test_to_markdown_to_field(self, sample_email):
        """Test markdown includes to field."""
        formatter = Formatter(sample_email)
        md = formatter.to_markdown()
        
        assert "**To:** recipient@test.com, other@test.com" in md
    
    def test_to_markdown_date_field(self, sample_email):
        """Test markdown includes date field."""
        formatter = Formatter(sample_email)
        md = formatter.to_markdown()
        
        assert "2024-03-15" in md
    
    def test_to_markdown_no_attachments(self):
        """Test markdown without attachments section."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain="Body content",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        md = formatter.to_markdown()
        
        assert "## Attachments" not in md
    
    def test_to_markdown_no_body(self):
        """Test markdown with no body content."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain=None,
            body_html=None,
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        md = formatter.to_markdown()
        
        assert "*No body content*" in md
    
    def test_to_markdown_raw_headers(self, sample_email):
        """Test markdown includes raw headers."""
        formatter = Formatter(sample_email)
        md = formatter.to_markdown()
        
        assert "## Raw Headers" in md
        assert "`Message-ID`" in md
        assert "`X-Priority`" in md
    
    def test_to_markdown_html_body(self):
        """Test markdown with HTML body."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain=None,
            body_html="<html><body><p>HTML content</p></body></html>",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        md = formatter.to_markdown()
        
        assert "HTML content" in md
        assert "<html>" not in md
    
    def test_to_markdown_no_subject(self):
        """Test markdown with no subject."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject=None,
            date=datetime(2024, 3, 15),
            body_plain="Body",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        md = formatter.to_markdown()
        
        assert "# Email: No Subject" in md
    
    def test_strip_html(self):
        """Test HTML stripping."""
        formatter = Formatter(Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain=None,
            body_html="<p>Test <b>bold</b> text</p>",
            attachments=[],
            raw_headers={}
        ))
        
        text = formatter._strip_html("<p>Test <b>bold</b> text</p>")
        
        assert "<p>" not in text
        assert "<b>" not in text
        assert "Test bold text" in text
    
    def test_strip_html_entities(self):
        """Test HTML entity conversion."""
        formatter = Formatter(Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain=None,
            body_html="Test &nbsp; &amp; &lt; &gt;",
            attachments=[],
            raw_headers={}
        ))
        
        text = formatter._strip_html("Test &nbsp; &amp; &lt; &gt;")
        
        # html.unescape converts &nbsp; to non-breaking space (\xa0), &amp; to &, etc.
        assert "&" in text
        assert "<" in text
        assert ">" in text
    
    def test_format_eml(self, sample_email):
        """Test format method with EML."""
        formatter = Formatter(sample_email)
        result = formatter.format("eml")
        
        assert "From: sender@example.com" in result
    
    def test_format_markdown(self, sample_email):
        """Test format method with Markdown."""
        formatter = Formatter(sample_email)
        result = formatter.format("md")
        
        assert "# Email: Test Subject: Hello World!" in result
    
    def test_format_pdf_without_path(self, sample_email):
        """Test format method with PDF without path."""
        formatter = Formatter(sample_email)
        
        with pytest.raises(ValueError, match="output_path required"):
            formatter.format("pdf")
    
    def test_format_unknown_format(self, sample_email):
        """Test format method with unknown format."""
        formatter = Formatter(sample_email)
        
        with pytest.raises(ValueError, match="Unknown output format"):
            formatter.format("unknown")


class TestBatchFormatter:
    """Test cases for BatchFormatter class."""
    
    @pytest.fixture
    def sample_emails(self):
        """Create sample emails for testing."""
        return [
            Email(
                from_addr="sender1@example.com",
                to_addrs=["recipient@test.com"],
                subject="Email 1",
                date=datetime(2024, 3, 15),
                body_plain="Body 1",
                attachments=[],
                raw_headers={}
            ),
            Email(
                from_addr="sender2@example.com",
                to_addrs=["recipient@test.com"],
                subject="Email 2",
                date=datetime(2024, 3, 16),
                body_plain="Body 2",
                attachments=["file.pdf"],
                raw_headers={}
            ),
        ]
    
    def test_format_all_eml(self, sample_emails, tmp_path):
        """Test batch formatting to EML."""
        batch_formatter = BatchFormatter(sample_emails)
        
        paths = batch_formatter.format_all(
            output_format="eml",
            base_path=str(tmp_path)
        )
        
        assert len(paths) == 2
        for path in paths:
            assert os.path.exists(path)
            assert path.endswith(".eml")
    
    def test_format_all_markdown(self, sample_emails, tmp_path):
        """Test batch formatting to Markdown."""
        batch_formatter = BatchFormatter(sample_emails)
        
        paths = batch_formatter.format_all(
            output_format="md",
            base_path=str(tmp_path)
        )
        
        assert len(paths) == 2
        for path in paths:
            assert os.path.exists(path)
            assert path.endswith(".md")
    
    def test_format_all_pdf(self, sample_emails, tmp_path):
        """Test batch formatting to PDF."""
        pytest.importorskip("fpdf")
        batch_formatter = BatchFormatter(sample_emails)
        
        paths = batch_formatter.format_all(
            output_format="pdf",
            base_path=str(tmp_path)
        )
        
        assert len(paths) == 2
        for path in paths:
            assert os.path.exists(path)
            assert path.endswith(".pdf")
    
    def test_format_all_custom_filename(self, sample_emails, tmp_path):
        """Test batch formatting with custom filename template."""
        batch_formatter = BatchFormatter(sample_emails)
        
        paths = batch_formatter.format_all(
            output_format="eml",
            base_path=str(tmp_path),
            filename_template="{{from_domain}}_{{subject_sanitized}}.{ext}"
        )
        
        assert len(paths) == 2
        # Check that filenames contain domain
        for path in paths:
            assert "example.com" in path


class TestFormatterEdgeCases:
    """Edge case tests for Formatter."""
    
    def test_email_with_special_chars_in_subject(self):
        """Test formatting with special characters in subject."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject='Test<>:"/\\|?*?',
            date=datetime(2024, 3, 15),
            body_plain="Body",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        md = formatter.to_markdown()
        
        assert "Test<>:" in md  # Markdown preserves special chars in title
    
    def test_email_with_unicode_body(self):
        """Test formatting with unicode characters."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain="你好世界 世界你好",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        md = formatter.to_markdown()
        
        assert "你好" in md
        assert "世界" in md
    
    def test_email_with_empty_from(self):
        """Test formatting with empty from address."""
        email = Email(
            from_addr="",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain="Body",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        eml = formatter.to_eml()
        
        assert "From: Unknown" in eml
    
    def test_email_with_empty_to(self):
        """Test formatting with empty to addresses."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=[],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain="Body",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        eml = formatter.to_eml()
        
        assert "To:" not in eml or "To: " not in eml
    
    def test_email_with_no_date(self):
        """Test formatting with no date."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=None,
            body_plain="Body",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        eml = formatter.to_eml()
        
        assert "Date:" not in eml
    
    def test_pdf_creation_failure(self):
        """Test PDF creation when fpdf is not available."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain="Body",
            attachments=[],
            raw_headers={}
        )
        
        formatter = Formatter(email)
        result = formatter.to_pdf("/tmp/test.pdf")
        
        # Should return False if fpdf is not available
        try:
            import fpdf
            assert result is True
        except ImportError:
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
