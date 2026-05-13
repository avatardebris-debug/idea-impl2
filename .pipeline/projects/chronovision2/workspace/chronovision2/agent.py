"""
agent.py
The main agent loop — receives LLM responses, executes tools, and feeds
results back into the loop.

This is the orchestrator that ties together:
  - LLM interface (llm_interface.py)
  - Tool registry (tools.py)
  - Hypothesis manager (hypothesis_manager.py)
  - Memory system (memory.py)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from chronovision2.llm_interface import get_llm, LLMBase, Message
from chronovision2.tools import TOOLS, TOOL_SCHEMAS
from chronovision2.core.hypothesis_manager import HypothesisManager
from chronovision2.memory import MemorySystem

log = logging.getLogger(__name__)


class Agent:
    """
    Main agent class.

    Parameters
    ----------
    provider : str
        LLM provider name (openai, claude, ollama, gemini, grok).
    model : str | None
        Model override.
    temperature : float
        Sampling temperature.
    max_iterations : int
        Maximum tool-call iterations per task.
    """

    def __init__(
        self,
        provider: str = "ollama",
        model: str | None = None,
        temperature: float = 0.2,
        max_iterations: int = 20,
    ):
        self.llm: LLMBase = get_llm(
            provider=provider,
            model=model,
            temperature=temperature,
        )
        self.max_iterations = max_iterations
        self.hypothesis_manager = HypothesisManager()
        self.memory = MemorySystem()
        self.iteration_count: int = 0

    # ------------------------------------------------------------------
    # Core loop
    # ------------------------------------------------------------------

    def run(self, user_input: str) -> str:
        """
        Execute one full agent loop for a user request.

        Returns the final assistant response text.
        """
        messages: list[dict] = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_input},
        ]

        for i in range(self.max_iterations):
            self.iteration_count += 1

            # Get LLM response
            response = self.llm.chat(messages, tools=TOOL_SCHEMAS)

            # Check for tool calls
            if response.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": response.tool_calls,
                })

                # Execute each tool call
                for tc in response.tool_calls:
                    result = self._execute_tool(tc)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", ""),
                        "content": result,
                    })

                # Feed results back to LLM
                response = self.llm.chat(messages, tools=TOOL_SCHEMAS)

                # If the LLM now has text content (no more tool calls), we're done
                if not response.tool_calls and response.content:
                    messages.append({
                        "role": "assistant",
                        "content": response.content,
                    })
                    break

            elif response.content:
                # Pure text response — done
                messages.append({
                    "role": "assistant",
                    "content": response.content,
                })
                break

        return response.content or "(no response)"

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def _execute_tool(self, tool_call: dict) -> str:
        """Execute a single tool call and return its result."""
        name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        if name not in TOOLS:
            return f"ERROR: Unknown tool '{name}'"

        try:
            result = TOOLS[name](**args)
            return result
        except Exception as e:
            return f"ERROR executing '{name}': {e}"

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        """Build the system prompt with hypothesis info."""
        summary = self.hypothesis_manager.get_summary()
        return (
            "You are a helpful AI agent with access to file, shell, and search tools. "
            "Use tools to accomplish the user's request. Be thorough and precise.\n\n"
            f"Current hypothesis state: {json.dumps(summary, indent=2)}"
        )
