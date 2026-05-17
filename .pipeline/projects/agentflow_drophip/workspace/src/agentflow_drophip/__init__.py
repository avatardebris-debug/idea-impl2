"""AgentFlow — AI-powered dropshipping automation system.

AgentFlow is a multi-agent system that automates the entire dropshipping
business workflow, from product sourcing to order fulfillment.

Usage:
    from agentflow_drophip import Orchestrator

    # Create orchestrator
    orchestrator = Orchestrator()

    # Setup business
    spec = orchestrator.setup_business(
        "I want to start a dropshipping business selling electronics "
        "on Shopify with automatic fulfillment"
    )

    # Run full workflow
    result = orchestrator.run_full_workflow()
"""

from agentflow_drophip.agents import AgentResult, BaseAgent, SourcingAgent, ListingAgent, FulfillmentAgent
from agentflow_drophip.config import AgentFlowConfig, get_config
from agentflow_drophip.exceptions import (
    AgentFlowError,
    AgentError,
    OrchestratorError,
    ParserError,
    WorkflowError,
)
from agentflow_drophip.intent_parser import IntentParser
from agentflow_drophip.models import BusinessSpec
from agentflow_drophip.orchestrator import Orchestrator
from agentflow_drophip.workflow import DAG, Node, Task, TaskResult, TaskStatus, WorkflowEngine

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "AgentFlowError",
    "AgentResult",
    "AgentError",
    "BaseAgent",
    "BusinessSpec",
    "DAG",
    "FulfillmentAgent",
    "IntentParser",
    "ListingAgent",
    "Node",
    "Orchestrator",
    "OrchestratorError",
    "ParserError",
    "SourcingAgent",
    "Task",
    "TaskResult",
    "TaskStatus",
    "WorkflowEngine",
    "WorkflowError",
    "get_config",
    "AgentFlowConfig",
]
