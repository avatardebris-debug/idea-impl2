"""Tests for the Formatter module."""

import pytest
import os
import tempfile
from datetime import datetime
from email_tool.formatter import Formatter, BatchFormatter
from email_tool.models import Email


class TestFormatterToEML:
    """Tests for Formatter.to_eml() method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            body_plain="This is the plain text body.",
            date=datetime(2024, 1, 15, 10, 30, 0)
        )
        self.formatter = Formatter(self.email)
    
    def test_to_eml_basic(self):
        """Test basic to_eml conversion."""
        result = self.formatter.to_eml()
        
        assert "From: sender@example.com" in result
        assert "To: recipient@example.com" in result
        assert "Subject: Test Subject" in result
        assert "This is the plain text body." in result
    
    def test_to_eml_with_html(self):
        """Test to_eml with HTML body."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="HTML Email",
            body_html="<p>HTML body</p>"
        )
        formatter = Formatter(email)
        
        result = formatter.to_eml()
        
        assert "<p>HTML body</p>" in result
        assert "text/html" in result
    
    def test_to_eml_with_attachments(self):
        """Test to_eml with attachments."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Email with Attachment",
            attachments=["document.pdf", "image.png"]
        )
        formatter = Formatter(email)
        
        result = formatter.to_eml()
        
        assert "document.pdf" in result
        assert "image.png" in result
    
    def test_to_eml_with_custom_headers(self):
        """Test to_eml with custom headers."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Custom Headers",
            raw_headers={"X-Priority": "1", "X-Mailer": "TestMailer"}
        )
        formatter = Formatter(email)
        
        result = formatter.to_eml()
        
        assert "X-Priority: 1" in result
        assert "X-Mailer: TestMailer" in result


class TestFormatterToMarkdown:
    """Tests for Formatter.to_markdown() method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            body_plain="This is the plain text body.",
            date=datetime(2024, 1, 15, 10, 30, 0)
        )
        self.formatter = Formatter(self.email)
    
    def test_to_markdown_basic(self):
        """Test basic markdown conversion."""
        result = self.formatter.to_markdown()
        
        assert "# Email: Test Subject" in result
        assert "## Metadata" in result
        assert "## Body" in result
        assert "**From:** sender@example.com" in result
        assert "This is the plain text body." in result
    
    def test_to_markdown_with_html(self):
        """Test markdown conversion with HTML body."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="HTML Email",
            body_html="<p>HTML body</p>"
        )
        formatter = Formatter(email)
        
        result = formatter.to_markdown()
        
        assert "HTML body" in result
        assert "<p>" not in result  # HTML tags should be stripped
    
    def test_to_markdown_with_attachments(self):
        """Test markdown conversion with attachments."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Email with Attachment",
            attachments=["document.pdf"]
        )
        formatter = Formatter(email)
        
        result = formatter.to_markdown()
        
        assert "## Attachments" in result
        assert "- document.pdf" in result
    
    def test_to_markdown_with_raw_headers(self):
        """Test markdown conversion with raw headers."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Custom Headers",
            raw_headers={"X-Priority": "1"}
        )
        formatter = Formatter(email)
        
        result = formatter.to_markdown()
        
        assert "## Raw Headers" in result
        assert "X-Priority" in result


class TestFormatterToPDF:
    """Tests for Formatter.to_pdf() method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            body_plain="This is the plain text body.",
            date=datetime(2024, 1, 15, 10, 30, 0)
        )
    
    def test_to_pdf_basic(self):
        """Test basic PDF conversion."""
        formatter = Formatter(self.email)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test.pdf")
            result = formatter.to_pdf(output_path)
            
            assert result is True
            assert os.path.exists(output_path)
    
    def test_to_pdf_with_custom_title(self):
        """Test PDF conversion with custom title."""
        formatter = Formatter(self.email)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test.pdf")
            result = formatter.to_pdf(output_path, title="Custom Title")
            
            assert result is True
            assert os.path.exists(output_path)
    
    def test_to_pdf_without_fpdf(self):
        """Test PDF conversion when fpdf is not installed."""
        # Temporarily hide fpdf
        import sys
        original_fpdc = sys.modules.get('fpdf')
        sys.modules['fpdf'] = None
        
        try:
            formatter = Formatter(self.email)
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "test.pdf")
                result = formatter.to_pdf(output_path)
                
                assert result is False
        finally:
            # Restore fpdf
            if original_fpdc:
                sys.modules['fpdf'] = original_fpdc
            elif 'fpdf' in sys.modules:
                del sys.modules['fpdf']
    
    def test_to_pdf_creates_directory(self):
        """Test that PDF conversion creates directory if needed."""
        formatter = Formatter(self.email)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            subdir = os.path.join(temp_dir, "subdir", "nested")
            output_path = os.path.join(subdir, "test.pdf")
            result = formatter.to_pdf(output_path)
            
            assert result is True
            assert os.path.exists(output_path)


class TestFormatterFormat:
    """Tests for Formatter.format() method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            body_plain="Test body"
        )
    
    def test_format_eml(self):
        """Test format method with EML output."""
        formatter = Formatter(self.email)
        
        result = formatter.format("eml")
        
        assert "From: sender@example.com" in result
        assert isinstance(result, str)
    
    def test_format_markdown(self):
        """Test format method with Markdown output."""
        formatter = Formatter(self.email)
        
        result = formatter.format("md")
        
        assert "# Email: Test Subject" in result
        assert isinstance(result, str)
    
    def test_format_pdf_requires_path(self):
        """Test that PDF format requires output path."""
        formatter = Formatter(self.email)
        
        with pytest.raises(ValueError):
            formatter.format("pdf")
    
    def test_format_invalid_format(self):
        """Test format method with invalid format."""
        formatter = Formatter(self.email)
        
        with pytest.raises(ValueError):
            formatter.format("invalid")


class TestBatchFormatter:
    """Tests for BatchFormatter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.emails = [
            Email(
                from_addr="sender1@example.com",
                to_addrs=["recipient@example.com"],
                subject="Email 1",
                body_plain="Body 1"
            ),
            Email(
                from_addr="sender2@example.com",
                to_addrs=["recipient@example.com"],
                subject="Email 2",
                body_plain="Body 2"
            )
        ]
    
    def test_format_all_eml(self):
        """Test batch formatting to EML."""
        batch_formatter = BatchFormatter(self.emails)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = batch_formatter.format_all(
                output_format="eml",
                base_path=temp_dir
            )
            
            assert len(paths) == 2
            for path in paths:
                assert os.path.exists(path)
                assert path.endswith(".eml")
    
    def test_format_all_markdown(self):
        """Test batch formatting to Markdown."""
        batch_formatter = BatchFormatter(self.emails)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = batch_formatter.format_all(
                output_format="md",
                base_path=temp_dir
            )
            
            assert len(paths) == 2
            for path in paths:
                assert os.path.exists(path)
                assert path.endswith(".md")
    
    def test_format_all_pdf(self):
        """Test batch formatting to PDF."""
        batch_formatter = BatchFormatter(self.emails)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = batch_formatter.format_all(
                output_format="pdf",
                base_path=temp_dir
            )
            
            assert len(paths) == 2
            for path in paths:
                assert os.path.exists(path)
                assert path.endswith(".pdf")
    
    def test_format_all_with_filename_template(self):
        """Test batch formatting with custom filename template."""
        batch_formatter = BatchFormatter(self.emails)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = batch_formatter.format_all(
                output_format="md",
                base_path=temp_dir,
                filename_template="{{subject_sanitized}}.md"
            )
            
            assert len(paths) == 2
            # Files should be named after subjects
            filenames = [os.path.basename(p) for p in paths]
            assert "Email_1.md" in filenames
            assert "Email_2.md" in filenames
    
    def test_format_all_with_custom_extension(self):
        """Test batch formatting with custom file extension."""
        batch_formatter = BatchFormatter(self.emails)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = batch_formatter.format_all(
                output_format="md",
                base_path=temp_dir,
                file_extension="txt"
            )
            
            assert len(paths) == 2
            for path in paths:
                assert path.endswith(".txt")
    
    def test_format_all_invalid_format(self):
        """Test batch formatting with invalid format."""
        batch_formatter = BatchFormatter(self.emails)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError):
                batch_formatter.format_all(
                    output_format="invalid",
                    base_path=temp_dir
                )
    
    def test_format_all_empty_list(self):
        """Test batch formatting with empty email list."""
        batch_formatter = BatchFormatter([])
        
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = batch_formatter.format_all(
                output_format="md",
                base_path=temp_dir
            )
            
            assert paths == []


class TestFormatterEdgeCases:
    """Tests for edge cases in Formatter."""
    
    def test_formatter_with_empty_email(self):
        """Test formatter with minimal email."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject=""
        )
        formatter = Formatter(email)
        
        result = formatter.to_markdown()
        
        assert "Email:" in result
        assert isinstance(result, str)
    
    def test_formatter_with_unicode(self):
        """Test formatter with unicode characters."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Unicode: 你好世界 🌍",
            body_plain="Body: Привет мир مرحبا"
        )
        formatter = Formatter(email)
        
        result = formatter.to_markdown()
        
        assert "你好世界" in result
        assert "Привет мир" in result
    
    def test_formatter_with_special_characters(self):
        """Test formatter with special characters."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Special: @#$%^&*()",
            body_plain="Body: <>&\"'"
        )
        formatter = Formatter(email)
        
        result = formatter.to_markdown()
        
        assert "@#$%^&*()" in result
        assert "<>&\"'" in result
    
    def test_formatter_with_long_subject(self):
        """Test formatter with very long subject."""
        long_subject = "A" * 1000
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject=long_subject
        )
        formatter = Formatter(email)
        
        result = formatter.to_markdown()
        
        assert long_subject in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
