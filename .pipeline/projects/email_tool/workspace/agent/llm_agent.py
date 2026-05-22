"""LLM-powered agent implementation for email processing."""

import json
import os
from typing import Any, Dict, List, Optional

from email_tool.agent.base import AbstractAgent, AgentContext, AgentResult
from email_tool.agent.rule_validator import RuleValidator
from email_tool.agent.prompt_templates import PromptTemplates
from email_tool.models import Rule


class LLMAgent(AbstractAgent):
    """
    LLM-powered agent for email processing.
    
    This agent uses an LLM (OpenAI or Ollama) to:
    - Generate rules from natural language descriptions
    - Suggest categories for uncategorized emails
    - Summarize inbox organization status
    
    Configuration supports multiple providers and can be disabled.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize the LLM agent.
        
        Args:
            config: Agent configuration including provider settings.
            **kwargs: Additional configuration parameters.
        """
        super().__init__(config)
        
        # Extract parameters from kwargs or config
        self.model = kwargs.get("model", config.get("model", "gpt-4o-mini")) if config else kwargs.get("model", "gpt-4o-mini")
        self.temperature = kwargs.get("temperature", config.get("temperature", 0.7)) if config else kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", config.get("max_tokens", 2000)) if config else kwargs.get("max_tokens", 2000)
        self.enable_few_shot = kwargs.get("enable_few_shot", config.get("enable_few_shot", True)) if config else kwargs.get("enable_few_shot", True)
        self.api_key = kwargs.get("api_key", config.get("api_key")) if config else kwargs.get("api_key")
        self.provider = kwargs.get("provider", config.get("provider", "openai")) if config else kwargs.get("provider", "openai")
        
        # Initialize prompt templates
        self.prompt_templates = PromptTemplates()
        
        # Initialize rule validator
        self.rule_validator = RuleValidator()
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """Return the capabilities of this agent."""
        return [
            {
                "name": "generate_rules",
                "description": "Generate email filtering rules from natural language descriptions",
                "parameters": ["description", "sample_emails", "context", "few_shot", "custom_prompt"]
            },
            {
                "name": "categorize_emails",
                "description": "Categorize emails using LLM-based analysis",
                "parameters": ["emails", "rules", "context", "prompt", "few_shot", "existing_categories"]
            },
            {
                "name": "summarize_inbox",
                "description": "Summarize inbox organization status",
                "parameters": ["emails", "rules", "matches", "context", "prompt", "few_shot"]
            }
        ]
    
    def suggest_categories(
        self,
        emails: List[Dict[str, Any]],
        rules: List[Dict[str, Any]] = None,
        context: Optional[AgentContext] = None,
        prompt: Optional[str] = None,
        few_shot: bool = True,
        existing_categories: Optional[List[str]] = None
    ) -> AgentResult:
        """
        Suggest categories for emails based on LLM analysis.
        
        Args:
            emails: Emails to categorize.
            rules: Existing rules to consider (optional).
            context: Optional conversation context.
            prompt: Optional custom prompt.
            few_shot: Whether to include few-shot examples.
            existing_categories: List of existing categories.
            
        Returns:
            AgentResult with category suggestions.
        """
        # Handle empty emails
        if not emails:
            return AgentResult(
                success=False,
                data=None,
                error_message="No emails provided for categorization",
                metadata={"conversation_id": context.conversation_id if context else None}
            )
        
        # Default rules to empty list if not provided
        if rules is None:
            rules = []
        
        # If no rules, return default categorization without calling LLM
        if not rules:
            categorizations = []
            for email in emails:
                email_id = email.get("id", email.get("email_id", "unknown"))
                categorizations.append({
                    "email_id": email_id,
                    "category": "uncategorized",
                    "confidence": 0.5,
                    "matched_rule": None
                })
            
            return AgentResult(
                success=True,
                data=categorizations,
                metadata={
                    "conversation_id": context.conversation_id if context else None,
                    "emails_processed": len(emails),
                    "reason": "No rules provided, all emails marked as uncategorized"
                }
            )
        
        try:
            # Generate prompt
            prompt_text = self._get_categorization_prompt(
                emails=emails,
                rules=rules,
                context=context,
                prompt=prompt,
                few_shot=few_shot,
                existing_categories=existing_categories
            )
            
            # Call LLM
            response = self._call_llm(prompt_text)
            
            # Parse JSON response
            try:
                data = json.loads(response)
                # Handle both list format and dict with categorizations key
                if isinstance(data, list):
                    categorizations = data
                elif isinstance(data, dict):
                    categorizations = data.get("categorizations", [])
                else:
                    categorizations = []
            except json.JSONDecodeError as e:
                return AgentResult(
                    success=False,
                    error_message=f"Invalid JSON response: {str(e)}",
                    metadata={"conversation_id": context.conversation_id if context else None}
                )
            
            return AgentResult(
                success=True,
                data=categorizations,
                metadata={
                    "conversation_id": context.conversation_id if context else None,
                    "emails_processed": len(emails)
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                error_message=f"Category suggestion failed: {str(e)}",
                metadata={"conversation_id": context.conversation_id if context else None}
            )
    
    def _get_api_key(self) -> str:
        """Get API key from environment or config."""
        if self.api_key:
            return self.api_key
        return os.getenv("OPENAI_API_KEY", "")
    
    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None, messages: Optional[List[Dict[str, str]]] = None, temperature: Optional[float] = None) -> str:
        """
        Call the LLM API.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt.
            messages: Optional list of message dicts for direct API call.
            temperature: Optional temperature override.
            
        Returns:
            The LLM response.
            
        Raises:
            Exception: If the LLM call fails.
        """
        # Check if LLM is disabled
        if not self.model or self.model.lower() == "disabled":
            raise Exception("LLM is disabled")
        
        # For testing, return a mock response
        if hasattr(self, '_mock_response'):
            return self._mock_response
        
        # Import here to avoid circular imports
        from email_tool.llm import LLMClient
        
        client = LLMClient(
            provider=self.provider,
            model=self.model,
            api_key=self._get_api_key()
        )
        
        # Use messages if provided, otherwise construct from prompt
        if messages:
            chat_messages = messages
        else:
            chat_messages = [
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        
        response = client.chat(
            messages=chat_messages,
            temperature=temperature or self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response
    
    def _get_rule_generation_prompt(
        self,
        description: str,
        sample_emails: List[Dict[str, Any]],
        context: Optional[AgentContext] = None,
        few_shot: bool = True,
        custom_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a prompt for rule generation.
        
        Args:
            description: Natural language description of rules to create.
            sample_emails: Sample emails to analyze.
            context: Optional conversation context.
            few_shot: Whether to include few-shot examples.
            custom_prompt: Optional custom prompt template.
            
        Returns:
            The formatted prompt.
        """
        if custom_prompt:
            return custom_prompt
        
        return self.prompt_templates.get_rule_generation_prompt(
            description=description,
            sample_emails=sample_emails
        )
    
    def _get_categorization_prompt(
        self,
        emails: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        context: Optional[AgentContext] = None,
        prompt: Optional[str] = None,
        few_shot: bool = True,
        existing_categories: Optional[List[str]] = None
    ) -> str:
        """
        Generate a prompt for email categorization.
        
        Args:
            emails: Emails to categorize.
            rules: Existing rules to consider.
            context: Optional conversation context.
            prompt: Optional custom prompt.
            few_shot: Whether to include few-shot examples.
            existing_categories: List of existing categories.
            
        Returns:
            The formatted prompt.
        """
        if prompt:
            return prompt
        
        return self.prompt_templates.get_categorization_prompt(
            emails=emails,
            existing_categories=existing_categories or []
        )
    
    def _get_summarization_prompt(
        self,
        emails: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        matches: List[Dict[str, Any]],
        context: Optional[AgentContext] = None,
        prompt: Optional[str] = None,
        few_shot: bool = True
    ) -> str:
        """
        Generate a prompt for inbox summarization.
        
        Args:
            emails: Emails to summarize.
            rules: Rules that matched emails.
            matches: Rule-match information.
            context: Optional conversation context.
            prompt: Optional custom prompt.
            few_shot: Whether to include few-shot examples.
            
        Returns:
            The formatted prompt.
        """
        if prompt:
            return prompt
        
        return self.prompt_templates.inbox_summarization(
            emails=emails,
            rules=rules,
            matches=matches,
            few_shot=few_shot and self.enable_few_shot
        )
    
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
            prompt: Optional custom prompt template.
            
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
        
        try:
            # Generate prompt
            prompt_text = self._get_rule_generation_prompt(
                description=description,
                sample_emails=sample_emails,
                context=context,
                few_shot=few_shot,
                custom_prompt=custom_prompt
            )
            
            # Call LLM
            response = self._call_llm(prompt_text)
            
            # Parse JSON response
            try:
                data = json.loads(response)
                rules = data.get("rules", [])
            except json.JSONDecodeError as e:
                return AgentResult(
                    success=False,
                    error_message=f"Invalid JSON response: {str(e)}",
                    metadata={"conversation_id": context.conversation_id if context else None}
                )
            
            # Validate rules
            validation_result = self.rule_validator.validate_rules(rules)
            if not validation_result.success:
                return AgentResult(
                    success=False,
                    data=None,
                    error_message=f"Invalid rules: {validation_result.metadata.get('errors', [])}",
                    metadata={"conversation_id": context.conversation_id if context else None}
                )
            
            return AgentResult(
                success=True,
                data=rules,
                metadata={
                    "conversation_id": context.conversation_id if context else None,
                    "rules_count": len(rules)
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                error_message=f"Rule generation failed: {str(e)}",
                metadata={"conversation_id": context.conversation_id if context else None}
            )
    
    def categorize_emails(
        self,
        emails: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        context: Optional[AgentContext] = None,
        prompt: Optional[str] = None,
        few_shot: bool = True,
        existing_categories: Optional[List[str]] = None
    ) -> AgentResult:
        """
        Categorize emails using LLM-based analysis.
        
        Args:
            emails: Emails to categorize.
            rules: Existing rules to consider for categorization.
            context: Optional conversation context.
            prompt: Optional custom prompt.
            few_shot: Whether to include few-shot examples.
            existing_categories: List of existing categories.
            
        Returns:
            AgentResult with categorization results.
        """
        # Handle empty emails
        if not emails:
            return AgentResult(
                success=True,
                data=[],
                metadata={
                    "warnings": ["No emails to categorize"],
                    "conversation_id": context.conversation_id if context else None
                }
            )
        
        try:
            # Generate prompt
            prompt_text = self._get_categorization_prompt(
                emails=emails,
                rules=rules,
                context=context,
                prompt=prompt,
                few_shot=few_shot,
                existing_categories=existing_categories
            )
            
            # Call LLM
            response = self._call_llm(prompt_text)
            
            # Parse JSON response
            try:
                data = json.loads(response)
                categorizations = data.get("categorizations", [])
            except json.JSONDecodeError as e:
                return AgentResult(
                    success=False,
                    error_message=f"Invalid JSON response: {str(e)}",
                    metadata={"conversation_id": context.conversation_id if context else None}
                )
            
            return AgentResult(
                success=True,
                data=categorizations,
                metadata={
                    "conversation_id": context.conversation_id if context else None,
                    "emails_processed": len(emails)
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                error_message=f"Categorization failed: {str(e)}",
                metadata={"conversation_id": context.conversation_id if context else None}
            )
    
    def summarize_inbox(
        self,
        emails: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        matches: List[Dict[str, Any]],
        context: Optional[AgentContext] = None,
        prompt: Optional[str] = None,
        few_shot: bool = True
    ) -> AgentResult:
        """
        Summarize inbox organization status.
        
        Args:
            emails: Emails to summarize.
            rules: Rules that matched emails.
            matches: Rule-match information.
            context: Optional conversation context.
            prompt: Optional custom prompt.
            few_shot: Whether to include few-shot examples.
            
        Returns:
            AgentResult with inbox summary.
        """
        # Handle empty emails
        if not emails:
            return AgentResult(
                success=True,
                data="No emails in inbox.",
                metadata={
                    "total_emails": 0,
                    "conversation_id": context.conversation_id if context else None
                }
            )
        
        try:
            # Generate prompt
            prompt_text = self._get_summarization_prompt(
                emails=emails,
                rules=rules,
                matches=matches,
                context=context,
                prompt=prompt,
                few_shot=few_shot
            )
            
            # Call LLM
            response = self._call_llm(prompt_text)
            
            return AgentResult(
                success=True,
                data=response,
                metadata={
                    "total_emails": len(emails),
                    "conversation_id": context.conversation_id if context else None
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                error_message=f"Summarization failed: {str(e)}",
                metadata={"conversation_id": context.conversation_id if context else None}
            )
