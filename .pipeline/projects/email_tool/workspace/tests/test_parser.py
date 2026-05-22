"""Tests for the EmailParser module."""

import pytest
import os
import tempfile
from datetime import datetime
from email_tool.parser import EmailParser
from email_tool.models import Email


class TestEmailParser:
    """Tests for EmailParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = EmailParser()
        self.sample_email_content = """From: sender@example.com
To: recipient@example.com
Subject: Test Email Subject
Date: Mon, 15 Jan 2024 10:30:00 +0000
Message-ID: <test123@example.com>

This is the plain text body of the email.
"""
    
    def test_parse_file_path(self):
        """Test parsing from file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.eml', delete=False) as f:
            f.write(self.sample_email_content)
            temp_path = f.name
        
        try:
            email = self.parser.parse(temp_path)
            
            assert email is not None
            assert isinstance(email, Email)
            assert email.from_addr == "sender@example.com"
            assert email.to_addrs == ["recipient@example.com"]
            assert email.subject == "Test Email Subject"
            assert email.body_plain == "This is the plain text body of the email."
        finally:
            os.unlink(temp_path)
    
    def test_parse_content(self):
        """Test parsing from string content."""
        email = self.parser.parse_content(self.sample_email_content)
        
        assert email is not None
        assert isinstance(email, Email)
        assert email.from_addr == "sender@example.com"
        assert email.to_addrs == ["recipient@example.com"]
        assert email.subject == "Test Email Subject"
        assert email.body_plain == "This is the plain text body of the email."
    
    def test_parse_with_html_body(self):
        """Test parsing email with HTML body."""
        html_email = """From: sender@example.com
To: recipient@example.com
Subject: HTML Email
Date: Mon, 15 Jan 2024 10:30:00 +0000

<html>
<body>
<p>This is the <strong>HTML</strong> body.</p>
</body>
</html>
"""
        email = self.parser.parse_content(html_email)
        
        assert email is not None
        assert email.body_html == "<html>\n<body>\n<p>This is the <strong>HTML</strong> body.</p>\n</body>\n</html>"
    
    def test_parse_with_multipart_body(self):
        """Test parsing email with multipart body."""
        multipart_email = """From: sender@example.com
To: recipient@example.com
Subject: Multipart Email
Date: Mon, 15 Jan 2024 10:30:00 +0000
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

This is the plain text body.

--boundary123
Content-Type: text/html; charset="utf-8"

<p>This is the <strong>HTML</strong> body.</p>

--boundary123--
"""
        email = self.parser.parse_content(multipart_email)
        
        assert email is not None
        assert email.body_plain == "This is the plain text body."
        assert email.body_html == "<p>This is the <strong>HTML</strong> body.</p>"
    
    def test_parse_with_attachments(self):
        """Test parsing email with attachments."""
        attachment_email = """From: sender@example.com
To: recipient@example.com
Subject: Email with Attachment
Date: Mon, 15 Jan 2024 10:30:00 +0000
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

This email has an attachment.

--boundary123
Content-Type: application/pdf
Content-Disposition: attachment; filename="document.pdf"

[Binary content would be here]

--boundary123--
"""
        email = self.parser.parse_content(attachment_email)
        
        assert email is not None
        assert "document.pdf" in email.attachments
    
    def test_parse_with_multiple_recipients(self):
        """Test parsing email with multiple recipients."""
        multi_recipient_email = """From: sender@example.com
To: recipient1@example.com, recipient2@example.com
Cc: cc@example.com
Subject: Multi-recipient Email
Date: Mon, 15 Jan 2024 10:30:00 +0000

Email with multiple recipients.
"""
        email = self.parser.parse_content(multi_recipient_email)
        
        assert email is not None
        assert len(email.to_addrs) == 2
        assert "recipient1@example.com" in email.to_addrs
        assert "recipient2@example.com" in email.to_addrs
    
    def test_parse_with_custom_headers(self):
        """Test parsing email with custom headers."""
        custom_headers_email = """From: sender@example.com
To: recipient@example.com
Subject: Custom Headers Email
X-Priority: 1
X-Mailer: CustomMailer
Date: Mon, 15 Jan 2024 10:30:00 +0000

Email with custom headers.
"""
        email = self.parser.parse_content(custom_headers_email)
        
        assert email is not None
        assert email.raw_headers.get("X-Priority") == "1"
        assert email.raw_headers.get("X-Mailer") == "CustomMailer"
    
    def test_parse_empty_email(self):
        """Test parsing empty email content."""
        email = self.parser.parse_content("")
        
        assert email is not None
        assert email.from_addr is None
        assert email.subject is None
        assert email.body_plain is None
    
    def test_parse_invalid_email(self):
        """Test parsing invalid email content."""
        invalid_email = "This is not a valid email format"
        
        email = self.parser.parse_content(invalid_email)
        
        # Should still return an Email object even if parsing fails
        assert email is not None
        assert isinstance(email, Email)
    
    def test_parse_with_date(self):
        """Test parsing email with date header."""
        email = self.parser.parse_content(self.sample_email_content)
        
        assert email.date is not None
        assert isinstance(email.date, datetime)
        assert email.date.year == 2024
        assert email.date.month == 1
        assert email.date.day == 15
    
    def test_parse_with_missing_fields(self):
        """Test parsing email with missing optional fields."""
        minimal_email = """From: sender@example.com
Subject: Minimal Email
Date: Mon, 15 Jan 2024 10:30:00 +0000

No To field, no body.
"""
        email = self.parser.parse_content(minimal_email)
        
        assert email is not None
        assert email.from_addr == "sender@example.com"
        assert email.subject == "Minimal Email"
        assert email.to_addrs == []
        assert email.body_plain == "No To field, no body."
    
    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse("/nonexistent/path/to/email.eml")
    
    def test_parse_with_special_characters(self):
        """Test parsing email with special characters."""
        special_email = """From: sender@example.com
To: recipient@example.com
Subject: Test with special chars: @#$%^&*()
Date: Mon, 15 Jan 2024 10:30:00 +0000

Body with special chars: <>&"'
"""
        email = self.parser.parse_content(special_email)
        
        assert email is not None
        assert email.subject == "Test with special chars: @#$%^&*()"
        assert "<>&\"'" in email.body_plain
    
    def test_parse_with_unicode(self):
        """Test parsing email with unicode characters."""
        unicode_email = """From: sender@example.com
To: recipient@example.com
Subject: Unicode Test: 你好世界 🌍
Date: Mon, 15 Jan 2024 10:30:00 +0000

Body with unicode: Привет мир مرحبا
"""
        email = self.parser.parse_content(unicode_email)
        
        assert email is not None
        assert "你好世界" in email.subject
        assert "Привет мир" in email.body_plain


class TestEmailParserBatch:
    """Tests for batch parsing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = EmailParser()
    
    def test_parse_batch_from_directory(self):
        """Test parsing multiple emails from directory."""
        emails_data = [
            """From: sender1@example.com
To: recipient@example.com
Subject: Email 1
Date: Mon, 15 Jan 2024 10:30:00 +0000

First email.
""",
            """From: sender2@example.com
To: recipient@example.com
Subject: Email 2
Date: Mon, 15 Jan 2024 11:30:00 +0000

Second email.
""",
            """From: sender3@example.com
To: recipient@example.com
Subject: Email 3
Date: Mon, 15 Jan 2024 12:30:00 +0000

Third email.
"""
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write test emails
            for i, content in enumerate(emails_data):
                filepath = os.path.join(temp_dir, f"email_{i}.eml")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Parse batch
            emails = self.parser.parse_batch(temp_dir)
            
            assert len(emails) == 3
            assert emails[0].subject == "Email 1"
            assert emails[1].subject == "Email 2"
            assert emails[2].subject == "Email 3"
    
    def test_parse_batch_with_subdirectories(self):
        """Test parsing emails from subdirectories."""
        emails_data = [
            """From: sender1@example.com
To: recipient@example.com
Subject: Email 1
Date: Mon, 15 Jan 2024 10:30:00 +0000

First email.
""",
            """From: sender2@example.com
To: recipient@example.com
Subject: Email 2
Date: Mon, 15 Jan 2024 11:30:00 +0000

Second email.
"""
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create subdirectory
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)
            
            # Write test emails
            filepath1 = os.path.join(temp_dir, "email_1.eml")
            filepath2 = os.path.join(subdir, "email_2.eml")
            
            with open(filepath1, 'w', encoding='utf-8') as f:
                f.write(emails_data[0])
            with open(filepath2, 'w', encoding='utf-8') as f:
                f.write(emails_data[1])
            
            # Parse batch
            emails = self.parser.parse_batch(temp_dir)
            
            assert len(emails) == 2
    
    def test_parse_batch_empty_directory(self):
        """Test parsing from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            emails = self.parser.parse_batch(temp_dir)
            
            assert emails == []
    
    def test_parse_batch_non_eml_files(self):
        """Test parsing directory with non-.eml files."""
        emails_data = [
            """From: sender@example.com
To: recipient@example.com
Subject: Email 1
Date: Mon, 15 Jan 2024 10:30:00 +0000

First email.
"""
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write test email
            filepath = os.path.join(temp_dir, "email_1.eml")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(emails_data[0])
            
            # Write non-.eml file
            non_eml_path = os.path.join(temp_dir, "readme.txt")
            with open(non_eml_path, 'w', encoding='utf-8') as f:
                f.write("This is not an email")
            
            # Parse batch
            emails = self.parser.parse_batch(temp_dir)
            
            assert len(emails) == 1
            assert emails[0].subject == "Email 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
