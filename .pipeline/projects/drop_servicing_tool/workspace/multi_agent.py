"""Multi-Agent SOP Executor.

Executes SOPs through multiple agent steps, routing each step to
the appropriate LLM provider via an LLMClientRouter.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_config import AgentConfigList, ProviderType
from .agent_router import LLMClientRouter
from .sop_schema import SOP, SOPInput
from .sop_store import get_sop


class MultiAgentSOPExecutor:
    """Orchestrates multi-agent SOP execution."""

    def __init__(
        self,
        sop_name: str,
        agent_config_list: AgentConfigList,
        router: LLMClientRouter,
        base_dir: Optional[Path] = None,
    ):
        self.sop_name = sop_name
        self.agent_config_list = agent_config_list
        self.router = router
        self._base = base_dir or Path(".")

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the SOP with *input_data* through all steps.

        Returns a dict with step results and metadata.
        """
        # Load SOP
        sop = get_sop(self.sop_name)

        # Validate input
        validated = self._validate_input(sop, input_data)

        # Execute each step
        step_outputs: List[Dict[str, Any]] = []
        for step_index, step in enumerate(sop.steps):
            # Get agent config for this step
            config = self.agent_config_list.get_config(step_index)
            if config is None:
                config = type(self.agent_config_list.get_config(0))(
                    provider=ProviderType.OPENAI,
                    model="gpt-4o-mini",
                ) if self.agent_config_list.get_config(0) else None
                if config is None:
                    from .agent_config import AgentConfig
                    config = AgentConfig(
                        provider=ProviderType.OPENAI,
                        model="gpt-4o-mini",
                    )

            # Get client (with fallback)
            client = self._get_client_with_fallback(config)

            if client is None:
                raise RuntimeError(
                    f"No client available for step {step_index} ({step.name})"
                )

            # Build prompt
            prompt = self._build_prompt(sop, step_index, validated, step_outputs)

            # Execute step
            system_prompt = config.system_prompt_override or ""
            raw_output = client.call(system_prompt, prompt)

            # Parse output
            result = {
                "step_name": step.name,
                "raw": raw_output,
                "step_index": step_index,
            }
            step_outputs.append(result)

        # Build final result
        result = dict(validated)
        result["_sop_name"] = self.sop_name
        result["_steps"] = [
            {
                "step_index": so["step_index"],
                "step_name": so["step_name"],
                "raw": so["raw"],
            }
            for so in step_outputs
        ]
        return result

    def _validate_input(
        self,
        sop: SOP,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate input against SOP schema."""
        from .sop_schema import validate_input
        return validate_input(sop, input_data)

    def _get_client_with_fallback(
        self,
        config: Any,
    ) -> Any:
        """Get LLM client with fallback support."""
        provider = config.provider if hasattr(config, "provider") else ProviderType.OPENAI
        fallbacks = []
        if hasattr(config, "fallback_models") and config.fallback_models:
            fallbacks = config.fallback_models

        # Try primary first
        client = self.router.resolve_fallback(provider, fallbacks)
        if client is not None:
            return client

        # Implicit fallback: try all registered providers
        for name in self.router.list_providers():
            if name != provider.value:
                try:
                    return self.router.providers[name]
                except KeyError:
                    continue

        return None

    def _build_prompt(
        self,
        sop: SOP,
        step_index: int,
        input_data: Dict[str, Any],
        step_outputs: List[Dict[str, Any]],
    ) -> str:
        """Build the prompt string for a step."""
        step = sop.steps[step_index]

        previous_output = "N/A"
        if step_index > 0 and step_outputs:
            previous_output = step_outputs[step_index - 1].get("raw", "N/A")

        prompt = (
            f"# Step: {step.name}\n"
            f"{step.description}\n\n"
            f"## Input\n"
            f"{json.dumps(input_data, indent=2)}\n\n"
            f"## Previous Output\n"
            f"{previous_output}\n\n"
            f"## Output Format\n"
            f"{sop.output_format or 'N/A'}"
        )
        return prompt
