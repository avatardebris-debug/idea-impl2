"""Tests for Email Tool main module.

This module contains comprehensive tests for the main email tool functionality,
including email management, filtering, and search capabilities.
"""

import pytest
from datetime import datetime
from email_tool import EmailTool
from email_tool.models import Email, EmailMetadata
from email_tool.email_manager import EmailManager
from email_tool.email_filter import EmailFilter
from email_tool.email_search import EmailSearch
from email_tool.rules import RuleSet, Rule, RuleType


class TestEmailTool:
    """Tests for EmailTool class."""
    
    def test_email_tool_creation(self):
        """Test EmailTool creation."""
        tool = EmailTool()
        
        assert tool is not None
        assert tool.email_manager is not None
        assert tool.email_filter is not None
        assert tool.email_search is not None
    
    def test_email_tool_with_custom_manager(self):
        """Test EmailTool with custom email manager."""
        custom_manager = EmailManager()
        tool = EmailTool(email_manager=custom_manager)
        
        assert tool.email_manager is custom_manager
    
    def test_email_tool_add_email(self):
        """Test adding email to tool."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = tool.add_email(email)
        
        assert result is True
        assert len(tool.email_manager.emails) == 1
    
    def test_email_tool_add_emails(self):
        """Test adding multiple emails to tool."""
        tool = EmailTool()
        
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
        
        result = tool.add_emails(emails)
        
        assert result is True
        assert len(tool.email_manager.emails) == 2
    
    def test_email_tool_get_email(self):
        """Test getting email by ID."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        tool.add_email(email)
        
        result = tool.get_email(email.id)
        
        assert result is not None
        assert result.id == email.id
        assert result.from_email == "test@example.com"
    
    def test_email_tool_get_email_not_found(self):
        """Test getting non-existent email."""
        tool = EmailTool()
        
        result = tool.get_email("non-existent-id")
        
        assert result is None
    
    def test_email_tool_get_emails(self):
        """Test getting all emails."""
        tool = EmailTool()
        
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
        
        tool.add_emails(emails)
        
        result = tool.get_emails()
        
        assert len(result) == 2
    
    def test_email_tool_get_emails_with_filter(self):
        """Test getting emails with filter."""
        tool = EmailTool()
        
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
        
        tool.add_emails(emails)
        
        result = tool.get_emails(from_email="test1@example.com")
        
        assert len(result) == 1
        assert result[0].from_email == "test1@example.com"
    
    def test_email_tool_update_email(self):
        """Test updating email."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        tool.add_email(email)
        
        # Update email
        email.subject = "Updated Subject"
        email.body_text = "Updated body"
        
        result = tool.update_email(email)
        
        assert result is True
        updated_email = tool.get_email(email.id)
        assert updated_email.subject == "Updated Subject"
        assert updated_email.body_text == "Updated body"
    
    def test_email_tool_update_email_not_found(self):
        """Test updating non-existent email."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = tool.update_email(email)
        
        assert result is False
    
    def test_email_tool_delete_email(self):
        """Test deleting email."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        tool.add_email(email)
        
        result = tool.delete_email(email.id)
        
        assert result is True
        assert len(tool.email_manager.emails) == 0
    
    def test_email_tool_delete_email_not_found(self):
        """Test deleting non-existent email."""
        tool = EmailTool()
        
        result = tool.delete_email("non-existent-id")
        
        assert result is False
    
    def test_email_tool_search_emails(self):
        """Test searching emails."""
        tool = EmailTool()
        
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
        
        tool.add_emails(emails)
        
        results = tool.search_emails(query="Test")
        
        assert len(results) == 2
    
    def test_email_tool_search_emails_no_results(self):
        """Test searching emails with no results."""
        tool = EmailTool()
        
        emails = [
            Email(
                from_email="test1@example.com",
                subject="Test Subject 1",
                body_text="Test body 1"
            )
        ]
        
        tool.add_emails(emails)
        
        results = tool.search_emails(query="Non-existent")
        
        assert len(results) == 0
    
    def test_email_tool_filter_emails(self):
        """Test filtering emails."""
        tool = EmailTool()
        
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
        
        tool.add_emails(emails)
        
        results = tool.filter_emails(from_email="test1@example.com")
        
        assert len(results) == 1
        assert results[0].from_email == "test1@example.com"
    
    def test_email_tool_filter_emails_no_results(self):
        """Test filtering emails with no results."""
        tool = EmailTool()
        
        emails = [
            Email(
                from_email="test1@example.com",
                subject="Test Subject 1",
                body_text="Test body 1"
            )
        ]
        
        tool.add_emails(emails)
        
        results = tool.filter_emails(from_email="non-existent@example.com")
        
        assert len(results) == 0
    
    def test_email_tool_get_statistics(self):
        """Test getting email statistics."""
        tool = EmailTool()
        
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
        
        tool.add_emails(emails)
        
        stats = tool.get_statistics()
        
        assert stats["total_emails"] == 2
        assert stats["unique_senders"] == 2
    
    def test_email_tool_clear_all_emails(self):
        """Test clearing all emails."""
        tool = EmailTool()
        
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
        
        tool.add_emails(emails)
        
        result = tool.clear_all_emails()
        
        assert result is True
        assert len(tool.email_manager.emails) == 0
    
    def test_email_tool_export_emails(self):
        """Test exporting emails."""
        tool = EmailTool()
        
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
        
        tool.add_emails(emails)
        
        result = tool.export_emails()
        
        assert result is not None
        assert len(result) == 2
    
    def test_email_tool_import_emails(self):
        """Test importing emails."""
        tool = EmailTool()
        
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
        
        tool.add_emails(emails)
        
        exported = tool.export_emails()
        
        tool.clear_all_emails()
        
        result = tool.import_emails(exported)
        
        assert result is True
        assert len(tool.email_manager.emails) == 2


class TestEmailToolIntegration:
    """Integration tests for EmailTool class."""
    
    def test_email_tool_full_workflow(self):
        """Test complete EmailTool workflow."""
        tool = EmailTool()
        
        # Add emails
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
        
        tool.add_emails(emails)
        
        # Search emails
        results = tool.search_emails(query="Test")
        assert len(results) == 2
        
        # Filter emails
        filtered = tool.filter_emails(from_email="test1@example.com")
        assert len(filtered) == 1
        
        # Get statistics
        stats = tool.get_statistics()
        assert stats["total_emails"] == 2
        
        # Export and import
        exported = tool.export_emails()
        tool.clear_all_emails()
        
        tool.import_emails(exported)
        assert len(tool.email_manager.emails) == 2
        
        # Delete email
        tool.delete_email(emails[0].id)
        assert len(tool.email_manager.emails) == 1
    
    def test_email_tool_with_rules(self):
        """Test EmailTool with rules."""
        tool = EmailTool()
        
        # Add rules
        rule_set = RuleSet(name="Test Rules")
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="test@example.com",
            priority=50
        )
        rule_set.add_rule(rule)
        
        tool.email_filter.add_rule_set(rule_set)
        
        # Add email
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        tool.add_email(email)
        
        # Filter emails
        filtered = tool.filter_emails(from_email="test@example.com")
        assert len(filtered) == 1
    
    def test_email_tool_with_search(self):
        """Test EmailTool with search."""
        tool = EmailTool()
        
        # Add emails
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
        
        tool.add_emails(emails)
        
        # Search emails
        results = tool.search_emails(query="Test Subject 1")
        assert len(results) == 1
        assert results[0].id == emails[0].id
    
    def test_email_tool_with_filtering(self):
        """Test EmailTool with filtering."""
        tool = EmailTool()
        
        # Add emails
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
        
        tool.add_emails(emails)
        
        # Filter emails
        filtered = tool.filter_emails(from_email="test1@example.com")
        assert len(filtered) == 1
        assert filtered[0].id == emails[0].id
    
    def test_email_tool_with_export_import(self):
        """Test EmailTool with export and import."""
        tool = EmailTool()
        
        # Add emails
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
        
        tool.add_emails(emails)
        
        # Export
        exported = tool.export_emails()
        assert len(exported) == 2
        
        # Clear and import
        tool.clear_all_emails()
        tool.import_emails(exported)
        
        assert len(tool.email_manager.emails) == 2
        assert tool.email_manager.emails[0].from_email == "test1@example.com"
        assert tool.email_manager.emails[1].from_email == "test2@example.com"


class TestEmailToolEdgeCases:
    """Edge case tests for EmailTool class."""
    
    def test_email_tool_empty(self):
        """Test EmailTool with no emails."""
        tool = EmailTool()
        
        result = tool.get_emails()
        assert len(result) == 0
        
        stats = tool.get_statistics()
        assert stats["total_emails"] == 0
    
    def test_email_tool_duplicate_emails(self):
        """Test EmailTool with duplicate emails."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        tool.add_email(email)
        tool.add_email(email)
        
        # Should have 2 emails (same ID)
        assert len(tool.email_manager.emails) == 2
    
    def test_email_tool_large_dataset(self):
        """Test EmailTool with large dataset."""
        tool = EmailTool()
        
        emails = []
        for i in range(1000):
            emails.append(Email(
                from_email=f"test{i}@example.com",
                subject=f"Test Subject {i}",
                body_text=f"Test body {i}"
            ))
        
        tool.add_emails(emails)
        
        assert len(tool.email_manager.emails) == 1000
        
        # Search
        results = tool.search_emails(query="Test")
        assert len(results) == 1000
        
        # Filter
        filtered = tool.filter_emails(from_email="test500@example.com")
        assert len(filtered) == 1
    
    def test_email_tool_special_characters(self):
        """Test EmailTool with special characters."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject with special chars: @#$%",
            body_text="Test body with special chars: @#$%"
        )
        
        tool.add_email(email)
        
        result = tool.get_email(email.id)
        assert result.subject == "Test Subject with special chars: @#$%"
        assert result.body_text == "Test body with special chars: @#$%"
    
    def test_email_tool_unicode(self):
        """Test EmailTool with unicode characters."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject with unicode: 你好世界",
            body_text="Test body with unicode: 你好世界"
        )
        
        tool.add_email(email)
        
        result = tool.get_email(email.id)
        assert result.subject == "Test Subject with unicode: 你好世界"
        assert result.body_text == "Test body with unicode: 你好世界"
    
    def test_email_tool_long_subject(self):
        """Test EmailTool with very long subject."""
        tool = EmailTool()
        
        long_subject = "A" * 1000
        email = Email(
            from_email="test@example.com",
            subject=long_subject,
            body_text="Test body"
        )
        
        tool.add_email(email)
        
        result = tool.get_email(email.id)
        assert result.subject == long_subject
    
    def test_email_tool_empty_fields(self):
        """Test EmailTool with empty fields."""
        tool = EmailTool()
        
        email = Email(
            from_email="",
            subject="",
            body_text=""
        )
        
        tool.add_email(email)
        
        result = tool.get_email(email.id)
        assert result.from_email == ""
        assert result.subject == ""
        assert result.body_text == ""
    
    def test_email_tool_none_fields(self):
        """Test EmailTool with None fields."""
        tool = EmailTool()
        
        email = Email(
            from_email=None,
            subject=None,
            body_text=None
        )
        
        tool.add_email(email)
        
        result = tool.get_email(email.id)
        assert result.from_email is None
        assert result.subject is None
        assert result.body_text is None


class TestEmailToolPerformance:
    """Performance tests for EmailTool class."""
    
    def test_email_tool_add_many_emails(self):
        """Test adding many emails."""
        tool = EmailTool()
        
        emails = []
        for i in range(1000):
            emails.append(Email(
                from_email=f"test{i}@example.com",
                subject=f"Test Subject {i}",
                body_text=f"Test body {i}"
            ))
        
        tool.add_emails(emails)
        
        assert len(tool.email_manager.emails) == 1000
    
    def test_email_tool_search_many_emails(self):
        """Test searching many emails."""
        tool = EmailTool()
        
        emails = []
        for i in range(1000):
            emails.append(Email(
                from_email=f"test{i}@example.com",
                subject=f"Test Subject {i}",
                body_text=f"Test body {i}"
            ))
        
        tool.add_emails(emails)
        
        results = tool.search_emails(query="Test")
        
        assert len(results) == 1000
    
    def test_email_tool_filter_many_emails(self):
        """Test filtering many emails."""
        tool = EmailTool()
        
        emails = []
        for i in range(1000):
            emails.append(Email(
                from_email=f"test{i}@example.com",
                subject=f"Test Subject {i}",
                body_text=f"Test body {i}"
            ))
        
        tool.add_emails(emails)
        
        results = tool.filter_emails(from_email="test500@example.com")
        
        assert len(results) == 1


class TestEmailToolErrors:
    """Error handling tests for EmailTool class."""
    
    def test_email_tool_get_email_invalid_id(self):
        """Test getting email with invalid ID."""
        tool = EmailTool()
        
        result = tool.get_email("invalid-id")
        
        assert result is None
    
    def test_email_tool_update_email_invalid_id(self):
        """Test updating email with invalid ID."""
        tool = EmailTool()
        
        email = Email(
            from_email="test@example.com",
            subject="Test Subject",
            body_text="Test body"
        )
        
        result = tool.update_email(email)
        
        assert result is False
    
    def test_email_tool_delete_email_invalid_id(self):
        """Test deleting email with invalid ID."""
        tool = EmailTool()
        
        result = tool.delete_email("invalid-id")
        
        assert result is False
    
    def test_email_tool_search_empty_query(self):
        """Test searching with empty query."""
        tool = EmailTool()
        
        emails = [
            Email(
                from_email="test@example.com",
                subject="Test Subject",
                body_text="Test body"
            )
        ]
        
        tool.add_emails(emails)
        
        results = tool.search_emails(query="")
        
        # Should return all emails
        assert len(results) == 1
    
    def test_email_tool_filter_empty_criteria(self):
        """Test filtering with empty criteria."""
        tool = EmailTool()
        
        emails = [
            Email(
                from_email="test@example.com",
                subject="Test Subject",
                body_text="Test body"
            )
        ]
        
        tool.add_emails(emails)
        
        results = tool.filter_emails()
        
        # Should return all emails
        assert len(results) == 1
