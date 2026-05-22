"""Tests for the EmailCategorizer component."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from email_tool.agent.categorizer import EmailCategorizer
from email_tool.agent.llm_agent import LLMAgent
from email_tool.agent.base import AgentContext, AgentResult
from email_tool.models import Rule, RuleType


class TestEmailCategorizerInit:
    """Tests for EmailCategorizer initialization."""
    
    def test_init_default(self):
        """Test EmailCategorizer with default LLM agent."""
        categorizer = EmailCategorizer()
        
        assert categorizer.llm_agent is not None
        assert isinstance(categorizer.llm_agent, LLMAgent)
    
    def test_init_with_custom_agent(self):
        """Test EmailCategorizer with custom LLM agent."""
        custom_agent = LLMAgent(api_key="custom_key")
        categorizer = EmailCategorizer(llm_agent=custom_agent)
        
        assert categorizer.llm_agent == custom_agent


class TestEmailCategorizerCategorizeEmails:
    """Tests for EmailCategorizer.categorize_emails method."""
    
    def test_categorize_emails_success(self):
        """Test successful email categorization."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "email_id": "1",
                    "suggested_category": "invoices",
                    "confidence": 0.95,
                    "reason": "Contains invoice number"
                },
                {
                    "email_id": "2",
                    "suggested_category": "newsletters",
                    "confidence": 0.88,
                    "reason": "Contains newsletter content"
                }
            ],
            metadata={"processed_count": 2}
        )
        
        with patch.object(LLMAgent, 'suggest_categories', return_value=mock_result):
            categorizer = EmailCategorizer()
            
            result = categorizer.categorize_emails(
                emails=[
                    {"id": "1", "subject": "Invoice #123", "body": "Please pay invoice"},
                    {"id": "2", "subject": "Weekly Newsletter", "body": "Latest news"}
                ],
                existing_categories=["general", "personal"]
            )
            
            assert result.success is True
            assert len(result.data) == 2
            assert result.metadata["processed_count"] == 2
    
    def test_categorize_emails_empty_list(self):
        """Test handling of empty email list."""
        categorizer = EmailCategorizer()
        
        result = categorizer.categorize_emails(
            emails=[],
            existing_categories=["general"]
        )
        
        assert result.success is False
        assert "No emails provided" in result.error_message
    
    def test_categorize_emails_no_existing_categories(self):
        """Test categorization without existing categories."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "email_id": "1",
                    "suggested_category": "work",
                    "confidence": 0.90,
                    "reason": "Work-related content"
                }
            ],
            metadata={"processed_count": 1}
        )
        
        with patch.object(LLMAgent, 'suggest_categories', return_value=mock_result):
            categorizer = EmailCategorizer()
            
            result = categorizer.categorize_emails(
                emails=[{"id": "1", "subject": "Meeting", "body": "Team meeting"}],
                existing_categories=[]
            )
            
            assert result.success is True
            assert len(result.data) == 1
    
    def test_categorize_emails_low_confidence(self):
        """Test handling of low confidence categorizations."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "email_id": "1",
                    "suggested_category": "general",
                    "confidence": 0.35,
                    "reason": "Unclear content"
                }
            ],
            metadata={"processed_count": 1, "low_confidence_count": 1}
        )
        
        with patch.object(LLMAgent, 'suggest_categories', return_value=mock_result):
            categorizer = EmailCategorizer()
            
            result = categorizer.categorize_emails(
                emails=[{"id": "1", "subject": "Test", "body": "Test"}],
                existing_categories=["general"]
            )
            
            assert result.success is True
            assert "low_confidence_count" in result.metadata
            assert result.metadata["low_confidence_count"] == 1
    
    def test_categorize_emails_llm_error(self):
        """Test handling of LLM errors."""
        with patch.object(LLMAgent, 'suggest_categories') as mock_suggest:
            mock_suggest.side_effect = Exception("LLM Error")
            
            categorizer = EmailCategorizer()
            
            result = categorizer.categorize_emails(
                emails=[{"id": "1", "subject": "Test"}],
                existing_categories=["general"]
            )
            
            assert result.success is False
            assert "LLM Error" in result.error_message
    
    def test_categorize_emails_with_rules(self):
        """Test categorization with existing rules."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "email_id": "1",
                    "suggested_category": "invoices",
                    "confidence": 0.95,
                    "reason": "Matches invoice rule"
                }
            ],
            metadata={"processed_count": 1, "matched_rules": 1}
        )
        
        with patch.object(LLMAgent, 'suggest_categories', return_value=mock_result):
            categorizer = EmailCategorizer()
            
            result = categorizer.categorize_emails(
                emails=[{"id": "1", "subject": "Invoice #123", "body": "Please pay"}],
                existing_categories=["general"],
                rules=[
                    Rule(
                        name="Invoice Rule",
                        rule_type=RuleType.SUBJECT_CONTAINS,
                        pattern="invoice",
                        priority=80,
                        category="invoices"
                    )
                ]
            )
            
            assert result.success is True
            assert "matched_rules" in result.metadata


class TestEmailCategorizerPromptConstruction:
    """Tests for prompt construction in EmailCategorizer."""
    
    def test_construct_category_suggestion_prompt(self):
        """Test prompt construction for category suggestion."""
        categorizer = EmailCategorizer()
        
        prompt = categorizer._construct_category_suggestion_prompt(
            emails=[{"id": "1", "subject": "Meeting", "body": "Team meeting"}],
            existing_categories=["general", "work"]
        )
        
        assert "suggest categories" in prompt.lower()
        assert "existing categories" in prompt.lower()
        assert "JSON" in prompt
        assert "confidence" in prompt.lower()
    
    def test_construct_category_suggestion_prompt_no_existing(self):
        """Test prompt construction without existing categories."""
        categorizer = EmailCategorizer()
        
        prompt = categorizer._construct_category_suggestion_prompt(
            emails=[{"id": "1", "subject": "Meeting", "body": "Team meeting"}],
            existing_categories=[]
        )
        
        assert "suggest categories" in prompt.lower()
        assert "new categories" in prompt.lower()


class TestEmailCategorizerErrorHandling:
    """Tests for error handling in EmailCategorizer."""
    
    def test_categorize_emails_invalid_email_format(self):
        """Test handling of invalid email format."""
        categorizer = EmailCategorizer()
        
        result = categorizer.categorize_emails(
            emails=[{"id": "1"}],  # Missing subject and body
            existing_categories=["general"]
        )
        
        assert result.success is False
        assert "Invalid email format" in result.error_message
    
    def test_categorize_emails_timeout(self):
        """Test handling of timeout errors."""
        with patch.object(LLMAgent, 'suggest_categories') as mock_suggest:
            from requests.exceptions import Timeout
            mock_suggest.side_effect = Timeout("Request timed out")
            
            categorizer = EmailCategorizer()
            
            result = categorizer.categorize_emails(
                emails=[{"id": "1", "subject": "Test"}],
                existing_categories=["general"]
            )
            
            assert result.success is False
            assert "timeout" in result.error_message.lower()


class TestEmailCategorizerIntegration:
    """Integration tests for EmailCategorizer with other components."""
    
    def test_categorize_with_confidence_threshold(self):
        """Test categorization with confidence threshold."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "email_id": "1",
                    "suggested_category": "work",
                    "confidence": 0.95,
                    "reason": "Work-related"
                },
                {
                    "email_id": "2",
                    "suggested_category": "personal",
                    "confidence": 0.40,
                    "reason": "Unclear"
                }
            ],
            metadata={"processed_count": 2, "low_confidence_count": 1}
        )
        
        with patch.object(LLMAgent, 'suggest_categories', return_value=mock_result):
            categorizer = EmailCategorizer()
            
            result = categorizer.categorize_emails(
                emails=[
                    {"id": "1", "subject": "Meeting", "body": "Work meeting"},
                    {"id": "2", "subject": "Test", "body": "Test"}
                ],
                existing_categories=["general", "work", "personal"],
                confidence_threshold=0.75
            )
            
            assert result.success is True
            assert len(result.data) == 2
            assert result.metadata["low_confidence_count"] == 1
    
    def test_categorize_with_rules_integration(self):
        """Test categorization with rule integration."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "email_id": "1",
                    "suggested_category": "invoices",
                    "confidence": 0.95,
                    "reason": "Matches invoice rule"
                }
            ],
            metadata={"processed_count": 1, "matched_rules": 1}
        )
        
        with patch.object(LLMAgent, 'suggest_categories', return_value=mock_result):
            categorizer = EmailCategorizer()
            
            result = categorizer.categorize_emails(
                emails=[{"id": "1", "subject": "Invoice #123", "body": "Please pay"}],
                existing_categories=["general"],
                rules=[
                    Rule(
                        name="Invoice Rule",
                        rule_type=RuleType.SUBJECT_CONTAINS,
                        pattern="invoice",
                        priority=80,
                        category="invoices"
                    )
                ]
            )
            
            assert result.success is True
            assert "matched_rules" in result.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
