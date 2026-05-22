"""Agent module for LLM-powered email processing."""

from email_tool.agent.base import AbstractAgent, AgentContext, AgentResult
from email_tool.agent.llm_agent import LLMAgent
from email_tool.agent.rule_generator import RuleGenerator
from email_tool.agent.categorizer import EmailCategorizer
from email_tool.agent.summarizer import InboxSummarizer
from email_tool.agent.memory import MemoryManager
from email_tool.agent.rule_validator import RuleValidator
from email_tool.agent.prompt_templates import PromptTemplates

__all__ = [
    "AbstractAgent",
    "AgentContext",
    "AgentResult",
    "LLMAgent",
    "RuleGenerator",
    "EmailCategorizer",
    "InboxSummarizer",
    "MemoryManager",
    "RuleValidator",
    "PromptTemplates",
]
