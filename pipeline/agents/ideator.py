"""
pipeline/agents/ideator.py
Ideator agent — firehose creativity engine.

Receives: trigger from Manager with current context
Produces: timestamped ideator output document, sends to Manager for triage
"""

from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message


class IdeatorAgent(AgentProcess):
    role = "ideator"
    max_steps = 20
    temperature = 0.8   # creative brainstorming — high diversity is the goal
    think = True        # chain-of-thought improves ideation quality

    def handle(self, msg: Message) -> AgentOutput:
        if msg.type == "generate_ideas":
            return self._handle_generate_ideas(msg)
        return self._handle_standard_ideation(msg)

    # ------------------------------------------------------------------
    # Standard ideation (called after a phase completes)
    # ------------------------------------------------------------------

    def _handle_standard_ideation(self, msg: Message) -> AgentOutput:
        phase_num = msg.payload.get("phase", 1)
        review_path = msg.payload.get("review_path", "")
        master_ideas_path = msg.payload.get("master_ideas_path", "")

        # Read all available context
        master_plan = self.read_state_file("state/master_plan.md")
        review_content = self.read_state_file(review_path) if review_path else ""

        # Read master ideas list from project root
        master_ideas = ""
        mi_path = pathlib.Path("master_ideas.md")
        if mi_path.exists():
            master_ideas = mi_path.read_text(encoding="utf-8")

        # Phase spec
        phase_spec = self.read_state_file(f"phases/phase_{phase_num}/spec.md")
        tasks_content = self.read_state_file(f"phases/phase_{phase_num}/tasks.md")

        # Generate a timestamped output path
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = f"ideator_output/{ts}_phase{phase_num}.md"

        task_prompt = (
            f"You are the Ideator — the creative brainstorming engine.\n\n"
            f"## Current Project Master Plan\n{master_plan[:2000]}\n\n"
            f"## Phase {phase_num} Spec\n{phase_spec[:1000]}\n\n"
            f"## Phase {phase_num} Tasks Completed\n{tasks_content[:1000]}\n\n"
            f"## Latest Review\n{review_content[:1500]}\n\n"
            f"## Master Ideas List (all ideas ever)\n{master_ideas[:2000]}\n\n"
            f"## Your Job\n"
            f"1. Read the above context carefully.\n"
            f"2. Generate 10-20 ideas across all categories:\n"
            f"   - Immediate improvements to what was just built\n"
            f"   - Feature expansions for the current idea\n"
            f"   - Parallel ideas that reuse existing code\n"
            f"   - Integration opportunities between ideas in the master list\n"
            f"   - Reusable tools/utilities to extract\n"
            f"3. Be SPECIFIC — name files, functions, exact changes.\n"
            f"4. Write your output to `.pipeline/{output_path}`.\n"
            f"5. Say DONE.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)

        # Read the output
        ideator_content = self.read_state_file(output_path)

        # Send to Manager for triage
        out_msg = Message.create(
            from_agent=self.role,
            to_agent="manager",
            type="result",
            payload={
                "phase": phase_num,
                "ideator_output_path": output_path,
                "ideator_content_preview": ideator_content[:2000],
                "source": "ideator",
            },
        )

        return AgentOutput(
            success=result.completed,
            answer=result.answer,
            outgoing=[out_msg],
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )

    # ------------------------------------------------------------------
    # Autonomous idea generation (called when master_ideas.md is empty)
    # ------------------------------------------------------------------

    def _handle_generate_ideas(self, msg: Message) -> AgentOutput:
        projects_context = msg.payload.get("projects_context", "")
        existing_ideas   = msg.payload.get("existing_ideas", "")
        reusable_tools   = msg.payload.get("reusable_tools", "")
        format_spec      = msg.payload.get("format_spec", "")
        master_ideas_path = msg.payload.get("master_ideas_path", "master_ideas.md")

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_path = f".pipeline/state/idea_generation_log_{ts}.md"

        task_prompt = (
            f"You are the Ideator. The idea backlog is empty. Generate exactly 30 new ideas "
            f"across 6 groups of 5.\n\n"
            f"## Existing Projects (with workspace files and plans)\n"
            f"{projects_context}\n\n"
            f"## Reusable Shared Tools Already Built\n"
            f"{reusable_tools}\n\n"
            f"## Existing Ideas (do NOT duplicate these)\n"
            f"{existing_ideas}\n\n"
            f"## Format for each idea\n"
            f"{format_spec}\n\n"
            f"## The 6 Categories (5 ideas each = 30 total)\n\n"
            f"**GROUP 1 — SIMILAR**: 5 ideas similar in scope/type to existing projects "
            f"but targeting different niches or audiences.\n\n"
            f"**GROUP 2 — EXPANSION**: 5 ideas that expand an existing project with new "
            f"major features. Read the workspace files listed above to understand what was "
            f"built and what meaningful next steps would be.\n\n"
            f"**GROUP 3 — INDEPENDENT**: 5 fresh ideas completely unrelated to existing work. "
            f"Think about tools, services, or products people actually pay for.\n\n"
            f"**GROUP 4 — COMBINATION**: 5 ideas that merge 2 or more existing projects "
            f"into a unified product. Name which projects are combined.\n\n"
            f"**GROUP 5 — BRIDGE**: 5 ideas for connectors, APIs, or integrations that "
            f"link existing projects together so they can share data or workflows.\n\n"
            f"**GROUP 6 — HARNESS**: 5 ideas for improving this pipeline/toolkit itself — "
            f"better agents, new capabilities, developer tooling, observability, etc.\n\n"
            f"## Instructions\n"
            f"1. Think deeply about the existing projects and their actual workspace code.\n"
            f"2. Write all 30 ideas (one per line) in the correct format.\n"
            f"3. APPEND them to `{master_ideas_path}` — do NOT overwrite the file.\n"
            f"   Use a section header like: `## Auto-Generated — {ts}`\n"
            f"4. Write a 3-line summary of what you added to `{log_path}`.\n"
            f"5. Say DONE.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)

        # Signal the manager that ideation is complete
        signal_msg = Message.create(
            from_agent=self.role,
            to_agent="manager",
            type="PIPELINE_SIGNAL",
            payload={
                "signal": "IDEA_GENERATION_COMPLETE",
                "log_path": log_path,
                "source": "ideator",
            },
        )

        return AgentOutput(
            success=result.completed,
            answer=result.answer,
            outgoing=[signal_msg],
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )


def main():
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default=__import__("os").environ.get("PIPELINE_MODEL", "qwen3.5:35b"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [ideator] %(message)s")

    agent = IdeatorAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
