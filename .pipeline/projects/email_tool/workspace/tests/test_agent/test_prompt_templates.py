"""Tests for prompt templates."""

import pytest
from email_tool.agent.prompt_templates import PromptTemplates


class TestPromptTemplates:
    """Test cases for PromptTemplates class."""
    
    def test_get_rule_generation_prompt_basic(self):
        """Test basic rule generation prompt."""
        templates = PromptTemplates()
        
        prompt = templates.get_rule_generation_prompt(
            description="Create rules",
            sample_emails=[],
            few_shot=True
        )
        
        assert "create rules" in prompt.lower()
        assert "sample emails" in prompt.lower()
    
    def test_get_rule_generation_prompt_with_sample_emails(self):
        """Test rule generation prompt with sample emails."""
        templates = PromptTemplates()
        
        sample_emails = [
            {
                "from": "sender@example.com",
                "subject": "Test Subject",
                "date": "2024-01-01",
                "body": "Test body"
            }
        ]
        
        prompt = templates.get_rule_generation_prompt(
            description="Create rules",
            sample_emails=sample_emails,
            few_shot=True
        )
        
        assert "sender@example.com" in prompt
        assert "test subject" in prompt.lower()
    
    def test_get_rule_generation_prompt_without_few_shot(self):
        """Test rule generation prompt without few-shot examples."""
        templates = PromptTemplates()
        
        prompt = templates.get_rule_generation_prompt(
            description="Create rules",
            sample_emails=[],
            few_shot=False
        )
        
        assert "here are some examples" not in prompt.lower()
    
    def test_get_rule_generation_prompt_with_few_shot(self):
        """Test rule generation prompt with few-shot examples."""
        templates = PromptTemplates()
        
        prompt = templates.get_rule_generation_prompt(
            description="Create rules",
            sample_emails=[],
            few_shot=True
        )
        
        assert "here are some examples" in prompt.lower()
        assert "example" in prompt.lower()
    
    def test_get_rule_generation_prompt_with_custom_prompt(self):
        """Test rule generation prompt with custom prompt."""
        templates = PromptTemplates()
        
        custom_prompt = "Custom prompt for rule generation"
        
        prompt = templates.get_rule_generation_prompt(
            description="Create rules",
            sample_emails=[],
            few_shot=False,
            custom_prompt=custom_prompt
        )
        
        assert custom_prompt in prompt
    
    def test_get_categorization_prompt_basic(self):
        """Test basic categorization prompt."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "body": "Test body"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=[],
            few_shot=True
        )
        
        assert "sender@example.com" in prompt
        assert "test" in prompt.lower()
    
    def test_get_categorization_prompt_with_rules(self):
        """Test categorization prompt with rules."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "body": "Test body"
            }
        ]
        
        rules = [
            {
                "name": "work_rule",
                "type": "subject_contains",
                "pattern": "work",
                "priority": 80,
                "category": "work"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=rules,
            few_shot=True
        )
        
        assert "work_rule" in prompt
        assert "work" in prompt.lower()
    
    def test_get_categorization_prompt_with_existing_categories(self):
        """Test categorization prompt with existing categories."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "body": "Test body"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=[],
            few_shot=True,
            existing_categories=["work", "personal"]
        )
        
        assert "work" in prompt.lower()
        assert "personal" in prompt.lower()
    
    def test_get_categorization_prompt_without_few_shot(self):
        """Test categorization prompt without few-shot examples."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "body": "Test body"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=[],
            few_shot=False
        )
        
        assert "here are some examples" not in prompt.lower()
    
    def test_get_categorization_prompt_with_few_shot(self):
        """Test categorization prompt with few-shot examples."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "body": "Test body"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=[],
            few_shot=True
        )
        
        assert "here are some examples" in prompt.lower()
        assert "example" in prompt.lower()
    
    def test_get_categorization_prompt_with_custom_prompt(self):
        """Test categorization prompt with custom prompt."""
        templates = PromptTemplates()
        
        custom_prompt = "Custom prompt for categorization"
        
        prompt = templates.get_categorization_prompt(
            emails=[],
            rules=[],
            few_shot=False,
            custom_prompt=custom_prompt
        )
        
        assert custom_prompt in prompt
    
    def test_get_categorization_prompt_with_long_subject(self):
        """Test categorization prompt with long subject."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "This is a very long subject line that contains a lot of information and might be too long for a summary",
                "date": "2024-01-01",
                "body": "Test body"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=[],
            few_shot=True
        )
        
        assert "This is a very long subject line" in prompt
    
    def test_get_categorization_prompt_with_duplicate_emails(self):
        """Test categorization prompt with duplicate emails."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "body": "Test body"
            },
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "body": "Test body"
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=[],
            few_shot=True
        )
        
        assert "test" in prompt.lower()
    
    def test_get_categorization_prompt_with_none_values(self):
        """Test categorization prompt with None values."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": None,
                "from": None,
                "subject": None,
                "date": None,
                "body": None
            }
        ]
        
        prompt = templates.get_categorization_prompt(
            emails=emails,
            rules=[],
            few_shot=True
        )
        
        # None values are displayed as "none" in the prompt
        assert "none" in prompt.lower()
    
    def test_get_summarization_prompt_empty_emails(self):
        """Test summarization prompt with empty email list."""
        templates = PromptTemplates()
        
        prompt = templates.get_summarization_prompt(
            emails=[],
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "no emails in inbox" in prompt.lower()
    
    def test_get_summarization_prompt_with_emails(self):
        """Test summarization prompt with emails."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "sender@example.com" in prompt
        assert "test" in prompt.lower()
    
    def test_get_summarization_prompt_with_rules(self):
        """Test summarization prompt with rules."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        rules = [
            {
                "name": "work_rule",
                "type": "subject_contains",
                "pattern": "work",
                "priority": 80,
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=[],
            few_shot=True
        )
        
        assert "work_rule" in prompt
        assert "work" in prompt.lower()
    
    def test_get_summarization_prompt_with_matches(self):
        """Test summarization prompt with matches."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        matches = [
            {
                "email_id": "1",
                "rule_name": "work_rule",
                "confidence": 0.95
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=matches,
            few_shot=True
        )
        
        # The prompt includes matches summary
        assert "work_rule" in prompt
        assert "0.95" in prompt
    
    def test_get_summarization_prompt_without_few_shot(self):
        """Test summarization prompt without few-shot examples."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=False
        )
        
        assert "here are some examples" not in prompt.lower()
    
    def test_get_summarization_prompt_with_few_shot(self):
        """Test summarization prompt with few-shot examples."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "here are some examples" in prompt.lower()
        assert "example" in prompt.lower()
    
    def test_get_summarization_prompt_with_custom_prompt(self):
        """Test summarization prompt with custom prompt."""
        templates = PromptTemplates()
        
        custom_prompt = "Custom prompt for summarization"
        
        prompt = templates.get_summarization_prompt(
            emails=[{"id": "1"}],
            rules=[],
            matches=[],
            few_shot=False,
            custom_prompt=custom_prompt
        )
        
        assert custom_prompt in prompt
    
    def test_get_summarization_prompt_with_multiple_emails(self):
        """Test summarization prompt with multiple emails."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender1@example.com",
                "subject": "Test 1",
                "date": "2024-01-01",
                "category": "work"
            },
            {
                "id": "2",
                "from": "sender2@example.com",
                "subject": "Test 2",
                "date": "2024-01-02",
                "category": "personal"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "sender1@example.com" in prompt
        assert "sender2@example.com" in prompt
    
    def test_get_summarization_prompt_with_multiple_rules(self):
        """Test summarization prompt with multiple rules."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        rules = [
            {
                "name": "work_rule",
                "type": "subject_contains",
                "pattern": "work",
                "priority": 80,
                "category": "work"
            },
            {
                "name": "personal_rule",
                "type": "subject_contains",
                "pattern": "personal",
                "priority": 70,
                "category": "personal"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=rules,
            matches=[],
            few_shot=True
        )
        
        assert "work_rule" in prompt
        assert "personal_rule" in prompt
    
    def test_get_summarization_prompt_with_multiple_matches(self):
        """Test summarization prompt with multiple matches."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        matches = [
            {
                "email_id": "1",
                "rule_name": "work_rule",
                "confidence": 0.95
            },
            {
                "email_id": "1",
                "rule_name": "personal_rule",
                "confidence": 0.85
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=matches,
            few_shot=True
        )
        
        assert "work_rule" in prompt
        assert "personal_rule" in prompt
    
    def test_get_summarization_prompt_with_empty_subject(self):
        """Test summarization prompt with empty subject."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "work" in prompt.lower()
    
    def test_get_summarization_prompt_with_empty_body(self):
        """Test summarization prompt with empty body."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test Subject",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "test subject" in prompt.lower()
    
    def test_get_summarization_prompt_with_special_characters(self):
        """Test summarization prompt with special characters."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test with special chars: @#$%",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "@#$%" in prompt
    
    def test_get_summarization_prompt_with_unicode_characters(self):
        """Test summarization prompt with unicode characters."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test with unicode: 你好 🌍",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "你好" in prompt
        assert "🌍" in prompt
    
    def test_get_summarization_prompt_with_long_subject(self):
        """Test summarization prompt with long subject."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "This is a very long subject line that contains a lot of information and might be too long for a summary",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "This is a very long subject line" in prompt
    
    def test_get_summarization_prompt_with_duplicate_emails(self):
        """Test summarization prompt with duplicate emails."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            },
            {
                "id": "1",
                "from": "sender@example.com",
                "subject": "Test",
                "date": "2024-01-01",
                "category": "work"
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        assert "test" in prompt.lower()
    
    def test_get_summarization_prompt_with_none_values(self):
        """Test summarization prompt with None values."""
        templates = PromptTemplates()
        
        emails = [
            {
                "id": None,
                "from": None,
                "subject": None,
                "date": None,
                "category": None
            }
        ]
        
        prompt = templates.get_summarization_prompt(
            emails=emails,
            rules=[],
            matches=[],
            few_shot=True
        )
        
        # None values are displayed as "none" in the prompt
        assert "none" in prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
