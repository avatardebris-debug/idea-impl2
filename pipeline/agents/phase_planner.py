"""
pipeline/agents/phase_planner.py
Phase Planner agent — breaks a phase spec into concrete ordered tasks.

Receives: phase spec from Idea Planner (via Manager)
Produces: phase_N/tasks.md, sends first task batch to Executor
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message


class PhasePlannerAgent(AgentProcess):
    role = "phase_planner"
    max_steps = 15
    temperature = 0.4   # slight creativity helps with edge-case task decomposition
    think = True        # reasoning here pays dividends for every downstream agent

    def handle(self, msg: Message) -> AgentOutput:
        phase_num = msg.payload.get("phase", 1)
        phase_spec = msg.payload.get("phase_spec", "")
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        tasks_path = f"phases/phase_{phase_num}/tasks.md"
        tasks_full_path = self._project_path(tasks_path)

        self._update_idea_status(f"phase_{phase_num}_planning")

        # Read master plan for full context
        master_plan = self.read_state_file("state/master_plan.md")

        # Read existing workspace to know what already exists
        workspace = self.get_workspace_path()

        task_prompt = (
            f"You are planning Phase {phase_num} of a project.\n\n"
            f"## Master Plan\n{master_plan[:3000]}\n\n"
            f"## This Phase's Spec\n{phase_spec}\n\n"
            f"## Instructions\n"
            f"1. Read the existing workspace with `list_tree` on {workspace} "
            f"to see what's already built.\n"
            f"2. Break this phase into 3-6 concrete, ordered coding tasks.\n"
            f"3. Write the task list to `{tasks_full_path}` using EXACTLY this format:\n\n"
            f"   ```\n"
            f"   # Phase {phase_num} Tasks\n\n"
            f"   - [ ] Task 1: <short title>\n"
            f"     - What: <what to build>\n"
            f"     - Files: <which files to create/modify>\n"
            f"     - Done when: <acceptance criteria — specific, testable>\n\n"
            f"   - [ ] Task 2: ...\n"
            f"   ```\n\n"
            f"   CRITICAL: Every task MUST start with `- [ ]`. "
            f"The executor marks tasks done with `- [x]` as it works.\n"
            f"   Do NOT use ## headings for tasks. Do NOT use ✅ or other symbols.\n"
            f"4. Say DONE.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)

        # --- Validate tasks.md was written ---
        tasks_content = self.read_state_file(tasks_path)

        # Guardrail: cap at MAX_TASKS_PER_PHASE
        MAX_TASKS_PER_PHASE = 8
        import re as _re
        import logging
        logger = logging.getLogger(__name__)

        if tasks_content:
            lines = tasks_content.split("\n")
            task_indices = [i for i, l in enumerate(lines) if l.strip().startswith("- [ ]")]
            if len(task_indices) > MAX_TASKS_PER_PHASE:
                logger.warning(
                    "[phase_planner] Phase %d has %d tasks (limit %d) — truncating",
                    phase_num, len(task_indices), MAX_TASKS_PER_PHASE,
                )
                cut_at = task_indices[MAX_TASKS_PER_PHASE]
                truncated = "\n".join(lines[:cut_at])
                truncated += f"\n\n<!-- {len(task_indices) - MAX_TASKS_PER_PHASE} tasks removed by guardrail (max {MAX_TASKS_PER_PHASE} per phase) -->\n"
                self.write_state_file(tasks_path, truncated)
                tasks_content = truncated
        else:
            # LLM failed to write tasks.md — generate fallback from spec
            logger.warning("[phase_planner] LLM did not write tasks.md — generating fallback from spec")
            fallback_tasks = self._generate_fallback_tasks(phase_num, phase_spec, master_plan)
            self.write_state_file(tasks_path, fallback_tasks)
            tasks_content = fallback_tasks
            logger.info("[phase_planner] Wrote fallback tasks.md (%d chars)", len(fallback_tasks))

        # Final validation: ensure at least one checkbox exists
        if not _re.search(r'^- \[ \]', tasks_content, _re.MULTILINE):
            logger.warning("[phase_planner] No checkboxes in tasks — using nuclear fallback")
            tasks_content = self._generate_fallback_tasks(phase_num, "", "")
            self.write_state_file(tasks_path, tasks_content)

        # Write phase spec for reference
        self.write_state_file(f"phases/phase_{phase_num}/spec.md", phase_spec or master_plan[:2000])

        # Update current phase state
        self.write_json_state("state/current_phase.json", {
            "phase_num": phase_num,
            "status": "planned",
            "tasks_path": tasks_path,
        })

        # Send to Executor
        out_msg = Message.create(
            from_agent=self.role,
            to_agent="executor",
            type="task",
            payload={
                "phase": phase_num,
                "tasks_path": tasks_path,
                "workspace_path": str(workspace),
                "idea_slug": idea_slug,
            },
        )

        return AgentOutput(
            success=result.completed,
            answer=result.answer,
            outgoing=[out_msg],
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )

    def _generate_fallback_tasks(self, phase_num: int, phase_spec: str, master_plan: str) -> str:
        """Generate a minimal tasks.md from the spec when the LLM fails to write one."""
        import re as _re

        # Pull success criteria bullets from spec
        criteria: list[str] = []
        spec_text = phase_spec or master_plan
        crit_match = _re.search(r'\*\*Success Criteria\*\*[:\s]*(.*?)(?=\*\*|\Z)', spec_text, _re.DOTALL | _re.IGNORECASE)
        if crit_match:
            for line in crit_match.group(1).splitlines():
                line = line.strip().lstrip("- *•").strip()
                if line and len(line) > 10:
                    criteria.append(line)

        # Pull file list from spec
        files: list[str] = []
        files_match = _re.search(r'\*\*Files to Create\*\*[:\s]*(.*?)(?=\*\*|\Z)', spec_text, _re.DOTALL | _re.IGNORECASE)
        if files_match:
            for line in files_match.group(1).splitlines():
                line = line.strip().lstrip("- *•`").strip().rstrip("`").strip()
                if line and ".py" in line:
                    files.append(line.split("—")[0].strip())

        # Build task list (group files into tasks)
        tasks = []
        if files:
            chunk_size = max(1, len(files) // min(6, max(1, len(files))))
            for i in range(0, min(len(files), 6)):
                f = files[i]
                module = f.split("/")[-1].replace(".py", "").replace("_", " ").title()
                crit = criteria[i] if i < len(criteria) else f"Implement and test {module}"
                tasks.append(
                    f"- [ ] Task {i+1}: Implement {module}\n"
                    f"  - What: Create `{f}` as described in the phase spec\n"
                    f"  - Files: `{f}`\n"
                    f"  - Done when: {crit}\n"
                )
        elif criteria:
            for i, crit in enumerate(criteria[:6]):
                tasks.append(
                    f"- [ ] Task {i+1}: {crit[:60]}\n"
                    f"  - What: {crit}\n"
                    f"  - Done when: {crit}\n"
                )
        else:
            # Absolute fallback — 3 generic tasks
            tasks = [
                f"- [ ] Task 1: Implement core Phase {phase_num} functionality\n  - What: Build the primary components described in the phase spec\n  - Done when: Core functionality works and is importable\n",
                f"- [ ] Task 2: Add tests for Phase {phase_num}\n  - What: Write unit tests covering the main code paths\n  - Done when: Tests pass with pytest\n",
                f"- [ ] Task 3: Integration and documentation\n  - What: Integrate with existing phases and update README\n  - Done when: Full pipeline works end-to-end\n",
            ]

        return f"# Phase {phase_num} Tasks\n\n" + "\n".join(tasks)



def main():
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default=__import__("os").environ.get("PIPELINE_MODEL", "qwen3.5:35b"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [phase_planner] %(message)s")

    agent = PhasePlannerAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
