"""
pipeline/agents/ship_evaluator.py
Final shippability gate: tests sufficient? ready for field_proven?
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.field_test_runner import format_results_markdown, run_all_field_tests
from pipeline.message_bus import Message
from pipeline.ship_provenance import load_provenance, save_provenance, set_maturity


class ShipEvaluatorAgent(AgentProcess):
    role = "ship_evaluator"
    model_tier = "light"
    num_ctx = 8192
    max_steps = 6
    phase_timeout = 600
    temperature = 0.25
    think = False

    def handle(self, msg: Message) -> AgentOutput:
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        phase_num = msg.payload.get("phase", 1)
        workspace = self.get_workspace_path()
        eval_path = "phases/ship/ship_evaluation.md"
        eval_full = self._project_path(eval_path)

        self._update_idea_status("ship_evaluating")

        prov = load_provenance(self._project_dir)
        field_results = self.read_state_file("phases/ship/field_test_results.md") or ""
        field_tests = self.read_state_file("phases/ship/field_tests.md") or ""
        thermo_review = self.read_state_file("phases/ship/thermo_review.md") or ""
        debug_report = self.read_state_file("phases/ship/debug_report.md") or ""
        master_plan = self.read_state_file("state/master_plan.md") or ""

        task_prompt = (
            f"You are the final ship-prove evaluator.\n\n"
            f"## Project\n{idea_slug}\n\n"
            f"## Master plan\n{master_plan[:1500]}\n\n"
            f"## Field test plan\n{field_tests[:2500]}\n\n"
            f"## Field test results\n{field_results[:3000]}\n\n"
            f"## Thermo review\n{thermo_review[:2000] or '(skipped)'}\n\n"
            f"## Debug history\n{debug_report[:1500] or '(none)'}\n\n"
            f"## Questions\n"
            f"1. Is phase work fully validated?\n"
            f"2. Did field tests prove the stated purpose (not just syntax)?\n"
            f"3. Is the test plan sufficient or should more field tests be generated?\n\n"
            f"Write `{eval_full}` with sections:\n"
            f"## Phase validation\n## Field test adequacy\n## Shippability\n"
            f"## Recommended maturity (M2 field-tested / M3 refactored-debugged)\n"
            f"## Verdict\n"
            f"Use exactly one of:\n"
            f"- Verdict: FIELD_PROVEN\n"
            f"- Verdict: NEEDS_MORE_FIELD_TESTS\n"
            f"- Verdict: SHIP_INSUFFICIENT\n"
            f"Say DONE when written.\n"
        )

        result = self.call_llm_direct(task_prompt)
        eval_content = self.read_state_file(eval_path)
        if not eval_content.strip():
            eval_content = result.answer or ""
            if eval_content:
                self.write_state_file(eval_path, eval_content)

        verdict = self._parse_verdict(eval_content)
        outgoing: list[Message] = []

        if verdict == "NEEDS_MORE_FIELD_TESTS":
            self._update_idea_status("field_test_planning")
            outgoing.append(
                Message.create(
                    from_agent=self.role,
                    to_agent="field_test_planner",
                    type="task",
                    payload={"idea_slug": idea_slug, "phase": phase_num},
                    priority=1,
                )
            )
        elif verdict == "SHIP_INSUFFICIENT":
            self._update_idea_status("ship_insufficient")
        else:
            # Re-run field tests deterministically before final proven
            tests_file = self._project_dir / "phases/ship/field_tests.md"
            run = run_all_field_tests(workspace, tests_file, include_baseline=True)
            if not run.all_passed:
                self.write_state_file(
                    "phases/ship/field_test_results.md",
                    format_results_markdown(run),
                )
                self._update_idea_status("field_test_failed")
                outgoing.append(
                    Message.create(
                        from_agent=self.role,
                        to_agent="debug_loop",
                        type="task",
                        payload={
                            "idea_slug": idea_slug,
                            "phase": phase_num,
                            "field_test_results_path": "phases/ship/field_test_results.md",
                        },
                        priority=1,
                    )
                )
            else:
                self._update_idea_status("field_proven")
                thermo_done = bool(prov.get("thermo_reviewed")) or not thermo_review
                debug_loops = int(prov.get("debug_loops", 0))
                if thermo_done and (debug_loops > 0 or prov.get("field_test_loops", 0) > 0):
                    set_maturity(self._project_dir, "M3")
                else:
                    set_maturity(self._project_dir, "M2")
                save_provenance(
                    self._project_dir,
                    {**load_provenance(self._project_dir), "ship_evaluated": True},
                )

        return AgentOutput(
            success=verdict == "FIELD_PROVEN",
            answer=result.answer,
            outgoing=outgoing,
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )

    def _parse_verdict(self, content: str) -> str:
        if re.search(r"Verdict:\s*NEEDS_MORE_FIELD_TESTS", content, re.IGNORECASE):
            return "NEEDS_MORE_FIELD_TESTS"
        if re.search(r"Verdict:\s*SHIP_INSUFFICIENT", content, re.IGNORECASE):
            return "SHIP_INSUFFICIENT"
        if re.search(r"Verdict:\s*FIELD_PROVEN", content, re.IGNORECASE):
            return "FIELD_PROVEN"
        return "SHIP_INSUFFICIENT"


def main() -> None:
    import argparse
    import logging

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="ollama")
    from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL

    parser.add_argument("--model", default=DEFAULT_PIPELINE_MODEL)
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [ship_evaluator] %(message)s",
    )
    agent = ShipEvaluatorAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
