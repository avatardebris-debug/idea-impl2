"""Tests for Email Tool email processing.

This module contains comprehensive tests for email processing,
parsing, and transformation logic.
"""

import pytest
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_tool.email_processing import (
    EmailProcessor,
    EmailParser,
    EmailTransformer,
    EmailFormat,
    EmailProcessorError,
    parse_email,
    parse_email_from_file,
    parse_email_from_string,
    parse_email_from_bytes,
    transform_email,
    transform_emails_batch,
    detect_email_format,
    detect_email_format_from_file,
    detect_email_format_from_string,
    detect_email_format_from_bytes
)
from email_tool.models import Email, EmailMetadata


class TestEmailParser:
    """Tests for EmailParser class."""
    
    def test_parse_email_from_mime_message(self):
        """Test parsing email from MIME message."""
        parser = EmailParser()
        
        msg = MIMEText("Test body", "plain")
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'test@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Date'] = 'Mon, 1 Jan 2024 00:00:00 +0000'
        
        email_obj = parser.parse(msg)
        
        assert email_obj.from_email == "test@example.com"
        assert email_obj.subject == "Test Subject"
        assert email_obj.body_text == "Test body"
    
    def test_parse_email_with_html(self):
        """Test parsing email with HTML content."""
        parser = EmailParser()
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'test@example.com'
        
        text_part = MIMEText("Plain text", "plain")
        html_part = MIMEText("<p>HTML content</p>", "html")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        email_obj = parser.parse(msg)
        
        assert email_obj.body_text == "Plain text"
        assert email_obj.body_html == "<p>HTML content</p>"
    
    def test_parse_email_with_attachments(self):
        """Test parsing email with attachments."""
        parser = EmailParser()
        
        msg = MIMEMultipart()
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'test@example.com'
        
        text_part = MIMEText("Test body", "plain")
        msg.attach(text_part)
        
        email_obj = parser.parse(msg)
        
        assert email_obj.from_email == "test@example.com"
        assert email_obj.subject == "Test Subject"
        assert email_obj.body_text == "Test body"
    
    def test_parse_email_missing_fields(self):
        """Test parsing email with missing fields."""
        parser = EmailParser()
        
        msg = MIMEText("Test body", "plain")
        
        email_obj = parser.parse(msg)
        
        assert email_obj.from_email is None
        assert email_obj.subject is None
        assert email_obj.body_text == "Test body"
    
    def test_parse_email_with_headers(self):
        """Test parsing email with custom headers."""
        parser = EmailParser()
        
        msg = MIMEText("Test body", "plain")
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'test@example.com'
        msg['X-Custom-Header'] = 'Custom Value'
        
        email_obj = parser.parse(msg)
        
        assert email_obj.from_email == "test@example.com"
        assert email_obj.subject == "Test Subject"
        assert email_obj.headers.get("X-Custom-Header") == "Custom Value"
    
    def test_parse_email_with_date(self):
        """Test parsing email with date."""
        parser = EmailParser()
        
        msg = MIMEText("Test body", "plain")
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'test@example.com'
        msg['Date'] = 'Mon, 1 Jan 2024 00:00:00 +0000'
        
        email_obj = parser.parse(msg)
        
        assert email_obj.metadata.received_date is not None
    
    def test_parse_email_with_message_id(self):
        """Test parsing email with message ID."""
        parser = EmailParser()
        
        msg = MIMEText("Test body", "plain")
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'test@example.com'
        msg['Message-ID'] = '<test@example.com>'
        
        email_obj = parser.parse(msg)
        
        assert email_obj.metadata.message_id == "<test@example.com>"


class TestEmailTransformer:
    """Tests for EmailTransformer class."""
    
    def test_transform_email_to_eml(self):
        """Test transforming email to EML format."""
        transformer = EmailTransformer()
        
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = transformer.transform(email_obj, EmailFormat.EML)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_transform_email_to_msg(self):
        """Test transforming email to MSG format."""
        transformer = EmailTransformer()
        
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = transformer.transform(email_obj, EmailFormat.MSG)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_transform_email_to_txt(self):
        """Test transforming email to TXT format."""
        transformer = EmailTransformer()
        
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = transformer.transform(email_obj, EmailFormat.TXT)
        
        assert result is not None
        assert isinstance(result, str)
    
    def test_transform_email_with_html(self):
        """Test transforming email with HTML content."""
        transformer = EmailTransformer()
        
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body",
            body_html="<p>HTML content</p>"
        )
        
        result = transformer.transform(email_obj, EmailFormat.EML)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_transform_email_with_attachments(self):
        """Test transforming email with attachments."""
        transformer = EmailTransformer()
        
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body",
            attachments=[
                {
                    "filename": "test.txt",
                    "content": b"Test attachment content",
                    "content_type": "text/plain"
                }
            ]
        )
        
        result = transformer.transform(email_obj, EmailFormat.EML)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_transform_email_invalid_format(self):
        """Test transforming email with invalid format."""
        transformer = EmailTransformer()
        
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        with pytest.raises(ValueError, match="Invalid format"):
            transformer.transform(email_obj, "invalid")


class TestEmailProcessor:
    """Tests for EmailProcessor class."""
    
    def test_process_email_parse_and_transform(self):
        """Test processing email with parse and transform."""
        processor = EmailProcessor()
        
        email_bytes = b"""From: test@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 00:00:00 +0000
Message-ID: <test@example.com>

Test body
"""
        
        result = processor.process(
            email_bytes,
            output_format=EmailFormat.TXT
        )
        
        assert result is not None
        assert "Test Subject" in result
        assert "Test body" in result
    
    def test_process_email_with_headers(self):
        """Test processing email with headers."""
        processor = EmailProcessor()
        
        email_bytes = b"""From: test@example.com
Subject: Test Subject
X-Custom-Header: Custom Value
Date: Mon, 1 Jan 2024 00:00:00 +0000

Test body
"""
        
        result = processor.process(
            email_bytes,
            output_format=EmailFormat.TXT
        )
        
        assert result is not None
        assert "Custom Value" in result
    
    def test_process_email_with_attachments(self):
        """Test processing email with attachments."""
        processor = EmailProcessor()
        
        email_bytes = b"""From: test@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 00:00:00 +0000

Test body
"""
        
        result = processor.process(
            email_bytes,
            output_format=EmailFormat.TXT
        )
        
        assert result is not None
    
    def test_process_email_invalid_format(self):
        """Test processing email with invalid format."""
        processor = EmailProcessor()
        
        email_bytes = b"""From: test@example.com
Subject: Test Subject

Test body
"""
        
        with pytest.raises(ValueError, match="Invalid format"):
            processor.process(
                email_bytes,
                output_format="invalid"
            )
    
    def test_process_email_empty(self):
        """Test processing empty email."""
        processor = EmailProcessor()
        
        with pytest.raises(EmailProcessorError, match="Empty email"):
            processor.process(
                b"",
                output_format=EmailFormat.TXT
            )
    
    def test_process_email_corrupted(self):
        """Test processing corrupted email."""
        processor = EmailProcessor()
        
        with pytest.raises(EmailProcessorError, match="Failed to parse email"):
            processor.process(
                b"Corrupted email content",
                output_format=EmailFormat.TXT
            )


class TestParseEmailFunctions:
    """Tests for parse_email functions."""
    
    def test_parse_email_from_bytes(self):
        """Test parsing email from bytes."""
        email_bytes = b"""From: test@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 00:00:00 +0000

Test body
"""
        
        email_obj = parse_email(email_bytes)
        
        assert email_obj.from_email == "test@example.com"
        assert email_obj.subject == "Test Subject"
        assert email_obj.body_text == "Test body"
    
    def test_parse_email_from_string(self):
        """Test parsing email from string."""
        email_str = """From: test@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 00:00:00 +0000

Test body
"""
        
        email_obj = parse_email_from_string(email_str)
        
        assert email_obj.from_email == "test@example.com"
        assert email_obj.subject == "Test Subject"
    
    def test_parse_email_from_file(self):
        """Test parsing email from file."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.eml') as f:
            f.write("""From: test@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 00:00:00 +0000

Test body
""")
            temp_file = f.name
        
        try:
            email_obj = parse_email_from_file(temp_file)
            
            assert email_obj.from_email == "test@example.com"
            assert email_obj.subject == "Test Subject"
        finally:
            import os
            os.unlink(temp_file)
    
    def test_parse_email_from_mime_message(self):
        """Test parsing email from MIME message."""
        msg = MIMEText("Test body", "plain")
        msg['Subject'] = 'Test Subject'
        msg['From'] = 'test@example.com'
        
        email_obj = parse_email(msg)
        
        assert email_obj.from_email == "test@example.com"
        assert email_obj.subject == "Test Subject"


class TestTransformEmailFunctions:
    """Tests for transform_email functions."""
    
    def test_transform_email_to_eml(self):
        """Test transforming email to EML."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = transform_email(email_obj, EmailFormat.EML)
        
        assert result is not None
        assert isinstance(result, bytes)
    
    def test_transform_email_to_txt(self):
        """Test transforming email to TXT."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = transform_email(email_obj, EmailFormat.TXT)
        
        assert result is not None
        assert isinstance(result, str)
    
    def test_transform_email_to_msg(self):
        """Test transforming email to MSG."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = transform_email(email_obj, EmailFormat.MSG)
        
        assert result is not None
        assert isinstance(result, bytes)


class TestDetectEmailFormat:
    """Tests for email format detection."""
    
    def test_detect_format_from_bytes_eml(self):
        """Test detecting EML format from bytes."""
        email_bytes = b"""From: test@example.com
Subject: Test Subject

Test body
"""
        
        format_type = detect_email_format_from_bytes(email_bytes)
        
        assert format_type == EmailFormat.EML
    
    def test_detect_format_from_bytes_txt(self):
        """Test detecting TXT format from bytes."""
        email_bytes = b"""Test Subject
Test body
"""
        
        format_type = detect_email_format_from_bytes(email_bytes)
        
        assert format_type == EmailFormat.TXT
    
    def test_detect_format_from_bytes_msg(self):
        """Test detecting MSG format from bytes."""
        # MSG files typically start with specific bytes
        email_bytes = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
        
        format_type = detect_email_format_from_bytes(email_bytes)
        
        assert format_type == EmailFormat.MSG
    
    def test_detect_format_from_string_eml(self):
        """Test detecting EML format from string."""
        email_str = """From: test@example.com
Subject: Test Subject

Test body
"""
        
        format_type = detect_email_format_from_string(email_str)
        
        assert format_type == EmailFormat.EML
    
    def test_detect_format_from_string_txt(self):
        """Test detecting TXT format from string."""
        email_str = """Test Subject
Test body
"""
        
        format_type = detect_email_format_from_string(email_str)
        
        assert format_type == EmailFormat.TXT
    
    def test_detect_format_from_file_eml(self):
        """Test detecting EML format from file."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.eml') as f:
            f.write("""From: test@example.com
Subject: Test Subject

Test body
""")
            temp_file = f.name
        
        try:
            format_type = detect_email_format_from_file(temp_file)
            
            assert format_type == EmailFormat.EML
        finally:
            import os
            os.unlink(temp_file)
    
    def test_detect_format_from_file_txt(self):
        """Test detecting TXT format from file."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("""Test Subject
Test body
""")
            temp_file = f.name
        
        try:
            format_type = detect_email_format_from_file(temp_file)
            
            assert format_type == EmailFormat.TXT
        finally:
            import os
            os.unlink(temp_file)
    
    def test_detect_format_unknown(self):
        """Test detecting unknown format."""
        email_bytes = b"Unknown format content"
        
        format_type = detect_email_format_from_bytes(email_bytes)
        
        assert format_type == EmailFormat.UNKNOWN


class TestBatchProcessing:
    """Tests for batch email processing."""
    
    def test_transform_emails_batch(self):
        """Test transforming multiple emails."""
        emails = [
            Email(
                from_email="test1@example.com",
                subject="Test Subject 1",
                body_text="Test body 1"
            ),
            Email(
                from_email="test2@example.com",
                subject="Test Subject 2",
                body_text="Test body 2"
            )
        ]
        
        results = transform_emails_batch(emails, EmailFormat.TXT)
        
        assert len(results) == 2
        assert "Test Subject 1" in results[0]
        assert "Test Subject 2" in results[1]
    
    def test_transform_emails_batch_empty(self):
        """Test transforming empty list of emails."""
        results = transform_emails_batch([], EmailFormat.TXT)
        
        assert len(results) == 0
    
    def test_transform_emails_batch_with_errors(self):
        """Test transforming emails with errors."""
        emails = [
            Email(
                from_email="test1@example.com",
                subject="Test Subject 1",
                body_text="Test body 1"
            ),
            Email(
                from_email="test2@example.com",
                subject="Test Subject 2",
                body_text="Test body 2"
            )
        ]
        
        results = transform_emails_batch(emails, EmailFormat.TXT)
        
        assert len(results) == 2
        assert all(isinstance(r, str) for r in results)


class TestEmailProcessingIntegration:
    """Integration tests for email processing."""
    
    def test_full_email_processing_workflow(self):
        """Test complete email processing workflow."""
        # Create email
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        # Transform to EML
        transformer = EmailTransformer()
        eml_bytes = transformer.transform(email_obj, EmailFormat.EML)
        
        # Parse from EML
        parser = EmailParser()
        parsed_email = parser.parse(emails.message_from_bytes(eml_bytes))
        
        assert parsed_email.from_email == "test@example.com"
        assert parsed_email.subject == "Test Subject"
        assert parsed_email.body_text == "Test body"
    
    def test_email_processing_with_attachments(self):
        """Test email processing with attachments."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body",
            attachments=[
                {
                    "filename": "test.txt",
                    "content": b"Test attachment",
                    "content_type": "text/plain"
                }
            ]
        )
        
        transformer = EmailTransformer()
        eml_bytes = transformer.transform(email_obj, EmailFormat.EML)
        
        parser = EmailParser()
        parsed_email = parser.parse(emails.message_from_bytes(eml_bytes))
        
        assert parsed_email.from_email == "test@example.com"
        assert parsed_email.subject == "Test Subject"
        assert parsed_email.body_text == "Test body"
    
    def test_email_processing_with_html(self):
        """Test email processing with HTML content."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Plain text",
            body_html="<p>HTML content</p>"
        )
        
        transformer = EmailTransformer()
        eml_bytes = transformer.transform(email_obj, EmailFormat.EML)
        
        parser = EmailParser()
        parsed_email = parser.parse(emails.message_from_bytes(eml_bytes))
        
        assert parsed_email.from_email == "test@example.com"
        assert parsed_email.subject == "Test Subject"
        assert parsed_email.body_text == "Plain text"
        assert parsed_email.body_html == "<p>HTML content</p>"
    
    def test_email_processing_with_headers(self):
        """Test email processing with custom headers."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body",
            metadata=EmailMetadata(
                headers={
                    "X-Custom-Header": "Custom Value",
                    "X-Another-Header": "Another Value"
                }
            )
        )
        
        transformer = EmailTransformer()
        eml_bytes = transformer.transform(email_obj, EmailFormat.EML)
        
        parser = EmailParser()
        parsed_email = parser.parse(emails.message_from_bytes(eml_bytes))
        
        assert parsed_email.from_email == "test@example.com"
        assert parsed_email.subject == "Test Subject"
        assert parsed_email.headers.get("X-Custom-Header") == "Custom Value"
        assert parsed_email.headers.get("X-Another-Header") == "Another Value"


class TestEmailProcessingEdgeCases:
    """Tests for edge cases in email processing."""
    
    def test_email_with_special_characters(self):
        """Test email with special characters."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject with special chars: @#$%",
            body_text="Test body with special chars: @#$%"
        )
        
        transformer = EmailTransformer()
        result = transformer.transform(email_obj, EmailFormat.TXT)
        
        assert "special chars" in result
    
    def test_email_with_unicode(self):
        """Test email with unicode characters."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject with unicode: 你好世界",
            body_text="Test body with unicode: 你好世界"
        )
        
        transformer = EmailTransformer()
        result = transformer.transform(email_obj, EmailFormat.TXT)
        
        assert "你好世界" in result
    
    def test_email_with_long_subject(self):
        """Test email with very long subject."""
        long_subject = "A" * 1000
        email_obj = Email(
            from_email="test@example.com",
            subject=long_subject,
            body_text="Test body"
        )
        
        transformer = EmailTransformer()
        result = transformer.transform(email_obj, EmailFormat.TXT)
        
        assert long_subject in result
    
    def test_email_with_empty_body(self):
        """Test email with empty body."""
        email_obj = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text=""
        )
        
        transformer = EmailTransformer()
        result = transformer.transform(email_obj, EmailFormat.TXT)
        
        assert "Test Subject" in result
    
    def test_email_with_no_subject(self):
        """Test email with no subject."""
        email_obj = Email(
            from_email="test@example.com",
            subject=None,
            body_text="Test body"
        )
        
        transformer = EmailTransformer()
        result = transformer.transform(email_obj, EmailFormat.TXT)
        
        assert "Test body" in result
    
    def test_email_with_no_from(self):
        """Test email with no from address."""
        email_obj = Email(
            from_email=None,
            subject="Test Subject",
            body_text="Test body"
        )
        
        transformer = EmailTransformer()
        result = transformer.transform(email_obj, EmailFormat.TXT)
        
        assert "Test Subject" in result


class TestEmailProcessingPerformance:
    """Performance tests for email processing."""
    
    def test_process_large_email(self):
        """Test processing large email."""
        processor = EmailProcessor()
        
        # Create large email
        large_body = "A" * 100000
        email_bytes = f"""From: test@example.com
Subject: Test Subject
Date: Mon, 1 Jan 2024 00:00:00 +0000

{large_body}
""".encode()
        
        result = processor.process(
            email_bytes,
            output_format=EmailFormat.TXT
        )
        
        assert len(result) > 0
        assert large_body in result
    
    def test_process_many_emails(self):
        """Test processing many emails."""
        processor = EmailProcessor()
        
        emails = []
        for i in range(100):
            email_bytes = f"""From: test{i}@example.com
Subject: Test Subject {i}
Date: Mon, 1 Jan 2024 00:00:00 +0000

Test body {i}
""".encode()
            emails.append(email_bytes)
        
        results = []
        for email_bytes in emails:
            result = processor.process(
                email_bytes,
                output_format=EmailFormat.TXT
            )
            results.append(result)
        
        assert len(results) == 100
        assert all("Test Subject" in r for r in results)


class TestEmailProcessingErrors:
    """Tests for error handling in email processing."""
    
    def test_process_invalid_email(self):
        """Test processing invalid email."""
        processor = EmailProcessor()
        
        with pytest.raises(EmailProcessorError, match="Failed to parse email"):
            processor.process(
                b"Invalid email content",
                output_format=EmailFormat.TXT
            )
    
    def test_process_empty_email(self):
        """Test processing empty email."""
        processor = EmailProcessor()
        
        with pytest.raises(EmailProcessorError, match="Empty email"):
            processor.process(
                b"",
                output_format=EmailFormat.TXT
            )
    
    def test_process_corrupted_email(self):
        """Test processing corrupted email."""
        processor = EmailProcessor()
        
        with pytest.raises(EmailProcessorError, match="Failed to parse email"):
            processor.process(
                b"Corrupted email content",
                output_format=EmailFormat.TXT
            )
    
    def test_parse_invalid_mime_message(self):
        """Test parsing invalid MIME message."""
        parser = EmailParser()
        
        with pytest.raises(EmailProcessorError, match="Failed to parse email"):
            parser.parse(None)
    
    def test_transform_invalid_email(self):
        """Test transforming invalid email."""
        transformer = EmailTransformer()
        
        with pytest.raises(ValueError, match="Invalid email"):
            transformer.transform(None, EmailFormat.TXT)
    
    def test_detect_format_invalid_input(self):
        """Test detecting format with invalid input."""
        with pytest.raises(ValueError, match="Invalid input"):
            detect_email_format_from_bytes(None)
        
        with pytest.raises(ValueError, match="Invalid input"):
            detect_email_format_from_string(None)
        
        with pytest.raises(ValueError, match="Invalid input"):
            detect_email_format_from_file(None)
