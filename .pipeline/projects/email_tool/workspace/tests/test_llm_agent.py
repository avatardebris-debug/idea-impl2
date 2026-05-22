"""Tests for LLMAgent."""

import json
import os
from unittest.mock import Mock, patch

import pytest

from email_tool.agent.base import AgentContext
from email_tool.agent.llm_agent import LLMAgent
from email_tool.agent.rule_validator import RuleValidator


class TestLLMAgentInit:
    """Tests for LLMAgent initialization."""
    
    def test_init_default(self):
        """Test LLMAgent with default configuration."""
        agent = LLMAgent()
        
        assert agent.model == "gpt-4o-mini"
        assert agent.temperature == 0.7
        assert agent.max_tokens == 2000
        assert agent.enable_few_shot is True
        assert agent.provider == "openai"
        # api_key can be None (falls back to environment variable)
    
    def test_init_with_custom_params(self):
        """Test LLMAgent with custom configuration."""
        config = {
            "model": "ollama/llama2",
            "temperature": 0.5,
            "max_tokens": 1000,
            "enable_few_shot": False,
            "api_key": "test_key",
            "provider": "ollama"
        }
        
        agent = LLMAgent(config=config)
        
        assert agent.model == "ollama/llama2"
        assert agent.temperature == 0.5
        assert agent.max_tokens == 1000
        assert agent.enable_few_shot is False
        assert agent.api_key == "test_key"
        assert agent.provider == "ollama"
    
    def test_init_uses_kwargs_over_config(self):
        """Test that kwargs override config."""
        config = {
            "model": "config_model",
            "temperature": 0.5
        }
        
        agent = LLMAgent(
            config=config,
            model="kwargs_model",
            temperature=0.9
        )
        
        assert agent.model == "kwargs_model"
        assert agent.temperature == 0.9


class TestLLMAgentGenerateRules:
    """Tests for LLMAgent.generate_rules method."""
    
    def test_generate_rules_success(self):
        """Test successful rule generation."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "name": "Test Rule",
                            "type": "from_exact",
                            "pattern": "sender@example.com",
                            "priority": 80,
                            "category": "important"
                        }
                    ])
                }
            }]
        }
        
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps([
            {
                "name": "Test Rule",
                "type": "from_exact",
                "pattern": "sender@example.com",
                "priority": 80,
                "category": "important"
            }
        ])):
            agent = LLMAgent()
            
            result = agent.generate_rules(
                description="Create a rule for sender@example.com",
                sample_emails=[]
            )
            
            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["name"] == "Test Rule"
            assert result.data[0]["type"] == "from_exact"
    
    def test_generate_rules_empty_response(self):
        """Test handling of empty LLM response."""
        mock_response = {"choices": [{"message": {"content": ""}}]}
        
        with patch.object(LLMAgent, '_call_llm', return_value=mock_response):
            agent = LLMAgent()
            
            result = agent.generate_rules(
                description="Test",
                sample_emails=[]
            )
            
            assert result.success is False
            assert "No rules generated" in result.error_message
    
    def test_generate_rules_invalid_json(self):
        """Test handling of invalid JSON response."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": "This is not valid JSON"
                }
            }]
        }
        
        with patch.object(LLMAgent, '_call_llm', return_value=mock_response):
            agent = LLMAgent()
            
            result = agent.generate_rules(
                description="Test",
                sample_emails=[]
            )
            
            assert result.success is False
            assert "Invalid JSON" in result.error_message
    
    def test_generate_rules_with_sample_emails(self):
        """Test rule generation with sample emails."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "name": "Invoice Rule",
                            "type": "subject_contains",
                            "pattern": "invoice",
                            "priority": 80,
                            "category": "finance"
                        }
                    ])
                }
            }]
        }
        
        sample_emails = [
            {
                "id": "1",
                "from": "billing@example.com",
                "subject": "Your Invoice #12345",
                "body": "Please find your invoice attached.",
                "date": "2024-01-15"
            }
        ]
        
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps([
            {
                "name": "Invoice Rule",
                "type": "subject_contains",
                "pattern": "invoice",
                "priority": 80,
                "category": "finance"
            }
        ])):
            agent = LLMAgent()
            
            result = agent.generate_rules(
                description="Create rule for invoices",
                sample_emails=sample_emails
            )
            
            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["pattern"] == "invoice"
    
    def test_generate_rules_validation_errors(self):
        """Test that validation errors are captured in metadata."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "name": "Invalid Rule",
                            "type": "invalid_type",
                            "pattern": "test",
                            "priority": 150
                        }
                    ])
                }
            }]
        }
        
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps([
            {
                "name": "Invalid Rule",
                "type": "invalid_type",
                "pattern": "test",
                "priority": 150
            }
        ])):
            agent = LLMAgent()
            
            result = agent.generate_rules(
                description="Test",
                sample_emails=[]
            )
            
            assert result.success is False
            assert "errors" in result.metadata
            assert len(result.metadata["errors"]) > 0


class TestLLMAgentSuggestCategories:
    """Tests for LLMAgent.suggest_categories method."""
    
    def test_suggest_categories_success(self):
        """Test successful category suggestion."""
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps([
            {
                "email_id": "1",
                "suggested_category": "invoices",
                "confidence": 0.95
            }
        ])):
            agent = LLMAgent()
            
            result = agent.suggest_categories(
                emails=[{"id": "1", "subject": "Invoice #123"}],
                existing_categories=["general", "personal"]
            )
            
            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["suggested_category"] == "invoices"
    
    def test_suggest_categories_no_emails(self):
        """Test handling of empty email list."""
        agent = LLMAgent()
        
        result = agent.suggest_categories(
            emails=[],
            existing_categories=["general"]
        )
        
        assert result.success is False
        assert "No emails provided" in result.error_message
    
    def test_suggest_categories_with_rules(self):
        """Test category suggestion with existing rules."""
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps([
            {
                "email_id": "1",
                "suggested_category": "work",
                "confidence": 0.85
            }
        ])):
            agent = LLMAgent()
            
            rules = [
                {
                    "name": "Work Rule",
                    "type": "from_exact",
                    "pattern": "boss@company.com",
                    "priority": 90,
                    "category": "work"
                }
            ]
            
            result = agent.suggest_categories(
                emails=[{"id": "1", "from": "boss@company.com", "subject": "Meeting"}],
                rules=rules,
                existing_categories=["work", "personal"]
            )
            
            assert result.success is True
            assert len(result.data) == 1
    
    def test_suggest_categories_invalid_json(self):
        """Test handling of invalid JSON response."""
        with patch.object(LLMAgent, '_call_llm', return_value="This is not valid JSON"):
            agent = LLMAgent()
            
            result = agent.suggest_categories(
                emails=[{"id": "1", "subject": "Test"}]
            )
            
            assert result.success is False
            assert "Invalid JSON" in result.error_message
    
    def test_suggest_categories_empty_categorizations(self):
        """Test handling of empty categorizations in response."""
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps({"categorizations": []})):
            agent = LLMAgent()
            
            result = agent.suggest_categories(
                emails=[{"id": "1", "subject": "Test"}]
            )
            
            assert result.success is True
            assert result.data == []
    
    def test_suggest_categories_with_context(self):
        """Test category suggestion with conversation context."""
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps([
            {
                "email_id": "1",
                "suggested_category": "personal",
                "confidence": 0.90
            }
        ])):
            agent = LLMAgent()
            
            context = AgentContext(conversation_id="conv-123")
            
            result = agent.suggest_categories(
                emails=[{"id": "1", "subject": "Lunch"}],
                context=context
            )
            
            assert result.success is True
            assert result.metadata["conversation_id"] == "conv-123"


class TestLLMAgentSummarizeInbox:
    """Tests for LLMAgent.summarize_inbox method."""
    
    def test_summarize_inbox_success(self):
        """Test successful inbox summarization."""
        with patch.object(LLMAgent, '_call_llm', return_value="You have 50 emails. 30 invoices, 20 newsletters. 5 unclassified."):
            agent = LLMAgent()
            
            result = agent.summarize_inbox(
                emails=[{"id": str(i)} for i in range(50)],
                rules=[],
                matches=[]
            )
            
            assert result.success is True
            assert "50 emails" in result.data
    
    def test_summarize_inbox_empty(self):
        """Test summarization with no emails."""
        agent = LLMAgent()
        
        result = agent.summarize_inbox(
            emails=[],
            rules=[],
            matches=[]
        )
        
        assert result.success is True
        assert "No emails" in result.data


class TestLLMAgentCallLLM:
    """Tests for LLMAgent._call_llm internal method."""
    
    def test_call_llm_success(self):
        """Test successful LLM call."""
        with patch('requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                json=lambda: {"choices": [{"message": {"content": "test"}}]}
            )
            
            agent = LLMAgent(api_key="test_key")
            
            result = agent._call_llm(
                messages=[{"role": "user", "content": "test"}],
                temperature=0.7
            )
            
            assert result is not None
            assert "choices" in result
    
    def test_call_llm_api_error(self):
        """Test handling of API errors."""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            agent = LLMAgent(api_key="test_key")
            
            with pytest.raises(Exception):
                agent._call_llm(
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7
                )
    
    def test_call_llm_rate_limit(self):
        """Test handling of rate limit errors."""
        with patch('requests.post') as mock_post:
            mock_response = Mock(status_code=429)
            mock_post.return_value = mock_response
            
            agent = LLMAgent(api_key="test_key")
            
            with pytest.raises(Exception):
                agent._call_llm(
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7
                )


class TestLLMAgentPromptConstruction:
    """Tests for prompt construction in LLMAgent."""
    
    def test_construct_rule_generation_prompt(self):
        """Test prompt construction for rule generation."""
        agent = LLMAgent()
        
        prompt = agent._get_rule_generation_prompt(
            description="Create rule for invoices",
            sample_emails=[
                {"id": "1", "subject": "Invoice #123", "body": "Please pay invoice"}
            ]
        )
        
        assert "Generate email rules" in prompt
        assert "invoice" in prompt.lower()
        assert "JSON" in prompt
    
    def test_construct_category_suggestion_prompt(self):
        """Test prompt construction for category suggestion."""
        agent = LLMAgent()
        
        prompt = agent._get_categorization_prompt(
            emails=[{"id": "1", "subject": "Meeting"}],
            existing_categories=["general", "work"]
        )
        
        assert "suggest categories" in prompt.lower()
        assert "existing categories" in prompt.lower()


class TestLLMAgentIntegration:
    """Integration tests for LLMAgent with other components."""
    
    def test_generate_rules_with_validation(self):
        """Test rule generation with validation enabled."""
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps([
            {
                "name": "Valid Rule",
                "type": "from_exact",
                "pattern": "valid@example.com",
                "priority": 75,
                "category": "important"
            }
        ])):
            agent = LLMAgent()
            
            result = agent.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            # Validate the generated rules
            validator = RuleValidator()
            validation_result = validator.validate_rules(result.data)
            
            assert validation_result.success is True
            assert len(validation_result.data) == 1
    
    def test_generate_rules_strict_validation(self):
        """Test strict validation mode."""
        with patch.object(LLMAgent, '_call_llm', return_value=json.dumps([
            {
                "name": "Invalid Rule",
                "type": "invalid_type",
                "pattern": "test",
                "priority": 150
            }
        ])):
            agent = LLMAgent()
            
            result = agent.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            # In strict mode, should fail on validation errors
            assert result.success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
