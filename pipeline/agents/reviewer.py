"""
pipeline/agents/reviewer.py
Reviewer agent — performs detailed line-by-line code review.

Receives: workspace + validation report after Validator passes
Produces: review.md, writes verdict to current_idea.json for deterministic
          routing by the runner's _tick_project() function.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message


class ReviewerAgent(AgentProcess):
    role = "reviewer"
    max_steps = 25
    temperature = 0.3   # structured assessment — slightly creative but mostly deterministic
    think = False       # follows fixed review template — no CoT needed

    def handle(self, msg: Message) -> AgentOutput:
        phase_num = msg.payload.get("phase", 1)
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        workspace_path = msg.payload.get("workspace_path", str(self.get_workspace_path()))
        files_written = msg.payload.get("files_written", [])
        validation_path = msg.payload.get("validation_report_path",
                                          f"phases/phase_{phase_num}/validation_report.md")
        review_path = msg.payload.get("review_path",
                                      f"phases/phase_{phase_num}/review.md")
        tasks_path = msg.payload.get("tasks_path",
                                     f"phases/phase_{phase_num}/tasks.md")
        review_full_path = self._project_path(review_path)

        self._update_idea_status(f"phase_{phase_num}_reviewing")

        # Read context
        tasks_content = self.read_state_file(tasks_path)
        validation_content = self.read_state_file(validation_path)

        shared_libs_path = str(self._run_dir / ".pipeline" / "shared_libs")
        reusable_tools_path = str(self._run_dir / ".pipeline" / "state" / "reusable_tools.md")

        task_prompt = (
            f"You are reviewing Phase {phase_num} code.\n\n"
            f"## Task Spec\n{tasks_content}\n\n"
            f"## Validation Report\n{validation_content[:2000]}\n\n"
            f"## Workspace\n"
            f"Code is in: {workspace_path}\n"
            f"Files: {', '.join(files_written) if files_written else '(use list_tree)'}\n\n"
            f"## Your Job\n"
            f"1. Read EVERY code file in {workspace_path}.\n"
            f"2. Review each file line by line.\n"
            f"3. Write your structured review to `{review_full_path}` using EXACTLY\n"
            f"   these section headings (in this order):\n\n"
            f"   ### What's Good\n"
            f"   (bullet list of things working correctly)\n\n"
            f"   ## Blocking Bugs\n"
            f"   (ONLY issues that will cause crashes, wrong output, or test failures)\n"
            f"   (reference file:line for each — if none write 'None')\n\n"
            f"   ## Non-Blocking Notes\n"
            f"   (style, naming, future improvements — do NOT list these as bugs)\n\n"
            f"   ## Reusable Components\n"
            f"   (list any self-contained utilities, helpers, or classes that could be\n"
            f"   reused by other projects — e.g. HTTP client wrapper, PDF parser, auth helper)\n\n"
            f"   ## Verdict\n"
            f"   PASS or FAIL with one-line reason\n\n"
            f"4. A phase PASSES if '## Blocking Bugs' contains only 'None' or zero bullets.\n"
            f"5. If the verdict is PASS and '## Reusable Components' lists anything:\n"
            f"   a. For each reusable component, copy the relevant file(s) to a subfolder:\n"
            f"      `{shared_libs_path}/<component_name>/`\n"
            f"   b. Append a one-line entry to `{reusable_tools_path}`:\n"
            f"      `- <component_name>: <what it does> (source: {workspace_path})`\n"
            f"   Only copy self-contained, general-purpose code — not project-specific logic.\n"
            f"6. Say DONE.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)

        import re
        review_content = self.read_state_file(review_path)

        # Guard: if LLM didn't write review.md, synthesize conservative FAIL
        if not review_content:
            review_content = (
                f"# Code Review — Phase {phase_num}\n\n"
                f"## Blocking Bugs\n- Review could not be completed (LLM did not write review file)\n\n"
                f"## Non-Blocking Notes\nNone\n\n"
                f"## Verdict\nFAIL — review file was not generated\n"
            )
            self.write_state_file(review_path, review_content)
        # Count only bullets under '## Blocking Bugs' — non-blocking notes are deferred work
        bugs_section = re.search(
            r'## Blocking Bugs.*?(?=## |$)', review_content, re.DOTALL | re.IGNORECASE
        )
        if bugs_section:
            section_text = bugs_section.group()
            if re.search(r'\bnone\b', section_text, re.IGNORECASE):
                blocking_count = 0
            else:
                blocking_count = len(re.findall(r'^[-*]\s+', section_text, re.MULTILINE))
        else:
            blocking_count = 0

        # Extract non-blocking notes to pass through for deferred scheduling
        non_blocking_section = re.search(
            r'## Non-Blocking Notes.*?(?=## |$)', review_content, re.DOTALL | re.IGNORECASE
        )
        non_blocking_notes = ""
        if non_blocking_section:
            raw = non_blocking_section.group().strip()
            # Only capture if there are actual bullet items (not just the heading)
            if re.search(r'^[-*]\s+', raw, re.MULTILINE):
                non_blocking_notes = raw

        # --- Write review verdict to state (deterministic routing by runner) ---
        # Instead of sending to the manager LLM, we write structured review data
        # directly to current_idea.json. The runner's _tick_project() reads this
        # and makes the routing decision deterministically.
        try:
            idea_state = self.read_json_state("state/current_idea.json")

            # Guard: don't overwrite terminal states — the runner may have
            # force-completed this project while the reviewer was still running
            if idea_state.get("status") in ("complete", "stalled", "budget_exceeded"):
                return AgentOutput(
                    success=True, answer=result.answer, outgoing=[],
                    tokens_used=result.tokens_used, steps_used=result.steps_used,
                )

            idea_state["review_result"] = {
                "blocking_bugs": blocking_count,
                "review_path": review_path,
                "tasks_path": tasks_path,
                "workspace_path": workspace_path,
                "files_written": files_written,
                "non_blocking_notes": non_blocking_notes[:1500],
                "review_content_preview": review_content[:1500],
            }
            idea_state["status"] = f"phase_{phase_num}_reviewed"
            self.write_json_state("state/current_idea.json", idea_state)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("[reviewer] Failed to write review verdict: %s", e)

        return AgentOutput(
            success=True,
            answer=result.answer,
            outgoing=[],  # No outgoing messages — runner handles routing
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

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [reviewer] %(message)s")

    agent = ReviewerAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
