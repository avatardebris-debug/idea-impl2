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

        mission_block = ""
        try:
            from pipeline.mission import mission_prompt_block

            mission_block = mission_prompt_block(include_construct=True)
        except Exception:
            pass

        task_prompt = (
            f"You are the Ideator — the creative brainstorming engine.\n\n"
        )
        if mission_block:
            task_prompt += f"## Mission & Values\n{mission_block}\n\n"
        task_prompt += (
            f"## Current Project Master Plan\n{master_plan[:2000]}\n\n"
            f"## Phase {phase_num} Spec\n{phase_spec[:1000]}\n\n"
            f"## Phase {phase_num} Tasks Completed\n{tasks_content[:1000]}\n\n"
            f"## Latest Review\n{review_content[:1500]}\n\n"
            f"## Master Ideas List (all ideas ever)\n{master_ideas[:2000]}\n\n"
            f"## Your Job\n"
            f"1. Read the above context carefully.\n"
            f"2. Generate 10-20 ideas biased toward pipeline improvement and RSI:\n"
            f"   - Harness: runner, agents, debugging, speed, learning loops\n"
            f"   - Immediate fixes to what was just built\n"
            f"   - Reusable tools/utilities to extract (shared_libs / capability registry)\n"
            f"   - Bridges/connectors between existing projects (kind:connector requires: slugs)\n"
            f"   - Safe experiments (dynamic routing, metrics, A/B)\n"
            f"3. Be SPECIFIC — name files, functions, exact changes.\n"
            f"4. Write your output to `.pipeline/{output_path}` using sections:\n"
            f"   Immediate / Harness / Reusable / Bridge / Experiment\n"
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

        mission_block = ""
        construct_block = ""
        deconstruct_block = ""
        try:
            from pipeline.mission import (
                ideator_construct_prompt,
                ideator_deconstruct_prompt,
                mission_prompt_block,
            )

            mission_block = mission_prompt_block()
            construct_block = ideator_construct_prompt()
            deconstruct_block = ideator_deconstruct_prompt()
        except Exception:
            pass

        system_prompt = (
            "You are the Ideator for an autonomous self-improving software pipeline. "
            "Prioritize ideas that make the pipeline faster, smarter, more debuggable, "
            "more agentic, and better at recursive self-improvement (RSI). "
            "Respond ONLY with the list of ideas in the requested format. No preamble."
        )
        if mission_block:
            system_prompt += f"\n\n{mission_block}"

        user_prompt = (
            f"The idea backlog is empty. Generate exactly 30 ideas across 6 groups of 5.\n\n"
        )
        if construct_block:
            user_prompt += f"## Construct pass\n{construct_block}\n\n"
        user_prompt += (
            f"## Existing Projects (slug= in each block — use exact slugs for bridges)\n"
            f"{projects_context}\n\n"
            f"## Reusable Shared Tools Already Built\n"
            f"{reusable_tools}\n\n"
            f"## Existing Ideas (do NOT duplicate)\n"
            f"{existing_ideas}\n\n"
            f"## Format for each idea\n"
            f"{format_spec}\n\n"
            f"## Focus\n"
            f"Bias toward: pipeline harness, agent tooling, debugging, speed, learning/RSI, "
            f"workflows/connectors, and safe experiments — NOT random consumer apps.\n\n"
            f"## The 6 Categories (5 ideas each = 30 total)\n\n"
            f"**GROUP 1 — PIPELINE CORE**: 5 ideas improving runner, agents, orchestration, "
            f"message bus, subprocess reliability, dropbox steering, or run_loop.\n\n"
            f"**GROUP 2 — DEBUG & QUALITY**: 5 ideas for validator, reviewer, health checks, "
            f"test harness, failure analysis, or bug memory.\n\n"
            f"**GROUP 3 — SPEED & EFFICIENCY**: 5 ideas for context cache, parallel seeds, "
            f"token savings, faster iteration, or cheaper model routing.\n\n"
            f"**GROUP 4 — LEARNING & RSI**: 5 ideas for finetune corpus, metrics, capability "
            f"registry learning, constitutional patcher, or self-improvement loops.\n\n"
            f"**GROUP 5 — AGENTIC & BRIDGE**: 5 ideas linking 2+ existing capabilities via "
            f"workflows/connectors/MCP. Each line MUST include "
            f"`kind:connector requires: slug_a, slug_b` using exact slugs.\n\n"
            f"**GROUP 6 — EXPERIMENTS**: 5 ideas for dynamic routing, A/B agents, feature flags, "
            f"or novel pipeline experiments (mention kind:experiment in description).\n\n"
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

        if deconstruct_block and raw_text.strip():
            refine_messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"## Deconstruct pass\n{deconstruct_block}\n\n"
                        f"Refine these ideas. Output ONLY idea lines (- [ ] **[Title]** — ...):\n\n"
                        f"{raw_text[:12000]}"
                    ),
                },
            ]
            try:
                refined = llm.chat(refine_messages)
                if refined.content and re.search(r"^\s*-\s*\[[ xX]\]", refined.content, re.M):
                    raw_text = refined.content
            except Exception as exc:
                logger.warning("[ideator] Deconstruct pass failed (non-fatal): %s", exc)

        # --- Parse idea lines from response ---
        idea_lines = [
            line.strip()
            for line in raw_text.splitlines()
            if re.match(r"^\s*-\s*\[[ xX]\]", line)
        ]

        # Force all generated ideas to unchecked [ ]
        idea_lines = [re.sub(r"\[[ xX]\]", "[ ]", l) for l in idea_lines]

        # --- Bridge / agentic → connector YAML (GROUP 5) ---
        synth_summary: dict = {}
        try:
            from pipeline.connector_synthesis import process_ideator_generation, write_synthesis_log

            idea_lines, synth_summary = process_ideator_generation(raw_text, idea_lines)
            if synth_summary.get("written") or synth_summary.get("skipped"):
                write_synthesis_log(synth_summary, ts)
                logger.info(
                    "[ideator] Connector YAML written=%s skipped=%s",
                    synth_summary.get("written"),
                    synth_summary.get("skipped"),
                )
        except Exception as e:
            logger.warning("[ideator] Connector synthesis failed (non-fatal): %s", e)

        # --- Tag harness/experiment; queue harness in capability_gaps ---
        enrich_summary: dict = {}
        try:
            from pipeline.ideator_enrich import enrich_ideator_lines

            # Match groups by title (lines may already have kind:connector from synthesis)
            idea_lines, enrich_summary = enrich_ideator_lines(raw_text, idea_lines)
        except Exception as e:
            logger.warning("[ideator] Enrich failed (non-fatal): %s", e)

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

        connector_note = ""
        if synth_summary.get("written"):
            connector_note = f"; connector YAML: {len(synth_summary['written'])} created"
        summary = (
            f"Generated {len(idea_lines)} new ideas and appended to master_ideas.md{connector_note}"
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
