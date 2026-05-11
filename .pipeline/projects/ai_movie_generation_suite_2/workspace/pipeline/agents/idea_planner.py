"""
pipeline.agents.idea_planner
Idea Planner agent — receives ideas from the runner, checks dependencies,
and builds prompts for the LLM.
"""

from __future__ import annotations
import json
import pathlib
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class AgentOutput:
    """Result of an agent call."""
    success: bool = False
    answer: str = ""
    tokens_used: int = 0
    steps_used: int = 0
    outgoing: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# IdeaPlannerAgent
# ---------------------------------------------------------------------------

class IdeaPlannerAgent:
    """
    Receives seeded ideas, validates them, and builds LLM prompts
    that include dependency context.
    """

    def __init__(self, run_dir: str | pathlib.Path | None = None):
        self._run_dir = pathlib.Path(run_dir) if run_dir else pathlib.Path(".")
        self._current_slug: str = ""

    # ── State helpers ────────────────────────────────────────────────

    def _project_path(self, rel: str) -> pathlib.Path:
        """Resolve a relative project path under the pipeline dir."""
        return self._run_dir / "projects" / rel

    def read_state_file(self, path: str) -> str:
        """Read a state JSON file and return its content as string."""
        p = pathlib.Path(path)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""

    def write_state_file(self, path: str, content: str) -> None:
        """Write content to a state file."""
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def write_json_state(self, path: str, data: dict) -> None:
        """Write a dict as JSON to a state file."""
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ── Agent call ───────────────────────────────────────────────────

    def call_agent(self, task: str, **kwargs: Any) -> AgentOutput:
        """
        Call the underlying agent with the given task string.
        In production this would invoke the LLM; in tests it can be mocked.
        """
        # Default: return a successful output
        return AgentOutput(success=True, answer="DONE", tokens_used=0, steps_used=1)

    # ── Message handler ──────────────────────────────────────────────

    def handle(self, msg: Any) -> AgentOutput:
        """
        Handle a seeded idea message.

        Builds a prompt that includes:
        - The idea title and description
        - Dependency context (workspace paths, status)
        - Instructions for the planner
        """
        payload = msg.payload if hasattr(msg, "payload") else msg

        title = payload.get("title", "Untitled")
        idea = payload.get("idea", "")
        idea_slug = payload.get("idea_slug", "")
        depends_on = payload.get("depends_on", [])
        dep_workspaces = payload.get("dep_workspaces", {})

        self._current_slug = idea_slug

        # Build dependency context block
        dep_context_lines: list[str] = []
        if depends_on:
            dep_context_lines.append("## Dependencies\n")
            for dep_slug in depends_on:
                ws_path = dep_workspaces.get(dep_slug, "")
                dep_status = "unknown"
                if ws_path:
                    state_file = pathlib.Path(ws_path) / "state" / "current_idea.json"
                    if state_file.exists():
                        try:
                            state = json.loads(state_file.read_text())
                            dep_status = state.get("status", "unknown")
                        except (json.JSONDecodeError, OSError):
                            dep_status = "unknown"
                dep_context_lines.append(f"- **{dep_slug}**: status={dep_status}, workspace={ws_path}")
        else:
            dep_context_lines.append("## Dependencies\nNo dependencies — free to proceed.\n")

        dep_context = "\n".join(dep_context_lines)

        # Build the full prompt
        prompt = f"""## Task: Plan and execute the following idea

### Idea
**Title:** {title}
**Slug:** {idea_slug}

**Description:**
{idea}

{dep_context}

### Instructions
1. Read the dependency workspaces to understand what's available.
2. Use `list_tree` to explore each dependency workspace.
3. Design your implementation to be compatible with existing dependencies.
4. Write your code and tests.
5. Return your completed work.

**MUST be compatible** with all listed dependencies.
"""

        # Call the agent
        result = self.call_agent(prompt)

        # If the agent produced outgoing messages, record them
        if hasattr(result, "outgoing") and result.outgoing:
            for out_msg in result.outgoing:
                # Could send to message bus here
                pass

        return result
