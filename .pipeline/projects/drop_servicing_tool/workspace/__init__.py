"""Drop Servicing Tool — SOP Engine + Single Execution."""

__version__ = "0.1.0"

# Phase 3: Multi-Agent SOP Execution
from .agent_config import (
    AgentConfig,
    AgentConfigList,
    AgentMode,
    ProviderType,
    get_preset,
)
from .agent_registry import AgentRegistry
from .agent_router import AgentRouter, LLMClientRouter, ExecutionCost, StepCost
from .multi_agent import MultiAgentSOPExecutor
from .sop_schema import SOP, SOPInput, SOPStep, load_sop, validate_input
from .sop_store import create_sop, delete_sop, get_sop, list_sops
from .template_library import TemplateLibrary
from .export import Exporter

__all__ = [
    # Agent config
    "AgentConfig",
    "AgentConfigList",
    "AgentMode",
    "ProviderType",
    "get_preset",
    # Agent registry
    "AgentRegistry",
    # Agent router
    "AgentRouter",
    "LLMClientRouter",
    "ExecutionCost",
    "StepCost",
    # Multi-agent SOP
    "MultiAgentSOPExecutor",
    # SOP schema & store
    "SOP",
    "SOPInput",
    "SOPStep",
    "load_sop",
    "validate_input",
    "create_sop",
    "delete_sop",
    "get_sop",
    "list_sops",
    # Template library
    "TemplateLibrary",
]
