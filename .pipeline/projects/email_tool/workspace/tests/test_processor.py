"""Unit tests for the email processor module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from email_tool.processor import EmailProcessor, EmailMessage


class TestEmailMessage:
    """Tests for EmailMessage class."""

    def test_email_message_initialization(self):
        """Test EmailMessage initialization."""
        message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        assert message.subject == "Test Subject"
        assert message.from_addr == "sender@example.com"
        assert message.to_addr == "recipient@example.com"
        assert message.body == "Test body"
        assert message.timestamp == 1234567890

    def test_email_message_with_attachments(self):
        """Test EmailMessage with attachments."""
        message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890,
            attachments=["file1.pdf", "file2.docx"]
        )
        
        assert message.attachments == ["file1.pdf", "file2.docx"]

    def test_email_message_to_dict(self):
        """Test EmailMessage to_dict method."""
        message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        message_dict = message.to_dict()
        assert message_dict['subject'] == "Test Subject"
        assert message_dict['from_addr'] == "sender@example.com"
        assert message_dict['to_addr'] == "recipient@example.com"
        assert message_dict['body'] == "Test body"
        assert message_dict['timestamp'] == 1234567890

    def test_email_message_from_dict(self):
        """Test EmailMessage from_dict method."""
        message_dict = {
            'subject': "Test Subject",
            'from_addr': "sender@example.com",
            'to_addr': "recipient@example.com",
            'body': "Test body",
            'timestamp': 1234567890
        }
        
        message = EmailMessage.from_dict(message_dict)
        assert message.subject == "Test Subject"
        assert message.from_addr == "sender@example.com"
        assert message.to_addr == "recipient@example.com"
        assert message.body == "Test body"
        assert message.timestamp == 1234567890


class TestEmailProcessorInitialization:
    """Tests for EmailProcessor initialization."""

    def test_processor_initialization(self):
        """Test EmailProcessor initialization."""
        processor = EmailProcessor(base_path="/tmp/test_base")
        assert processor.base_path == Path("/tmp/test_base")
        assert processor.rules == []
        assert processor.stats == {'processed': 0, 'errors': 0, 'rules_matched': 0}

    def test_processor_initialization_with_rules(self):
        """Test EmailProcessor initialization with rules."""
        rules = [MagicMock()]
        processor = EmailProcessor(base_path="/tmp/test_base", rules=rules)
        assert processor.rules == rules

    def test_processor_initialization_with_config(self):
        """Test EmailProcessor initialization with config."""
        config = MagicMock()
        processor = EmailProcessor(base_path="/tmp/test_base", config=config)
        assert processor.config is config


class TestEmailProcessorProcessing:
    """Tests for EmailProcessor processing."""

    def test_process_email(self, tmp_path):
        """Test processing a single email."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        result = processor.process_email(email_message)
        assert result is True
        assert processor.stats['processed'] == 1

    def test_process_email_with_error(self, tmp_path):
        """Test processing email with error."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        with patch.object(processor, '_save_email', side_effect=Exception("Error")):
            with patch('email_tool.processor.logger') as mock_logger:
                result = processor.process_email(email_message)
                assert result is False
                assert processor.stats['errors'] == 1
                mock_logger.error.assert_called()

    def test_process_email_with_rules(self, tmp_path):
        """Test processing email with rules."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        with patch.object(processor, '_apply_rules') as mock_apply:
            result = processor.process_email(email_message)
            assert result is True
            mock_apply.assert_called()


class TestEmailProcessorSaving:
    """Tests for email saving."""

    def test_save_email(self, tmp_path):
        """Test saving email to file."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        result = processor._save_email(email_message)
        assert result is True

    def test_save_email_creates_directory(self, tmp_path):
        """Test that saving email creates directory structure."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        processor._save_email(email_message)
        
        # Check that directory was created
        assert (tmp_path / "sender@example.com").exists()

    def test_save_email_with_attachments(self, tmp_path):
        """Test saving email with attachments."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890,
            attachments=["file1.pdf"]
        )
        
        result = processor._save_email(email_message)
        assert result is True


class TestEmailProcessorRules:
    """Tests for rule application."""

    def test_apply_rules_no_rules(self, tmp_path):
        """Test applying rules when no rules are set."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        result = processor._apply_rules(email_message)
        assert result is None

    def test_apply_rules_with_rules(self, tmp_path):
        """Test applying rules to email."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        # Mock rules
        mock_rule = MagicMock()
        mock_rule.matches.return_value = True
        mock_rule.category = "test_category"
        processor.rules = [mock_rule]
        
        result = processor._apply_rules(email_message)
        assert result == "test_category"


class TestEmailProcessorStats:
    """Tests for statistics."""

    def test_get_stats(self, tmp_path):
        """Test getting processor statistics."""
        processor = EmailProcessor(base_path=tmp_path)
        
        stats = processor.get_stats()
        assert 'processed' in stats
        assert 'errors' in stats
        assert stats['processed'] == 0
        assert stats['errors'] == 0

    def test_stats_incremented_on_processing(self, tmp_path):
        """Test that stats are incremented on processing."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        processor.process_email(email_message)
        
        stats = processor.get_stats()
        assert stats['processed'] == 1


class TestEmailProcessorEdgeCases:
    """Tests for edge cases."""

    def test_processor_with_unicode_subject(self, tmp_path):
        """Test processing email with unicode subject."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="テスト 日本語",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        result = processor.process_email(email_message)
        assert result is True

    def test_processor_with_empty_body(self, tmp_path):
        """Test processing email with empty body."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="",
            timestamp=1234567890
        )
        
        result = processor.process_email(email_message)
        assert result is True

    def test_processor_with_special_characters_in_from(self, tmp_path):
        """Test processing email with special characters in from address."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender+tag@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890
        )
        
        result = processor.process_email(email_message)
        assert result is True

    def test_processor_with_multiple_attachments(self, tmp_path):
        """Test processing email with multiple attachments."""
        processor = EmailProcessor(base_path=tmp_path)
        
        email_message = EmailMessage(
            subject="Test Subject",
            from_addr="sender@example.com",
            to_addr="recipient@example.com",
            body="Test body",
            timestamp=1234567890,
            attachments=["file1.pdf", "file2.docx", "file3.xlsx"]
        )
        
        result = processor.process_email(email_message)
        assert result is True
