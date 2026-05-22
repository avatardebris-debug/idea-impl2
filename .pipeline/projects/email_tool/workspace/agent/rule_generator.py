"""Rule generator for email filtering rules."""

from typing import Any, Dict, List, Optional

from email_tool.agent.base import AgentContext, AgentResult
from email_tool.agent.llm_agent import LLMAgent
from email_tool.agent.rule_validator import RuleValidator
from email_tool.models import Rule


class RuleGenerator:
    """
    Generates email filtering rules from natural language descriptions.
    
    This class provides a high-level interface for rule generation,
    handling validation and error handling.
    """
    
    def __init__(self, llm_agent: Optional[LLMAgent] = None):
        """
        Initialize the rule generator.
        
        Args:
            llm_agent: Optional LLM agent instance. If not provided,
                      a default one will be created.
        """
        self.llm_agent = llm_agent or LLMAgent()
        self.rule_validator = RuleValidator()
    
    def generate_rules(
        self,
        description: str,
        sample_emails: List[Dict[str, Any]],
        context: Optional[AgentContext] = None,
        few_shot: bool = True,
        custom_prompt: Optional[str] = None
    ) -> AgentResult:
        """
        Generate rules from a natural language description.
        
        Args:
            description: Natural language description of rules to create.
            sample_emails: Sample emails to analyze for rule generation.
            context: Optional conversation context.
            few_shot: Whether to include few-shot examples.
            custom_prompt: Optional custom prompt template.
            
        Returns:
            AgentResult with generated rules or error information.
        """
        # Validate description
        if not description or not description.strip():
            return AgentResult(
                success=False,
                data=None,
                error_message="Description is required for rule generation",
                metadata={"conversation_id": context.conversation_id if context else None}
            )
        
        # Check for warnings
        warnings = []
        if not sample_emails:
            warnings.append("No sample emails provided")
            
        try:
            # Call LLM agent to generate rules
            result = self.llm_agent.generate_rules(
                description=description,
                sample_emails=sample_emails,
                context=context,
                few_shot=few_shot,
                custom_prompt=custom_prompt
            )
            
            if not result.success:
                result.metadata["warnings"] = warnings
                result.metadata["description"] = description
                return result
            
            # Validate generated rules
            validation_result = self.rule_validator.validate_rules(result.data)
            if not validation_result.success:
                return AgentResult(
                    success=False,
                    data=None,
                    error_message=f"Invalid rules: {validation_result.metadata.get('errors', [])}",
                    metadata={
                        "conversation_id": context.conversation_id if context else None,
                        "warnings": warnings,
                        "description": description
                    }
                )
            
            return AgentResult(
                success=True,
                data=result.data,
                metadata={
                    "conversation_id": context.conversation_id if context else None,
                    "rules_count": len(result.data),
                    "generated_count": len(result.data),
                    "warnings": warnings,
                    "description": description
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                error_message=f"Rule generation failed: {str(e)}",
                metadata={"conversation_id": context.conversation_id if context else None}
            )
