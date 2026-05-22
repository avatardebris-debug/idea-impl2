"""Tests for the PromptTemplates component."""

import pytest
from email_tool.agent.prompt_templates import PromptTemplates


class TestPromptTemplatesInit:
    """Tests for PromptTemplates initialization."""
    
    def test_init_default(self):
        """Test PromptTemplates with default configuration."""
        templates = PromptTemplates()
        
        assert templates.rule_generation_prompt == templates.RULE_GENERATION_PROMPT
        assert templates.categorization_prompt == templates.CATEGORIZATION_PROMPT
        assert templates.summarization_prompt == templates.SUMMARIZATION_PROMPT
        assert templates.enable_few_shot is True
        assert templates.VERSION == "1.0.0"
    
    def test_init_with_custom_prompts(self):
        """Test PromptTemplates with custom prompts."""
        custom_rule = "Custom rule prompt"
        custom_cat = "Custom categorization prompt"
        custom_sum = "Custom summarization prompt"
        
        templates = PromptTemplates(
            rule_generation_prompt=custom_rule,
            categorization_prompt=custom_cat,
            summarization_prompt=custom_sum,
            enable_few_shot=False
        )
        
        assert templates.rule_generation_prompt == custom_rule
        assert templates.categorization_prompt == custom_cat
        assert templates.summarization_prompt == custom_sum
        assert templates.enable_few_shot is False
    
    def test_init_uses_kwargs_over_config(self):
        """Test that kwargs override default prompts."""
        custom_rule = "Custom rule prompt"
        
        templates = PromptTemplates(rule_generation_prompt=custom_rule)
        
        assert templates.rule_generation_prompt == custom_rule
        # Other prompts should use defaults
        assert templates.categorization_prompt == templates.CATEGORIZATION_PROMPT


class TestPromptTemplatesVersion:
    """Tests for version tracking."""
    
    def test_get_version(self):
        """Test version retrieval."""
        templates = PromptTemplates()
        
        assert templates.get_version() == "1.0.0"
    
    def test_version_is_class_attribute(self):
        """Test that version is a class attribute."""
        assert PromptTemplates.VERSION == "1.0.0"


class TestPromptTemplatesGetRuleGenerationPrompt:
    """Tests for PromptTemplates.get_rule_generation_prompt method."""
    
    def test_get_rule_generation_prompt_basic(self):
        """Test basic rule generation prompt."""
        templates = PromptTemplates()
        
        description = "Create rule for invoices"
        sample_emails = []
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails
        )
        
        assert "Create rule for invoices" in prompt
        assert "Generate email rules" in prompt
        assert "from_exact" in prompt
        assert "subject_contains" in prompt
        assert "has_attachment" in prompt
    
    def test_get_rule_generation_prompt_with_samples(self):
        """Test rule generation prompt with sample emails."""
        templates = PromptTemplates()
        
        description = "Create rule for invoices"
        sample_emails = [
            {
                "id": "1",
                "from": "billing@example.com",
                "subject": "Your Invoice #12345",
                "body": "Please find your invoice attached.",
                "date": "2024-01-15"
            }
        ]
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails
        )
        
        assert "billing@example.com" in prompt
        assert "Invoice #12345" in prompt
        assert "Please find your invoice attached" in prompt
        assert "2024-01-15" in prompt
    
    def test_get_rule_generation_prompt_no_samples(self):
        """Test rule generation prompt with no sample emails."""
        templates = PromptTemplates()
        
        description = "Create rule for invoices"
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=[]
        )
        
        assert "No sample emails provided" in prompt
    
    def test_get_rule_generation_prompt_with_few_shot(self):
        """Test rule generation prompt with few-shot examples."""
        templates = PromptTemplates()
        
        description = "Create rule for invoices"
        sample_emails = []
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails,
            few_shot=True
        )
        
        assert "Example" in prompt
        assert "vendor_invoices" in prompt
        assert "meeting_requests" in prompt
        assert "boss_urgent" in prompt
    
    def test_get_rule_generation_prompt_no_few_shot(self):
        """Test rule generation prompt without few-shot examples."""
        templates = PromptTemplates()
        
        description = "Create rule for invoices"
        sample_emails = []
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails,
            few_shot=False
        )
        
        # Check that few-shot examples are not included
        assert "vendor_invoices" not in prompt
        assert "meeting_requests" not in prompt
        assert "boss_urgent" not in prompt
    
    def test_get_rule_generation_prompt_complex_description(self):
        """Test rule generation prompt with complex description."""
        templates = PromptTemplates()
        
        description = "Create rule for invoices from Amazon with priority 90"
        sample_emails = []
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails
        )
        
        assert "Create rule for invoices from Amazon with priority 90" in prompt
    
    def test_get_rule_generation_prompt_with_attachments(self):
        """Test rule generation prompt with attachment emails."""
        templates = PromptTemplates()
        
        description = "Create rule for invoices"
        sample_emails = [
            {
                "id": "1",
                "from": "billing@example.com",
                "subject": "Invoice #12345",
                "body": "Please find your invoice attached.",
                "date": "2024-01-15",
                "has_attachments": True
            }
        ]
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails
        )
        
        assert "has_attachments" in prompt.lower()
        assert "True" in prompt


class TestPromptTemplatesGetCategorizationPrompt:
    """Tests for PromptTemplates.get_categorization_prompt method."""
    
    def test_get_categorization_prompt_basic(self):
        """Test basic categorization prompt."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject"}]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            existing_categories=["general"]
        )
        
        assert "general" in prompt
        assert "suggest categories" in prompt.lower()
        assert "Test Subject" in prompt
    
    def test_get_categorization_prompt_with_rules(self):
        """Test categorization prompt with rules."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject"}]
        rules = [
            {
                "name": "Work Rule",
                "type": "from_exact",
                "pattern": "boss@company.com",
                "priority": 90,
                "category": "work"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=rules,
            existing_categories=None
        )
        
        # Should use rule-based categories when existing_categories is None
        assert "Work Rule" in prompt
        assert "work" in prompt
    
    def test_get_categorization_prompt_with_few_shot(self):
        """Test categorization prompt with few-shot examples."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject"}]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            existing_categories=["general"],
            few_shot=True
        )
        
        assert "Example" in prompt
        assert "Your order #12345" in prompt
        assert "Team lunch on Friday" in prompt
        assert "Project Alpha status update" in prompt
    
    def test_get_categorization_prompt_no_few_shot(self):
        """Test categorization prompt without few-shot examples."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject"}]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            existing_categories=["general"],
            few_shot=False
        )
        
        # Check that few-shot examples are not included
        assert "Your order #12345" not in prompt
        assert "Team lunch on Friday" not in prompt
        assert "Project Alpha status update" not in prompt
    
    def test_get_categorization_prompt_multiple_emails(self):
        """Test categorization prompt with multiple emails."""
        templates = PromptTemplates()
        
        emails = [
            {"id": "1", "subject": "Test Subject 1"},
            {"id": "2", "subject": "Test Subject 2"},
            {"id": "3", "subject": "Test Subject 3"}
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            existing_categories=["general"]
        )
        
        assert "Test Subject 1" in prompt
        assert "Test Subject 2" in prompt
        assert "Test Subject 3" in prompt
        assert "Email 1" in prompt
        assert "Email 2" in prompt
        assert "Email 3" in prompt
    
    def test_get_categorization_prompt_empty_existing_categories(self):
        """Test categorization prompt with empty existing categories."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject"}]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            existing_categories=[]
        )
        
        # Should show "No existing categories"
        assert "No existing categories" in prompt


class TestPromptTemplatesGetSummarizationPrompt:
    """Tests for PromptTemplates.get_summarization_prompt method."""
    
    def test_get_summarization_prompt_basic(self):
        """Test basic summarization prompt."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject", "from": "sender@example.com"}]
        rules = []
        matches = []
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=matches
        )
        
        assert "Total emails: 1" in prompt
        assert "Test Subject" in prompt
        assert "sender@example.com" in prompt
        assert "Active rules: 0" in prompt
        assert "Rule matches: 0" in prompt
    
    def test_get_summarization_prompt_with_rules(self):
        """Test summarization prompt with rules."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject", "from": "sender@example.com"}]
        rules = [
            {
                "name": "Work Rule",
                "type": "from_exact",
                "pattern": "boss@company.com",
                "priority": 90,
                "category": "work"
            }
        ]
        matches = [
            {"email_id": "1", "rule_id": "work-rule-1"}
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=matches
        )
        
        assert "Work Rule" in prompt
        assert "from_exact" in prompt
        assert "work" in prompt
        assert "work-rule-1" in prompt
    
    def test_get_summarization_prompt_with_few_shot(self):
        """Test summarization prompt with few-shot examples."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject", "from": "sender@example.com"}]
        rules = []
        matches = []
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=matches,
            few_shot=True
        )
        
        assert "Example" in prompt
        assert "15 unread invoices" in prompt
        assert "25 emails total" in prompt
        assert "42 emails analyzed" in prompt
    
    def test_get_summarization_prompt_no_few_shot(self):
        """Test summarization prompt without few-shot examples."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject", "from": "sender@example.com"}]
        rules = []
        matches = []
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=matches,
            few_shot=False
        )
        
        assert "Example" not in prompt
        assert "15 unread invoices" not in prompt
    
    def test_get_summarization_prompt_no_emails(self):
        """Test summarization prompt with no emails."""
        templates = PromptTemplates()
        
        emails = []
        rules = []
        matches = []
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=matches
        )
        
        assert "No emails in inbox to summarize" in prompt
    
    def test_get_summarization_prompt_multiple_emails(self):
        """Test summarization prompt with multiple emails."""
        templates = PromptTemplates()
        
        emails = [
            {"id": "1", "subject": "Test Subject 1", "from": "sender1@example.com"},
            {"id": "2", "subject": "Test Subject 2", "from": "sender2@example.com"},
            {"id": "3", "subject": "Test Subject 3", "from": "sender3@example.com"}
        ]
        rules = []
        matches = []
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=matches
        )
        
        assert "Total emails: 3" in prompt
        assert "Test Subject 1" in prompt
        assert "Test Subject 2" in prompt
        assert "Test Subject 3" in prompt
        assert "sender1@example.com" in prompt
        assert "sender2@example.com" in prompt
        assert "sender3@example.com" in prompt
    
    def test_get_summarization_prompt_with_rules_and_matches(self):
        """Test summarization prompt with rules and matches."""
        templates = PromptTemplates()
        
        emails = [
            {"id": "1", "subject": "Test Subject 1", "from": "sender1@example.com"},
            {"id": "2", "subject": "Test Subject 2", "from": "sender2@example.com"}
        ]
        rules = [
            {
                "name": "Work Rule",
                "type": "from_exact",
                "pattern": "boss@company.com",
                "priority": 90,
                "category": "work"
            },
            {
                "name": "Finance Rule",
                "type": "subject_contains",
                "pattern": "invoice",
                "priority": 80,
                "category": "finance"
            }
        ]
        matches = [
            {"email_id": "1", "rule_id": "work-rule-1"},
            {"email_id": "2", "rule_id": "finance-rule-1"}
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=matches
        )
        
        assert "Work Rule" in prompt
        assert "Finance Rule" in prompt
        assert "work-rule-1" in prompt
        assert "finance-rule-1" in prompt
        assert "2 emails" in prompt.lower()
        assert "2 emails matched" in prompt.lower()


class TestPromptTemplatesInboxSummarization:
    """Tests for PromptTemplates.inbox_summarization method."""
    
    def test_inbox_summarization_basic(self):
        """Test inbox summarization method."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject", "from": "sender@example.com"}]
        rules = []
        matches = []
        
        prompt = templates.inbox_summarization(
            emails=emails,
            rules=rules,
            matches=matches
        )
        
        assert "Total number of emails" in prompt
        assert "Test Subject" in prompt
        assert "sender@example.com" in prompt
        assert "categorized vs uncategorized" in prompt.lower()
        assert "recommendations" in prompt.lower()
    
    def test_inbox_summarization_with_rules(self):
        """Test inbox summarization with rules."""
        templates = PromptTemplates()
        
        emails = [{"id": "1", "subject": "Test Subject", "from": "sender@example.com"}]
        rules = [
            {
                "name": "Work Rule",
                "type": "from_exact",
                "pattern": "boss@company.com",
                "priority": 90,
                "category": "work"
            }
        ]
        matches = [
            {"email_id": "1", "rule_id": "work-rule-1"}
        ]
        
        prompt = templates.inbox_summarization(
            emails=emails,
            rules=rules,
            matches=matches
        )
        
        assert "Work Rule" in prompt
        assert "work-rule-1" in prompt
        assert "categorized vs uncategorized" in prompt.lower()


class TestPromptTemplatesFormatting:
    """Tests for email formatting utilities."""
    
    def test_format_emails_for_prompt_basic(self):
        """Test email formatting for prompts."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test Subject",
                "body": "Test body content",
                "date": "2024-01-15",
                "has_attachments": True
            }
        ]
        
        formatted = templates._format_emails_for_prompt(emails)
        
        assert "sender@example.com" in formatted
        assert "Test Subject" in formatted
        assert "Test body content" in formatted
        assert "2024-01-15" in formatted
        assert "has_attachments" in formatted.lower()
        assert "True" in formatted
    
    def test_format_emails_for_prompt_no_body(self):
        """Test email formatting without body."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test Subject",
                "date": "2024-01-15"
            }
        ]
        
        formatted = templates._format_emails_for_prompt(emails)
        
        assert "sender@example.com" in formatted
        assert "Test Subject" in formatted
        assert "No subject" in formatted
        assert "No body" in formatted
    
    def test_format_emails_for_prompt_truncated_body(self):
        """Test email formatting with truncated body."""
        templates = PromptTemplates()
        
        long_body = "A" * 300
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test Subject",
                "body": long_body,
                "date": "2024-01-15"
            }
        ]
        
        formatted = templates._format_emails_for_prompt(emails)
        
        assert "sender@example.com" in formatted
        assert "Test Subject" in formatted
        assert "..." in formatted
        assert len(formatted) < len(long_body)
    
    def test_format_emails_for_prompt_empty(self):
        """Test email formatting with empty list."""
        templates = PromptTemplates()
        
        formatted = templates._format_emails_for_prompt([])
        
        assert "No sample emails provided" in formatted
    
    def test_format_emails_for_prompt_limits_to_five(self):
        """Test that email formatting limits to 5 emails."""
        templates = PromptTemplates()
        
        emails = [
            {"id": str(i), "from": f"sender{i}@example.com", "subject": f"Subject {i}"}
            for i in range(10)
        ]
        
        formatted = templates._format_emails_for_prompt(emails)
        
        assert "Email 1" in formatted
        assert "Email 5" in formatted
        assert "Email 6" not in formatted
        assert "and 5 more emails" in formatted


class TestPromptTemplatesSpecialCharacters:
    """Tests for special character handling."""
    
    def test_get_rule_generation_prompt_special_characters(self):
        """Test rule generation prompt with special characters."""
        templates = PromptTemplates()
        
        description = "Create rule for 'test@example.com' with $100 invoice"
        sample_emails = []
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails
        )
        
        assert "test@example.com" in prompt
        assert "$100" in prompt
    
    def test_get_categorization_prompt_special_characters(self):
        """Test categorization prompt with special characters."""
        templates = PromptTemplates()
        
        emails = [
            {"id": "1", "subject": "Test 'Subject' with $100"}
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            existing_categories=["general"]
        )
        
        assert "Test 'Subject'" in prompt
        assert "$100" in prompt
    
    def test_get_summarization_prompt_special_characters(self):
        """Test summarization prompt with special characters."""
        templates = PromptTemplates()
        
        emails = [
            {"id": "1", "subject": "Test 'Subject' with $100"}
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[]
        )
        
        assert "Test 'Subject'" in prompt
        assert "$100" in prompt
    
    def test_get_rule_generation_prompt_unicode(self):
        """Test rule generation prompt with unicode characters."""
        templates = PromptTemplates()
        
        description = "Create rule for invoices from 日本公司"
        sample_emails = []
        
        prompt = templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails
        )
        
        assert "日本公司" in prompt
    
    def test_get_categorization_prompt_unicode(self):
        """Test categorization prompt with unicode characters."""
        templates = PromptTemplates()
        
        emails = [
            {"id": "1", "subject": "Meeting with 日本公司"}
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            existing_categories=["general"]
        )
        
        assert "日本公司" in prompt
    
    def test_get_summarization_prompt_unicode(self):
        """Test summarization prompt with unicode characters."""
        templates = PromptTemplates()
        
        emails = [
            {"id": "1", "subject": "Meeting with 日本公司"}
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[]
        )
        
        assert "日本公司" in prompt


class TestPromptTemplatesIntegration:
    """Integration tests for PromptTemplates with other components."""
    
    def test_full_rule_generation_flow(self):
        """Test complete rule generation prompt flow."""
        templates = PromptTemplates()
        
        sample_emails = [
            {
                "id": "1",
                "from": "billing@example.com",
                "subject": "Your Invoice #12345",
                "body": "Please find your invoice attached.",
                "date": "2024-01-15"
            }
        ]
        
        prompt = templates.get_rule_generation_prompt(
            description="Create rule for invoices",
            sample_emails=sample_emails
        )
        
        # Verify all components are present
        assert "Generate email rules" in prompt
        assert "billing@example.com" in prompt
        assert "Invoice #12345" in prompt
        assert "Example 1" in prompt
        assert "from_exact" in prompt.lower()
    
    def test_full_categorization_flow(self):
        """Test complete categorization prompt flow."""
        templates = PromptTemplates()
        
        rules = [
            {
                "name": "Work Rule",
                "type": "from_exact",
                "pattern": "boss@company.com",
                "priority": 90,
                "category": "work"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=[{"id": "1", "from": "boss@company.com", "subject": "Meeting"}],
            rules=rules,
            existing_categories=["work", "personal"]
        )
        
        # Verify all components are present
        assert "suggest categories" in prompt.lower()
        assert "boss@company.com" in prompt
        assert "Work Rule" in prompt
        assert "Example 1" in prompt
    
    def test_full_summarization_flow(self):
        """Test complete summarization prompt flow."""
        templates = PromptTemplates()
        
        matches = [
            {"email_id": "1", "rule_id": "work-rule-1"},
            {"email_id": "2", "rule_id": "finance-rule-1"}
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=[{"id": "1"}, {"id": "2"}],
            rules=[],
            matches=matches
        )
        
        # Verify all components are present
        assert "summarize inbox" in prompt.lower()
        assert "2 emails" in prompt
        assert "work-rule-1" in prompt
        assert "finance-rule-1" in prompt
        assert "Example 1" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
