"""SOP Executor — runs SOPs step-by-step with LLM or mock calls.

Wraps the shared executor engine with project-specific SOP loading
and output formatting.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from .sop_loader import AgencySOP


# ------ LLM client protocol ------

class LLMClient(Protocol):
    """Minimal LLM client interface."""
    def call(self, system_prompt: str, user_prompt: str) -> str: ...


# ------ Mock client ------

class MockLLMClient:
    """Deterministic mock LLM client for testing / no-API scenarios."""

    def __init__(self, prefix: str = "Step output") -> None:
        self.prefix = prefix

    def call(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps({
            "raw": f"{self.prefix} for step (mock output)",
            "step_name": "mock",
            "tokens_used": 0,
        })


# ------ Execution log entry ------

@dataclass
class StepLog:
    """Record of a single step execution."""
    step_name: str
    prompt: str
    output: str
    duration_seconds: float
    tokens_used: int = 0
    error: Optional[str] = None


# ------ SOPExecutor class ------

class SOPExecutor:
    """Executes a validated SOP step-by-step.

    Args:
        sop:         A validated :class:`AgencySOP` model.
        llm_client:  Optional LLM client.  If *None*, a :class:`MockLLMClient`
                      is used automatically.
    """

    def __init__(self, sop: AgencySOP, llm_client: Optional[LLMClient] = None) -> None:
        self.sop = sop
        self._llm = llm_client or MockLLMClient()
        self._step_outputs: List[Dict[str, Any]] = []
        self._log: List[StepLog] = []

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full SOP end-to-end.

        Args:
            input_data:  Input dict matching the SOP's declared inputs.

        Returns:
            Dict containing all step outputs keyed by their ``output_key``.

        Raises:
            ValueError:  If input validation fails or a step errors out.
        """
        from .sop_loader import SOPLoader
        loader = SOPLoader()
        validated = loader.validate_input(self.sop, input_data)

        self._step_outputs = []
        self._log = []

        for idx, step in enumerate(self.sop.steps):
            start = time.time()
            try:
                prompt = self._build_prompt(idx, validated)

                raw_output = self._llm.call(
                    system_prompt=(
                        f"You are executing step '{step.name}' of SOP "
                        f"'{self.sop.name}'."
                    ),
                    user_prompt=prompt,
                )

                try:
                    parsed = json.loads(raw_output)
                except (json.JSONDecodeError, TypeError):
                    parsed = {"raw": raw_output}

                duration = time.time() - start
                tokens = parsed.get("tokens_used", 0)

                entry = {
                    step.output_key: parsed,
                    "raw": raw_output,
                }
                self._step_outputs.append(entry)

                self._log.append(StepLog(
                    step_name=step.name,
                    prompt=prompt,
                    output=raw_output,
                    duration_seconds=duration,
                    tokens_used=tokens,
                ))

            except Exception as exc:
                duration = time.time() - start
                self._log.append(StepLog(
                    step_name=step.name,
                    prompt="",
                    output="",
                    duration_seconds=duration,
                    error=str(exc),
                ))
                raise ValueError(
                    f"Step '{step.name}' (index {idx}) failed: {exc}"
                ) from exc

        # Assemble final output
        final: Dict[str, Any] = {}
        for entry in self._step_outputs:
            final.update(entry)
        final["_sop_name"] = self.sop.name
        final["_execution_log"] = [
            {"step": entry.step_name, "duration": entry.duration_seconds, "error": entry.error}
            for entry in self._log
        ]
        return final

    def _build_prompt(self, step_index: int, input_data: Dict[str, Any]) -> str:
        """Build the prompt for a given step."""
        from .prompts import build_step_prompt
        return build_step_prompt(
            self.sop.to_sop(),
            step_index=step_index,
            input_data=input_data,
            step_outputs=self._step_outputs,
        )

    def get_step_outputs(self) -> List[Dict[str, Any]]:
        """Return intermediate step outputs."""
        return list(self._step_outputs)

    def get_execution_log(self) -> List[StepLog]:
        """Return execution log entries."""
        return list(self._log)


# ------ Convenience function ------

def execute_sop(
    sop_name: str,
    input_data: Dict[str, Any],
    llm_client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """Convenience function to execute an SOP by name.

    Args:
        sop_name:    Name of the SOP (must exist in the SOPs directory).
        input_data:  Input dict matching the SOP's declared inputs.
        llm_client:  Optional LLM client.

    Returns:
        Final output dict.
    """
    from .sop_loader import SOPLoader
    loader = SOPLoader()
    sop = loader.get_sop(sop_name)
    executor = SOPExecutor(sop, llm_client)
    return executor.run(input_data)
