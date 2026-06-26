"""
pipeline/agents/thermo_reviewer.py
Thermo-nuclear code quality review after field tests pass.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.message_bus import Message
from pipeline.review_artifacts import count_blocking_bugs, review_artifacts_complete
from pipeline.ship_provenance import load_provenance, save_provenance
from pipeline.ship_snapshots import snapshot_workspace


class ThermoReviewerAgent(AgentProcess):
    role = "thermo_reviewer"
    model_tier = "heavy"
    num_ctx = 12288
    max_steps = 15
    phase_timeout = 1800
    temperature = 0.3
    think = False

    def handle(self, msg: Message) -> AgentOutput:
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        phase_num = msg.payload.get("phase", 1)
        workspace = self.get_workspace_path()
        review_path = "phases/ship/thermo_review.md"
        review_full = self._project_path(review_path)

        self._update_idea_status("thermo_reviewing")

        pre_dir = self._project_dir / "workspace_pre_review"
        snapshot_workspace(workspace, pre_dir)

        master_plan = self.read_state_file("state/master_plan.md") or ""
        field_results = self.read_state_file("phases/ship/field_test_results.md") or ""

        task_prompt = (
            f"You are performing a thermo-nuclear code quality review (ship-prove track).\n\n"
            f"## Workspace\n{workspace}\n\n"
            f"## Master plan\n{master_plan[:2000]}\n\n"
            f"## Field tests (already passed)\n{field_results[:2000]}\n\n"
            f"## Rules\n"
            f"- Prefer code judo: smallest change that improves quality.\n"
            f"- Flag files >1000 lines for split.\n"
            f"- Check cross-file imports and stale references after any refactor.\n"
            f"- Do NOT change behavior unless fixing a real bug.\n\n"
            f"Write review to `{review_full}` with headings:\n"
            f"### What's Good\n## Blocking Bugs\n## Non-Blocking Notes\n"
            f"## Refactor plan\n## Verdict\n"
            f"PASS if no blocking bugs; FAIL otherwise.\n"
            f"Say DONE when written.\n"
        )

        result = self.call_agent(task=task_prompt, verbose=False)
        review_content = self.read_state_file(review_path)
        if not review_content.strip():
            review_content = result.answer or ""
            if review_content:
                self.write_state_file(review_path, review_content)

        blocking = count_blocking_bugs(review_content)
        complete = review_artifacts_complete(review_content)
        has_fail = (
            blocking > 0
            or (complete and re.search(r"verdict:\s*FAIL", review_content, re.IGNORECASE))
        )

        prov = load_provenance(self._project_dir)
        outgoing: list[Message] = []

        if has_fail:
            self._update_idea_status("thermo_refactoring")
            outgoing.append(
                Message.create(
                    from_agent=self.role,
                    to_agent="executor",
                    type="task",
                    payload={
                        "phase": phase_num,
                        "idea_slug": idea_slug,
                        "thermo_refactor": True,
                        "thermo_review_path": review_path,
                        "workspace_path": str(workspace),
                        "fix_required": True,
                        "error_summary": "Thermo review found blocking issues.",
                        "validation_report": review_content[:4000],
                    },
                    priority=1,
                )
            )
        else:
            save_provenance(self._project_dir, {**prov, "thermo_reviewed": True})
            self._update_idea_status("ship_evaluating")
            outgoing.append(
                Message.create(
                    from_agent=self.role,
                    to_agent="ship_evaluator",
                    type="task",
                    payload={"idea_slug": idea_slug, "phase": phase_num},
                    priority=1,
                )
            )

        return AgentOutput(
            success=not has_fail,
            answer=result.answer,
            outgoing=outgoing,
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )


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
        format="%(asctime)s [thermo_reviewer] %(message)s",
    )
    agent = ThermoReviewerAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
