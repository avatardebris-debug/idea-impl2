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

        # Read broader project context for quality review
        master_plan = self.read_state_file("state/master_plan.md")
        phase_spec = self.read_state_file(f"phases/phase_{phase_num}/spec.md")
        overflow_tasks = self.read_state_file(f"phases/phase_{phase_num}_overflow/tasks.md")

        # Build context sections
        project_context = ""
        if master_plan:
            project_context += f"## Project Master Plan (full vision)\n{master_plan[:1500]}\n\n"
        if phase_spec:
            project_context += f"## This Phase's Spec\n{phase_spec[:1000]}\n\n"
        if overflow_tasks:
            project_context += (
                f"## Overflow Tasks (batch 2 — runs after this batch validates)\n"
                f"{overflow_tasks[:1000]}\n\n"
                f"⚠️ The current code must work INDEPENDENTLY of these overflow tasks.\n"
                f"If batch 1 code depends on something only in overflow, flag it as a blocking bug.\n\n"
            )

        task_prompt = (
            f"You are reviewing Phase {phase_num} code.\n\n"
            + project_context
            + f"## Task Spec\n{tasks_content}\n\n"
            f"## Validation Report\n{validation_content[:2000]}\n\n"
            f"## Workspace\n"
            f"Code is in: {workspace_path}\n"
            f"Files: {', '.join(files_written) if files_written else '(use list_tree)'}\n\n"
            f"## Your Job\n"
            f"1. Read EVERY code file in {workspace_path}.\n"
            f"2. Review each file line by line.\n"
            f"3. Check: does this code align with the master plan's architecture?\n"
            f"4. If overflow tasks exist: can this batch run and validate WITHOUT them?\n"
            f"5. Write your structured review to `{review_full_path}` using EXACTLY\n"
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
            f"6. A phase PASSES if '## Blocking Bugs' contains only 'None' or zero bullets.\n"
            f"7. If the verdict is PASS and '## Reusable Components' lists anything:\n"
            f"   a. For each reusable component, copy the relevant file(s) to a subfolder:\n"
            f"      `{shared_libs_path}/<component_name>/`\n"
            f"   b. Append a one-line entry to `{reusable_tools_path}`:\n"
            f"      `- <component_name>: <what it does> (source: {workspace_path})`\n"
            f"   Only copy self-contained, general-purpose code — not project-specific logic.\n"
            f"8. Say DONE.\n"
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
            if re.search(r'^[-*]\s+', raw, re.MULTILINE):
                non_blocking_notes = raw

        # --- Determine review mode: pre-validation or post-validation ---
        # Pre-validation: reviewer comes from executor BEFORE tests run
        # Post-validation: reviewer comes from validator AFTER tests pass
        validation_report_content = self.read_state_file(validation_path)
        is_post_validation = (
            validation_report_content
            and "Verdict: PASS" in validation_report_content
        )

        if is_post_validation:
            # --- POST-VALIDATION: Deep review → write verdict to state for runner ---
            try:
                idea_state = self.read_json_state("state/current_idea.json")

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
        else:
            # --- PRE-VALIDATION: Structural review → route to validator or back to executor ---
            retry_count = msg.payload.get("retry_count", 0)
            MAX_PRE_VALIDATION_RETRIES = 3

            # If the reviewer LLM failed to produce output, don't blame the executor —
            # just forward to validator and let the post-validation path handle it.
            review_was_generated = "review file was not generated" not in review_content

            if blocking_count > 0 and review_was_generated and retry_count < MAX_PRE_VALIDATION_RETRIES:
                # Structural issues found — send back to executor, skip validation
                import logging as _log
                _log.getLogger(__name__).info(
                    "[reviewer] Pre-validation: %d blocking bugs → executor (attempt %d/%d)",
                    blocking_count, retry_count + 1, MAX_PRE_VALIDATION_RETRIES,
                )
                out_msg = Message.create(
                    from_agent=self.role,
                    to_agent="executor",
                    type="task",
                    payload={
                        "phase": phase_num,
                        "tasks_path": tasks_path,
                        "workspace_path": workspace_path,
                        "fix_required": True,
                        "review_path": review_path,
                        "fix_instructions": (
                            f"Reviewer found {blocking_count} blocking bugs BEFORE validation. "
                            f"Read `{review_full_path}` for details. Fix these structural "
                            f"issues first — tests have NOT been run yet."
                        ),
                        "idea_slug": idea_slug,
                        "retry_count": retry_count + 1,
                    },
                )
                # Update status to reflect we're in fix mode
                self._update_idea_status(f"phase_{phase_num}_executing")
            else:
                # Clean structure — forward to validator for test execution
                out_msg = Message.create(
                    from_agent=self.role,
                    to_agent="validator",
                    type="task",
                    payload={
                        "phase": phase_num,
                        "tasks_path": tasks_path,
                        "workspace_path": workspace_path,
                        "files_written": files_written,
                        "validation_report_path": validation_path,
                        "review_path": review_path,
                        "idea_slug": idea_slug,
                        "retry_count": msg.payload.get("retry_count", 0),
                    },
                )

            return AgentOutput(
                success=True,
                answer=result.answer,
                outgoing=[out_msg],
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
