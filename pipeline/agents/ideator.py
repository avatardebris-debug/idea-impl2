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
    model_tier = "light"
    num_ctx = 4096
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
        import pathlib
        import re
        import logging
        from llm_interface import get_llm

        logger = logging.getLogger(__name__)

        projects_context = msg.payload.get("projects_context", "")
        existing_ideas   = msg.payload.get("existing_ideas", "")
        reusable_tools   = msg.payload.get("reusable_tools", "")
        format_spec      = msg.payload.get("format_spec", "")
        master_ideas_path = msg.payload.get("master_ideas_path", "master_ideas.md")

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # --- Call LLM DIRECTLY (no ReAct loop) ---
        # generate_ideas is purely generative — no file tools needed.
        # We write to master_ideas.md ourselves in Python after the call.
        llm = get_llm(self.provider, model=self.model, temperature=0.85)

        system_prompt = (
            "You are the Ideator — a creative idea generation engine for an autonomous "
            "software development pipeline. Generate concise, actionable software project ideas. "
            "Respond ONLY with the list of ideas in the requested format. No preamble, no summary."
        )

        user_prompt = (
            f"The idea backlog is empty. Generate exactly 30 new ideas across 6 groups of 5.\n\n"
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
            f"major features. Use the workspace file listings above to understand what was "
            f"built and what meaningful next steps would be.\n\n"
            f"**GROUP 3 — INDEPENDENT**: 5 fresh ideas completely unrelated to existing work. "
            f"Think about tools, services, or products people actually pay for.\n\n"
            f"**GROUP 4 — COMBINATION**: 5 ideas that merge 2 or more existing projects "
            f"into a unified product. Name which projects are combined.\n\n"
            f"**GROUP 5 — BRIDGE**: 5 ideas for connectors, APIs, or integrations that "
            f"link existing projects together so they can share data or workflows.\n\n"
            f"**GROUP 6 — HARNESS**: 5 ideas for improving this pipeline/toolkit itself — "
            f"better agents, new capabilities, developer tooling, observability, etc.\n\n"
            f"Output ONLY the 30 idea lines with group headers. Each idea on its own line:\n"
            f"  - [ ] **[Title]** — [description]\n"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        logger.info("[ideator] Calling LLM directly for idea generation (no ReAct loop)")
        response = llm.chat(messages)
        raw_text = response.content or ""

        # --- Parse idea lines from response ---
        idea_lines = [
            line.strip()
            for line in raw_text.splitlines()
            if re.match(r"^\s*-\s*\[[ xX]\]", line)
        ]

        # Force all generated ideas to unchecked [ ]
        idea_lines = [re.sub(r"\[[ xX]\]", "[ ]", l) for l in idea_lines]

        # --- Append to master_ideas.md ---
        mi_path = pathlib.Path(master_ideas_path)
        if not mi_path.exists():
            mi_path = pathlib.Path("master_ideas.md")

        header = f"\n\n## Auto-Generated — {ts}\n\n"
        body   = "\n".join(idea_lines) + "\n"
        try:
            with open(mi_path, "a", encoding="utf-8") as f:
                f.write(header + body)
            logger.info(
                "[ideator] Appended %d ideas to %s", len(idea_lines), mi_path
            )
        except Exception as e:
            logger.error("[ideator] Failed to write to master_ideas.md: %s", e)

        # --- Write generation log ---
        log_dir = pathlib.Path(".pipeline/state")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = str(log_dir / f"idea_generation_log_{ts}.md")
        try:
            pathlib.Path(log_path).write_text(
                f"# Idea Generation — {ts}\n\n"
                f"Generated {len(idea_lines)} ideas.\n\n"
                f"## Raw LLM output preview\n\n{raw_text[:2000]}\n",
                encoding="utf-8",
            )
        except Exception:
            pass

        # --- Signal manager ---
        signal_msg = Message.create(
            from_agent=self.role,
            to_agent="manager",
            type="PIPELINE_SIGNAL",
            payload={
                "signal": "IDEA_GENERATION_COMPLETE",
                "ideas_added": len(idea_lines),
                "log_path": log_path,
                "source": "ideator",
            },
        )

        summary = (
            f"Generated {len(idea_lines)} new ideas and appended to master_ideas.md"
            if idea_lines
            else "LLM returned no parseable idea lines — check idea_generation_log"
        )
        return AgentOutput(
            success=bool(idea_lines),
            answer=summary,
            outgoing=[signal_msg],
            tokens_used=response.usage.total_tokens if response.usage else 0,
            steps_used=1,
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
