"""Email categorizer module for organizing emails."""

from typing import Any, Dict, List, Optional

from email_tool.agent.base import AgentContext, AgentResult
from email_tool.agent.llm_agent import LLMAgent


class EmailCategorizer:
    """
    Categorizes emails using LLM-based analysis.
    
    This class provides a high-level interface for email categorization,
    handling validation and error handling.
    """
    
    def __init__(self, llm_agent: Optional[LLMAgent] = None):
        """
        Initialize the email categorizer.
        
        Args:
            llm_agent: Optional LLM agent instance. If not provided,
                      a default one will be created.
        """
        self.llm_agent = llm_agent or LLMAgent()
    
    def categorize_emails(
        self,
        emails: List[Dict[str, Any]],
        rules: List[Dict[str, Any]] = None,
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
            # Call LLM agent to categorize emails
            result = self.llm_agent.suggest_categories(
                emails=emails,
                rules=rules or [],
                context=context,
                prompt=prompt,
                few_shot=few_shot,
                existing_categories=existing_categories
            )
            
            # Map rule_type to type for compatibility
            if result.success and result.data:
                for item in result.data:
                    if "matched_rule" in item and item["matched_rule"]:
                        # matched_rule is already a string name
                        pass
            
            # Add metadata about categorization counts
            if result.success and result.data:
                categorized_count = sum(1 for item in result.data if item.get("category") != "uncategorized")
                uncategorized_count = len(result.data) - categorized_count
                
                result.metadata["categorized_count"] = categorized_count
                result.metadata["uncategorized_count"] = uncategorized_count
                result.metadata["total_emails"] = len(emails)
            
            return result
            
        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                error_message=f"Categorization failed: {str(e)}",
                metadata={"conversation_id": context.conversation_id if context else None}
            )
