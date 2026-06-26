"""
pipeline/agents/debug_loop.py
Structured bug investigation before executor ship-fix (bug-investigate-fix workflow).
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.import_graph import scan_workspace
from pipeline.message_bus import Message
from pipeline.ship_config import max_debug_loops
from pipeline.ship_provenance import load_provenance, save_provenance


class DebugLoopAgent(AgentProcess):
    role = "debug_loop"
    model_tier = "heavy"
    num_ctx = 12288
    max_steps = 12
    phase_timeout = 1200
    temperature = 0.3
    think = False

    def handle(self, msg: Message) -> AgentOutput:
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        phase_num = msg.payload.get("phase", 1)
        workspace = self.get_workspace_path()
        results_path = msg.payload.get(
            "field_test_results_path", "phases/ship/field_test_results.md"
        )
        debug_path = "phases/ship/debug_report.md"
        debug_full = self._project_path(debug_path)

        self._update_idea_status("field_test_failed")

        field_results = self.read_state_file(results_path) or ""
        tests_spec = self.read_state_file("phases/ship/field_tests.md") or ""
        stale_block = scan_workspace(workspace).format_block()

        task_prompt = (
            f"You are debugging a completed project that FAILED field tests.\n\n"
            f"## Workspace\n{workspace}\n\n"
            f"## Field test results\n{field_results[:6000]}\n\n"
            f"## Field test plan\n{tests_spec[:3000]}\n\n"
            f"## Stale references\n{stale_block}\n\n"
            f"## Workflow (bug-investigate-fix)\n"
            f"1. Reproduce: state minimal repro steps from the failures.\n"
            f"2. Hypotheses: 1-4 ranked, falsifiable root-cause guesses.\n"
            f"3. Confirmed cause: which hypothesis the evidence supports.\n"
            f"4. Fix plan: ≤5 concrete steps for the executor (no scope creep).\n\n"
            f"Write your report to `{debug_full}` using these headings:\n"
            f"## Repro\n## Hypotheses\n## Root cause\n## Fix plan\n## Verification\n\n"
            f"Say DONE when the file is written.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)
        debug_content = self.read_state_file(debug_path)
        if not debug_content.strip():
            debug_content = self._fallback_report(field_results, result.answer)
            self.write_state_file(debug_path, debug_content)

        prov = load_provenance(self._project_dir)
        loops = int(prov.get("debug_loops", 0)) + 1
        save_provenance(self._project_dir, {**prov, "debug_loops": loops})

        outgoing: list[Message] = []
        if loops >= max_debug_loops():
            self._update_idea_status("ship_insufficient")
            return AgentOutput(
                success=False,
                answer=result.answer,
                outgoing=[],
                tokens_used=result.tokens_used,
                steps_used=result.steps_used,
            )

        outgoing.append(
            Message.create(
                from_agent=self.role,
                to_agent="executor",
                type="task",
                payload={
                    "phase": phase_num,
                    "idea_slug": idea_slug,
                    "ship_fix": True,
                    "debug_report_path": debug_path,
                    "field_test_results_path": results_path,
                    "tasks_path": f"phases/phase_{phase_num}/tasks.md",
                    "workspace_path": str(workspace),
                    "fix_required": True,
                    "error_summary": "Field tests failed — apply debug_report fix plan.",
                    "validation_report": debug_content[:4000],
                },
                priority=1,
            )
        )

        return AgentOutput(
            success=True,
            answer=result.answer,
            outgoing=outgoing,
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )

    def _fallback_report(self, field_results: str, answer: str) -> str:
        body = answer[:4000] if answer else field_results[:2000]
        return (
            "# Debug Report\n\n"
            "## Repro\nSee field test results.\n\n"
            "## Hypotheses\n- Implementation does not meet field test expectations\n\n"
            "## Root cause\nTo be confirmed by executor fix.\n\n"
            f"## Fix plan\n{body}\n\n"
            "## Verification\nRe-run field tests after fix.\n"
        )


def main() -> None:
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL

    parser.add_argument("--model", default=DEFAULT_PIPELINE_MODEL)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [debug_loop] %(message)s")
    agent = DebugLoopAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
