"""
pipeline/hermes_runner.py
Worker + Critic loop for open-ended Hermes tasks.

Architecture:
  - Worker:  Hermes AIAgent (run_conversation) — iterates with tools
  - Critic:  Lightweight LLM call — reads worker output, evaluates against
             `hermes_goal_check`, decides achieved/not-yet/give-up.

This module is imported by runner.py and goal_decomposer.py.
It does NOT start any subprocess — it runs Hermes in-process.

Usage:
    from pipeline.hermes_runner import HermesGoalRunner

    runner = HermesGoalRunner()
    result = runner.run(
        prompt="Research 3 MuJoCo robot URDFs and write a comparison table to .pipeline/goals/urdf_research.md",
        goal_check="Has the agent written a ranked comparison of ≥3 URDFs to .pipeline/goals/urdf_research.md?",
        time_budget_min=30,
    )
    print(result["status"])   # "achieved" | "budget_exceeded"
    print(result["output"])   # agent's final response text
    print(result["attempts"]) # number of critic loops used
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import re
import sys
import time
from typing import Any

logger = logging.getLogger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
HERMES_DIR = PROJECT_ROOT / "hermes-agent-main"

# ---------------------------------------------------------------------------
# Provider resolution (mirrors what runner.py uses for pipeline agents)
# ---------------------------------------------------------------------------

def _pipeline_model() -> str:
    """Return the model the pipeline is currently configured to use."""
    return os.environ.get("PIPELINE_MODEL", "qwen3:6b")


def _pipeline_provider() -> str:
    return os.environ.get("PIPELINE_PROVIDER", "ollama")


def _hermes_base_url(provider: str, model: str) -> str:
    """Map pipeline provider → Hermes-compatible base_url."""
    if provider == "ollama":
        return os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    if provider == "openrouter":
        return "https://openrouter.ai/api/v1"
    if provider == "openai":
        return "https://api.openai.com/v1"
    # Fallback: let Hermes auto-detect via env
    return ""


def _hermes_api_key(provider: str) -> str:
    """Return the API key for the given provider."""
    if provider == "ollama":
        return "ollama"   # Ollama ignores the key but AIAgent requires it non-empty
    if provider == "openrouter":
        return os.environ.get("OPENROUTER_API_KEY", "")
    if provider == "openai":
        return os.environ.get("OPENAI_API_KEY", "")
    return os.environ.get("OPENROUTER_API_KEY", os.environ.get("OPENAI_API_KEY", "sk-dummy"))


# ---------------------------------------------------------------------------
# Critic: lightweight LLM eval
# ---------------------------------------------------------------------------

def _critic_verdict(
    goal_check: str,
    agent_output: str,
    base_url: str,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    """
    Call a lightweight LLM to evaluate if the agent achieved the goal.

    Returns:
        {"achieved": bool, "confidence": float, "reason": str}
    """
    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url or None, api_key=api_key or "dummy")

        prompt = (
            f"You are a goal-achievement critic. Evaluate whether the agent output satisfies"
            f" the goal check.\n\n"
            f"GOAL CHECK: {goal_check}\n\n"
            f"AGENT OUTPUT (last 3000 chars):\n{agent_output[-3000:]}\n\n"
            f"Reply with JSON ONLY, no other text:\n"
            f'{{ "achieved": true/false, "confidence": 0.0-1.0, "reason": "one sentence" }}'
        )

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        raw = response.choices[0].message.content or "{}"
        # Strip <think>...</think> blocks from reasoning models
        raw = re.sub(r"<think>.*?</think>\s*", "", raw, flags=re.DOTALL).strip()
        # Extract JSON
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception as exc:
        logger.warning("Critic LLM call failed: %s", exc)

    # Fallback: assume not yet achieved (don't give up prematurely)
    return {"achieved": False, "confidence": 0.0, "reason": f"Critic call failed: {exc}"}


# ---------------------------------------------------------------------------
# Worker: Hermes AIAgent
# ---------------------------------------------------------------------------

def _build_worker(base_url: str, model: str, api_key: str, max_iterations: int = 25):
    """Instantiate a Hermes AIAgent configured for pipeline use."""
    # Add hermes to path temporarily
    if str(HERMES_DIR) not in sys.path:
        sys.path.insert(0, str(HERMES_DIR))

    try:
        from run_agent import AIAgent
    except ImportError as exc:
        raise RuntimeError(
            f"Cannot import Hermes AIAgent from {HERMES_DIR}. "
            f"Ensure hermes-agent-main/ is present. Error: {exc}"
        ) from exc

    worker = AIAgent(
        base_url=base_url,
        api_key=api_key,
        model=model,
        max_iterations=max_iterations,
        quiet_mode=True,       # suppress Hermes's per-tool prints in pipeline context
        verbose_logging=False,
    )
    return worker


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class HermesGoalRunner:
    """
    Worker + Critic loop for goal-directed Hermes tasks.

    The Worker (Hermes AIAgent) runs until either:
      - The Critic decides the goal is achieved (confidence > threshold), or
      - max_attempts is exhausted.

    The Critic's reason is fed back to the Worker as a follow-up message
    so it can iterate on its own shortcomings without restarting from scratch.
    """

    def __init__(
        self,
        model: str | None = None,
        provider: str | None = None,
        max_worker_iterations: int = 25,
        max_attempts: int = 4,
        critic_confidence_threshold: float = 0.72,
    ):
        self.model = model or _pipeline_model()
        self.provider = provider or _pipeline_provider()
        self.base_url = _hermes_base_url(self.provider, self.model)
        self.api_key = _hermes_api_key(self.provider)
        self.max_worker_iterations = max_worker_iterations
        self.max_attempts = max_attempts
        self.critic_threshold = critic_confidence_threshold

    def run(
        self,
        prompt: str,
        goal_check: str,
        time_budget_min: int = 30,
        branch_id: str = "",
    ) -> dict[str, Any]:
        """
        Run a Hermes task with goal-critic termination.

        Args:
            prompt:          Full task description for the Worker agent.
            goal_check:      Yes/no question the Critic evaluates against the output.
            time_budget_min: Wall-clock budget. Runner stops after this many minutes
                             even if goal not achieved.
            branch_id:       Optional label for log messages.

        Returns:
            {
              "status":   "achieved" | "budget_exceeded" | "error",
              "output":   str (Worker's last final_response),
              "attempts": int,
              "messages": list (full Hermes conversation history),
            }
        """
        label = f"[hermes:{branch_id}]" if branch_id else "[hermes]"
        deadline = time.time() + time_budget_min * 60

        worker = _build_worker(self.base_url, self.model, self.api_key, self.max_worker_iterations)
        history: list[dict] = []
        last_output = ""
        last_messages: list[dict] = []

        for attempt in range(1, self.max_attempts + 1):
            if time.time() > deadline:
                print(f"  {label} Time budget exhausted after {attempt - 1} attempt(s)")
                return {
                    "status": "budget_exceeded",
                    "output": last_output,
                    "attempts": attempt - 1,
                    "messages": last_messages,
                }

            print(f"  {label} Worker attempt {attempt}/{self.max_attempts}...")

            # Build the user message: first attempt = original prompt,
            # subsequent attempts = critic feedback appended
            if attempt == 1:
                user_msg = prompt
            else:
                user_msg = (
                    f"Your previous output was evaluated and found incomplete:\n\n"
                    f"REASON: {critic_reason}\n\n"
                    f"Please continue working to satisfy the goal:\n{goal_check}"
                )

            try:
                result = worker.run_conversation(
                    user_message=user_msg,
                    conversation_history=history if attempt > 1 else None,
                )
            except Exception as exc:
                logger.error("%s Worker raised exception on attempt %d: %s", label, attempt, exc)
                return {
                    "status": "error",
                    "output": last_output,
                    "attempts": attempt,
                    "messages": last_messages,
                    "error": str(exc),
                }

            last_output = result.get("final_response") or ""
            last_messages = result.get("messages", [])

            # Feed full history to next Worker call for continuity
            history = last_messages

            print(f"  {label} Calling critic (attempt {attempt})...")
            verdict = _critic_verdict(
                goal_check=goal_check,
                agent_output=last_output,
                base_url=self.base_url,
                model=self.model,
                api_key=self.api_key,
            )

            achieved = verdict.get("achieved", False)
            confidence = verdict.get("confidence", 0.0)
            critic_reason = verdict.get("reason", "No reason provided.")

            print(
                f"  {label} Critic: achieved={achieved} confidence={confidence:.2f} "
                f"— {critic_reason}"
            )

            if achieved and confidence >= self.critic_threshold:
                print(f"  {label} ✅ Goal achieved in {attempt} attempt(s)")
                return {
                    "status": "achieved",
                    "output": last_output,
                    "attempts": attempt,
                    "messages": last_messages,
                    "critic_confidence": confidence,
                }

        # All attempts exhausted without critic satisfaction
        print(f"  {label} ⚠ Max attempts ({self.max_attempts}) reached — returning best output")
        return {
            "status": "budget_exceeded",
            "output": last_output,
            "attempts": self.max_attempts,
            "messages": last_messages,
        }


# ---------------------------------------------------------------------------
# Convenience: run a single hermes_task branch from a goal tree
# ---------------------------------------------------------------------------

def run_hermes_branch(branch: dict, time_budget_min: int = 30) -> dict[str, Any]:
    """
    Run a single `hermes_task` branch dict from a GoalTree.

    Args:
        branch: A branch dict with keys: id, hermes_prompt, hermes_goal_check
        time_budget_min: Wall-clock budget in minutes

    Returns:
        Result dict from HermesGoalRunner.run()
    """
    runner = HermesGoalRunner()
    return runner.run(
        prompt=branch.get("hermes_prompt", branch.get("description", "")),
        goal_check=branch.get("hermes_goal_check", "Has the task been completed?"),
        time_budget_min=time_budget_min,
        branch_id=branch.get("id", ""),
    )
