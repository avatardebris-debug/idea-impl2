"""
Agent router for multi-agent SOP execution.

Routes each SOP step to the appropriate LLM provider/model based on configuration.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .agent_config import AgentConfig, AgentConfigList, AgentMode, ProviderType


# Estimated cost per 1M tokens (USD) for different providers
_COST_PER_M_TOKEN = {
    ProviderType.OPENAI: {"input": 0.15, "output": 0.60},
    ProviderType.ANTHROPIC: {"input": 0.003, "output": 0.015},
    ProviderType.OLLAMA: {"input": 0.0, "output": 0.0},  # Free/local
    ProviderType.LOCAL: {"input": 0.0, "output": 0.0},   # Free/local
}


@dataclass
class StepCost:
    """Cost tracking for a single step execution."""
    step_name: str
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    total_tokens: int = 0

    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens

    def to_dict(self) -> dict:
        return {
            "step_name": self.step_name,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "total_tokens": self.total_tokens,
        }


@dataclass
class ExecutionCost:
    """Total cost tracking for a bulk execution."""
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    step_costs: list = field(default_factory=list)

    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.total_input_tokens + self.total_output_tokens

    def to_dict(self) -> dict:
        return {
            "step_costs": [s.to_dict() for s in self.step_costs],
            "total_cost_usd": self.total_cost_usd,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
        }


class AgentRouter:
    """Routes SOP steps to appropriate agent models."""

    def __init__(
        self,
        agent_configs: Optional[AgentConfigList] = None,
        mode: Optional[AgentMode] = None,
    ):
        self.configs = agent_configs or AgentConfigList()
        self.mode = mode or AgentMode.AUTO
        self.cost_tracker = ExecutionCost(
            total_cost_usd=0.0,
            total_input_tokens=0,
            total_output_tokens=0,
            step_costs=[],
        )

        # If mode is set, apply preset configs
        if mode:
            self._apply_preset(mode)

    def set_mode(self, mode: AgentMode) -> None:
        """Set the router mode."""
        try:
            mode = AgentMode(mode)
        except ValueError:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode
        self._apply_preset(mode)

    def get_config(self, step_index: int) -> Optional[AgentConfig]:
        """Get config for a specific step."""
        return self.configs.get_config(step_index)

    def get_mode_config(self, mode: AgentMode) -> AgentConfig:
        """Get the agent config for a specific mode."""
        if mode == AgentMode.FAST:
            return self.configs.fast
        elif mode == AgentMode.BALANCED:
            return self.configs.balanced
        elif mode == AgentMode.QUALITY:
            return self.configs.quality
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def _apply_preset(self, mode: AgentMode) -> None:
        """Apply preset configuration for the given mode."""
        from .agent_config import get_preset
        preset = get_preset(mode)
        config = AgentConfig(
            provider=preset.provider,
            model=preset.model,
            temperature=preset.temperature,
            max_tokens=preset.max_tokens,
        )
        self.configs.add_config(0, config)

    def route_step(self, step_index: int, step_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route a single step to the appropriate agent.

        Returns a dict with:
            - provider: str
            - model: str
            - prompt: str
            - cost_estimate: float
        """
        config = self.configs.get_config(step_index)

        if config is None:
            # No specific config — use default (openai/gpt-4o-mini)
            config = AgentConfig(
                provider=ProviderType.OPENAI,
                model="gpt-4o-mini",
                temperature=0.7,
            )

        # Build the prompt from context
        prompt = self._build_prompt(step_name, context)

        # Estimate cost
        input_tokens = len(prompt.split())
        output_tokens = config.max_tokens or 512
        cost_per_m = _COST_PER_M_TOKEN.get(config.provider, {"input": 0.0, "output": 0.0})
        cost = (input_tokens / 1_000_000) * cost_per_m["input"] + \
               (output_tokens / 1_000_000) * cost_per_m["output"]

        step_cost = StepCost(
            step_name=step_name,
            provider=config.provider.value,
            model=config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
        self.cost_tracker.step_costs.append(step_cost)

        return {
            "provider": config.provider.value,
            "model": config.model,
            "prompt": prompt,
            "system_prompt": config.system_prompt_override or "",
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "cost_estimate": cost,
        }

    def _build_prompt(self, step_name: str, context: Dict[str, Any]) -> str:
        """Build the prompt for a step from context."""
        lines = [f"# Step: {step_name}", ""]

        # Add context items
        for key, value in context.items():
            if isinstance(value, str):
                lines.append(f"## {key}")
                lines.append(value[:2000] if len(value) > 2000 else value)  # Truncate long values
                lines.append("")
            elif isinstance(value, dict):
                lines.append(f"## {key}")
                lines.append(json.dumps(value, indent=2))
                lines.append("")

        return "\n".join(lines)

    def get_cost_report(self) -> str:
        """Get a human-readable cost report."""
        lines = [
            "=== Cost Report ===",
            f"Total cost: ${self.cost_tracker.total_cost_usd:.4f}",
            f"Total input tokens: {self.cost_tracker.total_input_tokens}",
            f"Total output tokens: {self.cost_tracker.total_output_tokens}",
            "",
            "Per-step breakdown:",
        ]
        for step in self.cost_tracker.step_costs:
            lines.append(
                f"  - {step.step_name}: ${step.cost_usd:.4f} "
                f"({step.provider}/{step.model}) "
                f"[in={step.input_tokens}, out={step.output_tokens}]"
            )
        return "\n".join(lines)

    def get_cost_comparison(self, sop_name: str, num_inputs: int) -> str:
        """Get cost comparison across different agent modes."""
        from .agent_config import get_preset

        lines = [f"=== Cost Comparison for '{sop_name}' (per {num_inputs} inputs) ===", ""]

        for mode in AgentMode:
            preset = get_preset(mode)
            estimated_cost = 0
            for key in ["input", "output"]:
                estimated_cost += (preset.get("max_tokens", 512) / 1_000_000) * _COST_PER_M_TOKEN.get(
                    ProviderType(preset["provider"]), {"input": 0, "output": 0}
                )[key]

            lines.append(f"  {mode.value:10s}: ~${estimated_cost:.4f} per input")

        return "\n".join(lines)


# ---------- LLMClientRouter ----------

class LLMClientRouter:
    """Routes LLM calls to registered provider clients and named agents.

    Supports provider-based routing with fallback chains, and named-agent
    registration for multi-agent SOP execution.
    """

    def __init__(self, configs: Optional[AgentConfigList] = None):
        self.configs = configs or AgentConfigList()
        self.providers: dict[str, Any] = {}   # name -> client
        self.agents: dict[str, Any] = {}       # name -> client
        self.mode: Optional[AgentMode] = AgentMode.AUTO

    def set_mode(self, mode: AgentMode) -> None:
        """Set the router mode."""
        try:
            mode = AgentMode(mode)
        except ValueError:
            raise ValueError(f"Invalid mode: {mode}")
        self.mode = mode

    def get_config(self, mode: AgentMode) -> AgentConfig:
        """Get the agent config for a specific mode."""
        if mode == AgentMode.FAST:
            return self.configs.fast
        elif mode == AgentMode.BALANCED:
            return self.configs.balanced
        elif mode == AgentMode.QUALITY:
            return self.configs.quality
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def get_client(self, provider: ProviderType | AgentMode) -> Any:
        """Get the client for a specific provider or agent mode.
        
        If an AgentMode is provided, resolves it to the corresponding
        provider config and returns that provider's client.
        """
        # If an AgentMode is provided, resolve to provider first
        if isinstance(provider, AgentMode):
            config = self.get_config(provider)
            provider = config.provider
        elif isinstance(provider, str):
            # Try to convert string to ProviderType
            try:
                provider = ProviderType(provider)
            except ValueError:
                raise ValueError(f"Invalid mode: {provider}")
        
        return self.get_provider_client(provider)

    # ---- Provider management ----

    def register_provider(self, name: str, client: Any) -> None:
        """Register an LLM client under *name*."""
        self.providers[name] = client

    def get_provider_client(self, provider: ProviderType) -> Any:
        """Return the client registered for *provider*.
        
        Raises KeyError if no client is registered for the provider.
        """
        key = provider.value
        if key in self.providers:
            return self.providers[key]
        raise KeyError(f"No client registered for provider: {provider.value}")

    def list_providers(self) -> list[str]:
        """Return names of all registered providers."""
        return list(self.providers.keys())

    def resolve_fallback(
        self,
        primary: ProviderType,
        fallbacks: list[str],
    ) -> Any | None:
        """Try *primary* first, then each name in *fallbacks*.

        Returns the first available client, or ``None`` if none found.
        """
        # Try primary
        try:
            return self.get_client(primary)
        except KeyError:
            pass
        # Try fallbacks
        for name in fallbacks:
            if name in self.providers:
                return self.providers[name]
        return None

    # ---- Agent management ----

    def register_agent(self, name: str, client: Any) -> None:
        """Register a named agent."""
        self.agents[name] = client

    def get_agent(self, name: str) -> Any:
        """Return the agent with *name*."""
        if name not in self.agents:
            raise KeyError(f"No agent registered with name '{name}'")
        return self.agents[name]

    def list_agents(self) -> list[str]:
        """Return names of all registered agents."""
        return list(self.agents.keys())
