"""Tests for the RuleGenerator component."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from email_tool.agent.rule_generator import RuleGenerator
from email_tool.agent.llm_agent import LLMAgent
from email_tool.agent.base import AgentContext, AgentResult
from email_tool.agent.rule_validator import RuleValidator
from email_tool.models import Rule, RuleType


class TestRuleGeneratorInit:
    """Tests for RuleGenerator initialization."""
    
    def test_init_default(self):
        """Test RuleGenerator with default LLM agent."""
        generator = RuleGenerator()
        
        assert generator.llm_agent is not None
        assert isinstance(generator.llm_agent, LLMAgent)
    
    def test_init_with_custom_agent(self):
        """Test RuleGenerator with custom LLM agent."""
        custom_agent = LLMAgent(api_key="custom_key")
        generator = RuleGenerator(llm_agent=custom_agent)
        
        assert generator.llm_agent == custom_agent


class TestRuleGeneratorGenerateRules:
    """Tests for RuleGenerator.generate_rules method."""
    
    def test_generate_rules_success(self):
        """Test successful rule generation."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "name": "Test Rule",
                    "type": "from_exact",
                    "pattern": "sender@example.com",
                    "priority": 75,
                    "category": "important"
                }
            ],
            metadata={"generated_count": 1}
        )
        
        with patch.object(LLMAgent, 'generate_rules', return_value=mock_result):
            generator = RuleGenerator()
            
            result = generator.generate_rules(
                description="Create rule for sender@example.com",
                sample_emails=[]
            )
            
            assert result.success is True
            assert len(result.data) == 1
            assert result.metadata["generated_count"] == 1
    
    def test_generate_rules_empty_description(self):
        """Test handling of empty description."""
        generator = RuleGenerator()
        
        result = generator.generate_rules(
            description="",
            sample_emails=[]
        )
        
        assert result.success is False
        assert "Description is required" in result.error_message
    
    def test_generate_rules_no_sample_emails(self):
        """Test rule generation without sample emails."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "name": "Test Rule",
                    "type": "from_exact",
                    "pattern": "sender@example.com",
                    "priority": 75,
                    "category": "important"
                }
            ],
            metadata={"warnings": ["No sample emails provided"]}
        )
        
        with patch.object(LLMAgent, 'generate_rules', return_value=mock_result):
            generator = RuleGenerator()
            
            result = generator.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            assert result.success is True
            assert "warnings" in result.metadata
    
    def test_generate_rules_with_sample_emails(self):
        """Test rule generation with sample emails."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "name": "Invoice Rule",
                    "type": "subject_contains",
                    "pattern": "invoice",
                    "priority": 80,
                    "category": "finance"
                }
            ],
            metadata={"generated_count": 1}
        )
        
        sample_emails = [
            {
                "id": "1",
                "from": "billing@example.com",
                "subject": "Your Invoice #12345",
                "body": "Please find your invoice attached.",
                "date": "2024-01-15"
            }
        ]
        
        with patch.object(LLMAgent, 'generate_rules', return_value=mock_result):
            generator = RuleGenerator()
            
            result = generator.generate_rules(
                description="Create rule for invoices",
                sample_emails=sample_emails
            )
            
            assert result.success is True
            assert len(result.data) == 1
            assert result.data[0]["pattern"] == "invoice"
    
    def test_generate_rules_validation_failure(self):
        """Test handling of validation failures."""
        mock_result = AgentResult(
            success=False,
            error_message="Invalid rule format",
            metadata={"errors": ["Invalid rule type"]}
        )
        
        with patch.object(LLMAgent, 'generate_rules', return_value=mock_result):
            generator = RuleGenerator()
            
            result = generator.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            assert result.success is False
            assert "Invalid rule format" in result.error_message
            assert "errors" in result.metadata
    
    def test_generate_rules_strict_mode(self):
        """Test strict mode validation."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "name": "Invalid Rule",
                    "type": "invalid_type",
                    "pattern": "test",
                    "priority": 150,
                    "category": "test"
                }
            ],
            metadata={"generated_count": 1}
        )
        
        with patch.object(LLMAgent, 'generate_rules', return_value=mock_result):
            generator = RuleGenerator(strict_mode=True)
            
            result = generator.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            assert result.success is False
            assert "Validation failed" in result.error_message


class TestRuleGeneratorValidateRules:
    """Tests for RuleGenerator._validate_rules method."""
    
    def test_validate_rules_success(self):
        """Test successful validation."""
        rules = [
            {
                "name": "Valid Rule",
                "type": "from_exact",
                "pattern": "sender@example.com",
                "priority": 75,
                "category": "important"
            }
        ]
        
        generator = RuleGenerator()
        result = generator._validate_rules(rules)
        
        assert result.success is True
        assert len(result.data) == 1
    
    def test_validate_rules_invalid_type(self):
        """Test validation of invalid rule type."""
        rules = [
            {
                "name": "Invalid Rule",
                "type": "invalid_type",
                "pattern": "test",
                "priority": 75,
                "category": "test"
            }
        ]
        
        generator = RuleGenerator()
        result = generator._validate_rules(rules)
        
        assert result.success is False
        assert "Invalid rule type" in result.error_message
    
    def test_validate_rules_invalid_priority(self):
        """Test validation of invalid priority."""
        rules = [
            {
                "name": "Invalid Rule",
                "type": "from_exact",
                "pattern": "sender@example.com",
                "priority": 150,
                "category": "test"
            }
        ]
        
        generator = RuleGenerator()
        result = generator._validate_rules(rules)
        
        assert result.success is False
        assert "Priority must be between 0 and 100" in result.error_message
    
    def test_validate_rules_missing_fields(self):
        """Test validation of missing required fields."""
        rules = [
            {
                "name": "Incomplete Rule",
                "type": "from_exact"
                # Missing pattern, priority, category
            }
        ]
        
        generator = RuleGenerator()
        result = generator._validate_rules(rules)
        
        assert result.success is False
        assert "Missing required fields" in result.error_message
    
    def test_validate_rules_empty_list(self):
        """Test validation of empty rule list."""
        generator = RuleGenerator()
        result = generator._validate_rules([])
        
        assert result.success is False
        assert "No rules provided" in result.error_message


class TestRuleGeneratorPromptConstruction:
    """Tests for prompt construction in RuleGenerator."""
    
    def test_construct_rule_generation_prompt(self):
        """Test prompt construction for rule generation."""
        generator = RuleGenerator()
        
        prompt = generator._construct_rule_generation_prompt(
            description="Create rule for invoices",
            sample_emails=[
                {"id": "1", "subject": "Invoice #123", "body": "Please pay invoice"}
            ]
        )
        
        assert "Generate email rules" in prompt
        assert "invoice" in prompt.lower()
        assert "JSON" in prompt
        assert "from_exact" in prompt.lower()
        assert "subject_contains" in prompt.lower()
    
    def test_construct_rule_generation_prompt_no_samples(self):
        """Test prompt construction without sample emails."""
        generator = RuleGenerator()
        
        prompt = generator._construct_rule_generation_prompt(
            description="Create rule for invoices",
            sample_emails=[]
        )
        
        assert "Generate email rules" in prompt
        assert "No sample emails provided" in prompt


class TestRuleGeneratorErrorHandling:
    """Tests for error handling in RuleGenerator."""
    
    def test_generate_rules_llm_error(self):
        """Test handling of LLM errors."""
        with patch.object(LLMAgent, 'generate_rules') as mock_generate:
            mock_generate.side_effect = Exception("LLM Error")
            
            generator = RuleGenerator()
            
            result = generator.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            assert result.success is False
            assert "LLM Error" in result.error_message
    
    def test_generate_rules_timeout(self):
        """Test handling of timeout errors."""
        with patch.object(LLMAgent, 'generate_rules') as mock_generate:
            from requests.exceptions import Timeout
            mock_generate.side_effect = Timeout("Request timed out")
            
            generator = RuleGenerator()
            
            result = generator.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            assert result.success is False
            assert "timeout" in result.error_message.lower()


class TestRuleGeneratorIntegration:
    """Integration tests for RuleGenerator with other components."""
    
    def test_generate_rules_with_validation_integration(self):
        """Test rule generation with validation integration."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "name": "Valid Rule",
                    "type": "from_exact",
                    "pattern": "valid@example.com",
                    "priority": 75,
                    "category": "important"
                }
            ],
            metadata={"generated_count": 1}
        )
        
        with patch.object(LLMAgent, 'generate_rules', return_value=mock_result):
            generator = RuleGenerator()
            
            result = generator.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            # Validate the generated rules
            validator = RuleValidator()
            validation_result = validator.validate_rules(result.data)
            
            assert validation_result.success is True
            assert len(validation_result.data) == 1
    
    def test_generate_rules_with_strict_validation_integration(self):
        """Test strict validation mode integration."""
        mock_result = AgentResult(
            success=True,
            data=[
                {
                    "name": "Invalid Rule",
                    "type": "invalid_type",
                    "pattern": "test",
                    "priority": 150,
                    "category": "test"
                }
            ],
            metadata={"generated_count": 1}
        )
        
        with patch.object(LLMAgent, 'generate_rules', return_value=mock_result):
            generator = RuleGenerator(strict_mode=True)
            
            result = generator.generate_rules(
                description="Create rule",
                sample_emails=[]
            )
            
            # In strict mode, should fail on validation errors
            assert result.success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
