"""
pipeline/agents/idea_planner.py
Idea Planner agent — turns a raw idea into a multi-phase master plan.

Receives: idea description (from user or master_ideas.md)
Produces: master_plan.md, sends Phase 1 spec to Phase Planner
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message


class IdeaPlannerAgent(AgentProcess):
    role = "idea_planner"
    model_tier = "light"
    num_ctx = 8192
    max_steps = 15
    phase_timeout = 900   # 15 min — planning should not block the pipeline for 45m
    temperature = 0.5   # needs to reason about architecture — moderate creativity
    think = False       # thinking burns ctx/steps on local Qwen; plan in prose instead

    def handle(self, msg: Message) -> AgentOutput:
        idea_description = msg.payload.get("idea", "")
        idea_title = msg.payload.get("title", "Untitled Idea")
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        priority_tier = msg.payload.get("priority_tier", 0)

        depends_on: list = msg.payload.get("depends_on", [])
        dep_workspaces: dict = msg.payload.get("dep_workspaces", {})

        master_plan_path = self._project_path("state/master_plan.md")

        # Build dependency context block if this project integrates with others
        dep_context = ""
        if depends_on and dep_workspaces:
            dep_lines = []
            for dep_slug, ws_path in dep_workspaces.items():
                dep_lines.append(
                    f"  - **{dep_slug}**: workspace at `{ws_path}`\n"
                    f"    Use `list_tree` on this path to discover its API surface,\n"
                    f"    data models, and file structure BEFORE writing your plan.\n"
                    f"    Your plan MUST be compatible with these existing interfaces."
                )
            dep_context = (
                f"## Dependencies (existing projects to integrate with)\n"
                + "\n".join(dep_lines)
                + "\n\nIMPORTANT: Read the dependency workspaces above before planning. "
                + "Your master plan must specify exactly which files/classes/functions "
                + "from the dependencies this project will import and extend.\n\n"
            )
        elif depends_on:
            # Deps declared but workspaces not built yet (shouldn't happen, but be safe)
            dep_context = (
                f"## Dependencies\nThis project depends on: {', '.join(depends_on)}.\n"
                f"Design your plan to integrate cleanly with these projects.\n\n"
            )

        task_prompt = (
            f"You are the Idea Planner. Create a multi-phase implementation plan.\n\n"
            f"## Idea\n**{idea_title}**\n\n{idea_description}\n\n"
            + dep_context +
            f"## Instructions\n"
            f"1. Analyze the idea and identify the core deliverable.\n"
            f"2. Break it into exactly 3 phases by default. Phase 1 must be the smallest\n"
            f"   useful thing (MVP). Only use 4-6 phases if the idea genuinely requires it\n"
            f"   (e.g. multiple distinct subsystems that can't ship together).\n"
            f"3. Output the full master plan as markdown in your response"
            + (f" and also write it to `{master_plan_path}`." if dep_workspaces else ".")
            + "\n"
            f"4. Each phase needs: description, deliverable, dependencies, success criteria.\n"
            f"5. Include architecture notes and risks.\n"
            f"6. Say DONE.\n"
        )

        if dep_workspaces:
            result = self.call_agent(task=task_prompt, verbose=False)
        else:
            # Tool-calling via Ollama on 35B models often hangs 10–30m; direct completion is reliable.
            result = self.call_llm_direct(task_prompt)
            plan_text = self._extract_plan_markdown(result.answer)
            if plan_text:
                self.write_state_file("state/master_plan.md", plan_text)


        # Read the master plan to extract Phase 1
        master_plan = self.read_state_file("state/master_plan.md")
        if not master_plan:
            # LLM failed to write master_plan — generate minimal plan
            master_plan = (
                f"# {idea_title} — Master Plan\n\n"
                f"## Idea Summary\n{idea_description[:500]}\n\n"
                f"## Phase 1: Core MVP\n"
                f"**Goal**: Build the minimum viable version of {idea_title}.\n"
                f"**Deliverable**: Working prototype with core functionality.\n"
                f"**Success Criteria**: Core features work and are importable.\n\n"
                f"## Phase 2: Testing & Polish\n"
                f"**Goal**: Add tests, error handling, and documentation.\n"
                f"**Deliverable**: Test suite passing, README complete.\n\n"
                f"## Phase 3: Integration & Documentation\n"
                f"**Goal**: Final integration, CLI/API surface, and deployment docs.\n"
                f"**Deliverable**: Production-ready package.\n"
            )
            self.write_state_file("state/master_plan.md", master_plan)
        phase_1_spec = self._extract_phase(master_plan, 1)


        # Save current idea state
        self.write_json_state("state/current_idea.json", {
            "title": idea_title,
            "description": idea_description[:500],
            "status": "planning",
            "phase": 1,
            "total_phases": self._count_phases(master_plan),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "depends_on": depends_on,
            "priority_tier": priority_tier,
        })


        # Send Phase 1 to Phase Planner
        out_msg = Message.create(
            from_agent=self.role,
            to_agent="phase_planner",
            type="task",
            payload={
                "phase": 1,
                "phase_spec": phase_1_spec,
                "idea_slug": idea_slug,
                "idea_title": idea_title,
            },
        )

        return AgentOutput(
            success=result.completed,
            answer=result.answer,
            outgoing=[out_msg],
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )

    def _extract_plan_markdown(self, text: str) -> str:
        """Pull master-plan markdown from a direct LLM response."""
        if not text:
            return ""
        fenced = re.search(r"```(?:markdown)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if fenced:
            text = fenced.group(1).strip()
        for marker in (r"#\s*Master Plan", r"##\s*Phase\s+1"):
            match = re.search(marker, text, re.IGNORECASE)
            if match:
                text = text[match.start():]
                break
        return re.sub(r"\nDONE\s*$", "", text, flags=re.IGNORECASE).strip()

    def _extract_phase(self, master_plan: str, phase_num: int) -> str:
        """Extract a specific phase section from the master plan."""
        if not master_plan:
            return f"Phase {phase_num} — (no plan available)"

        # Try to find the phase section using common heading patterns
        patterns = [
            rf"(## Phase {phase_num}[:\s].*?)(?=## Phase \d|## Architecture|## Risks|$)",
            rf"(### Phase {phase_num}[:\s].*?)(?=### Phase \d|### Architecture|### Risks|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, master_plan, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return f"Phase {phase_num} — see master plan for details"

    def _count_phases(self, master_plan: str) -> int:
        """Count implementation phases in the master plan (## or ### headings)."""
        seen: set[int] = set()
        for match in re.finditer(r"#{2,3}\s+Phase\s+(\d+)", master_plan, re.IGNORECASE):
            seen.add(int(match.group(1)))
        return max(seen) if seen else 1


def main():
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL
    parser.add_argument("--model", default=DEFAULT_PIPELINE_MODEL)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [idea_planner] %(message)s")

    agent = IdeaPlannerAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
