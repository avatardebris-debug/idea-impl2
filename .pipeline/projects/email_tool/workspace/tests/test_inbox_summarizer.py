"""Tests for the InboxSummarizer component."""

import pytest
from email_tool.agent.summarizer import InboxSummarizer
from email_tool.agent.base import AgentResult


class TestInboxSummarizerInit:
    """Tests for InboxSummarizer initialization."""
    
    def test_init_default(self):
        """Test InboxSummarizer with default initialization."""
        summarizer = InboxSummarizer()
        
        assert summarizer is not None


class TestInboxSummarizerSummarizeInbox:
    """Tests for InboxSummarizer.summarize_inbox method."""
    
    def test_summarize_inbox_empty(self):
        """Test summarization with no emails."""
        summarizer = InboxSummarizer()
        
        result = summarizer.summarize_inbox(
            emails=[],
            rules=[],
            matches=[]
        )
        
        assert result.success is True
        assert "No emails in inbox" in result.data
        assert result.metadata["total_emails"] == 0
    
    def test_summarize_inbox_single_email(self):
        """Test summarization with single email."""
        summarizer = InboxSummarizer()
        
        result = summarizer.summarize_inbox(
            emails=[{"id": "1", "category": "general"}],
            rules=[],
            matches=[]
        )
        
        assert result.success is True
        assert "1 emails" in result.data
        assert result.metadata["total_emails"] == 1
    
    def test_summarize_inbox_with_categories(self):
        """Test summarization with categorized emails."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1", "category": "invoices"},
            {"id": "2", "category": "invoices"},
            {"id": "3", "category": "newsletters"},
            {"id": "4", "category": "general"}
        ]
        
        matches = [
            {"email_id": "1", "rule_name": "Invoice Rule"},
            {"email_id": "2", "rule_name": "Invoice Rule"},
            {"email_id": "3", "rule_name": "Newsletter Rule"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=[],
            matches=matches
        )
        
        assert result.success is True
        assert "4 emails" in result.data
        assert "2 invoices" in result.data
        assert "1 newsletters" in result.data
        assert result.metadata["total_emails"] == 4
        assert result.metadata["matched_emails"] == 3
        assert result.metadata["unclassified_emails"] == 1
    
    def test_summarize_inbox_with_unclassified(self):
        """Test summarization with unclassified emails."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1", "category": "general"},
            {"id": "2", "category": "general"},
            {"id": "3", "category": "general"}
        ]
        
        matches = [
            {"email_id": "1", "rule_name": "Rule 1"},
            {"email_id": "2", "rule_name": "Rule 2"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=[],
            matches=matches
        )
        
        assert result.success is True
        assert "3 emails" in result.data
        assert "1 unclassified emails" in result.data
        assert result.metadata["unclassified_emails"] == 1
    
    def test_summarize_inbox_with_rule_statistics(self):
        """Test summarization with rule match statistics."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1", "category": "general"},
            {"id": "2", "category": "general"},
            {"id": "3", "category": "general"}
        ]
        
        matches = [
            {"email_id": "1", "rule_name": "Invoice Rule"},
            {"email_id": "2", "rule_name": "Invoice Rule"},
            {"email_id": "3", "rule_name": "Newsletter Rule"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=[],
            matches=matches
        )
        
        assert result.success is True
        assert "Top rules" in result.data
        assert "Invoice Rule" in result.data
        assert "Newsletter Rule" in result.data
    
    def test_summarize_inbox_multiple_categories(self):
        """Test summarization with multiple categories."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1", "category": "invoices"},
            {"id": "2", "category": "invoices"},
            {"id": "3", "category": "newsletters"},
            {"id": "4", "category": "newsletters"},
            {"id": "5", "category": "work"},
            {"id": "6", "category": "personal"}
        ]
        
        matches = [
            {"email_id": "1", "rule_name": "Invoice Rule"},
            {"email_id": "2", "rule_name": "Invoice Rule"},
            {"email_id": "3", "rule_name": "Newsletter Rule"},
            {"email_id": "4", "rule_name": "Newsletter Rule"},
            {"email_id": "5", "rule_name": "Work Rule"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=[],
            matches=matches
        )
        
        assert result.success is True
        assert "6 emails" in result.data
        assert "2 invoices" in result.data
        assert "2 newsletters" in result.data
        assert "1 work" in result.data
        assert "1 personal" in result.data
        assert "0 unclassified emails" in result.data


class TestInboxSummarizerMetadata:
    """Tests for InboxSummarizer metadata generation."""
    
    def test_metadata_total_emails(self):
        """Test total email count in metadata."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1"},
            {"id": "2"},
            {"id": "3"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=[],
            matches=[]
        )
        
        assert result.metadata["total_emails"] == 3
    
    def test_metadata_matched_emails(self):
        """Test matched email count in metadata."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1"},
            {"id": "2"},
            {"id": "3"}
        ]
        
        matches = [
            {"email_id": "1"},
            {"email_id": "2"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=[],
            matches=matches
        )
        
        assert result.metadata["matched_emails"] == 2
    
    def test_metadata_unclassified_emails(self):
        """Test unclassified email count in metadata."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1", "category": "general"},
            {"id": "2", "category": "general"},
            {"id": "3", "category": "general"}
        ]
        
        matches = [
            {"email_id": "1"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=[],
            matches=matches
        )
        
        assert result.metadata["unclassified_emails"] == 2
    
    def test_metadata_category_breakdown(self):
        """Test category breakdown in metadata."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1", "category": "invoices"},
            {"id": "2", "category": "invoices"},
            {"id": "3", "category": "newsletters"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=[],
            matches=[]
        )
        
        assert "category_breakdown" in result.metadata
        assert result.metadata["category_breakdown"]["invoices"] == 2
        assert result.metadata["category_breakdown"]["newsletters"] == 1


class TestInboxSummarizerPromptConstruction:
    """Tests for prompt construction in InboxSummarizer."""
    
    def test_construct_summary_prompt(self):
        """Test prompt construction for inbox summary."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1", "subject": "Invoice #123", "category": "invoices"},
            {"id": "2", "subject": "Newsletter", "category": "newsletters"}
        ]
        
        prompt = summarizer._construct_summary_prompt(
            emails=emails,
            rules=[],
            matches=[]
        )
        
        assert "summarize inbox" in prompt.lower()
        assert "JSON" in prompt
        assert "invoice" in prompt.lower()
        assert "newsletter" in prompt.lower()


class TestInboxSummarizerErrorHandling:
    """Tests for error handling in InboxSummarizer."""
    
    def test_summarize_inbox_invalid_email_format(self):
        """Test handling of invalid email format."""
        summarizer = InboxSummarizer()
        
        result = summarizer.summarize_inbox(
            emails=[{"id": "1"}],  # Missing category
            rules=[],
            matches=[]
        )
        
        assert result.success is False
        assert "Invalid email format" in result.error_message
    
    def test_summarize_inbox_invalid_match_format(self):
        """Test handling of invalid match format."""
        summarizer = InboxSummarizer()
        
        result = summarizer.summarize_inbox(
            emails=[{"id": "1", "category": "general"}],
            rules=[],
            matches=[{"email_id": "1"}]  # Missing rule_name
        )
        
        assert result.success is False
        assert "Invalid match format" in result.error_message


class TestInboxSummarizerIntegration:
    """Integration tests for InboxSummarizer."""
    
    def test_summarize_with_rules_and_matches(self):
        """Test summarization with rules and matches."""
        summarizer = InboxSummarizer()
        
        emails = [
            {"id": "1", "category": "invoices"},
            {"id": "2", "category": "invoices"},
            {"id": "3", "category": "newsletters"},
            {"id": "4", "category": "general"}
        ]
        
        rules = [
            {"name": "Invoice Rule", "category": "invoices"},
            {"name": "Newsletter Rule", "category": "newsletters"}
        ]
        
        matches = [
            {"email_id": "1", "rule_name": "Invoice Rule"},
            {"email_id": "2", "rule_name": "Invoice Rule"},
            {"email_id": "3", "rule_name": "Newsletter Rule"}
        ]
        
        result = summarizer.summarize_inbox(
            emails=emails,
            rules=rules,
            matches=matches
        )
        
        assert result.success is True
        assert "4 emails" in result.data
        assert "2 invoices" in result.data
        assert "1 newsletters" in result.data
        assert "1 unclassified emails" in result.data
        assert result.metadata["total_emails"] == 4
        assert result.metadata["matched_emails"] == 3
        assert result.metadata["unclassified_emails"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
