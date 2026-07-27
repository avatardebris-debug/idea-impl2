"""
pipeline/agents/ship_evaluator.py
Final shippability gate: tests adequate? ready for field_proven?

Dual gate:
  field_test_passed — runner all_passed (mechanical; set earlier on classic path)
  field_proven      — runner re-run all_passed AND ADEQUATE AND min P*/I* bars

Evaluator assumes overclaim. Must not invent command passes.
Closed adequacy: ADEQUATE | NEEDS_MORE_FIELD_TESTS | SHIP_INSUFFICIENT
(Legacy Verdict: FIELD_PROVEN maps to ADEQUATE.)

Status decisions go through pipeline.field_prove_gate.decide_field_status
(same gate as thin ship) so bars/env rules cannot drift.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.field_prove_gate import (
    VERDICT_ADEQUATE,
    VERDICT_FIELD_PROVEN,
    VERDICT_INSUFFICIENT,
    VERDICT_NEEDS_MORE,
    assess_plan_bars,
    decide_field_status,
    normalize_adequacy,
    parse_adequacy_verdict,
)
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

        bars = assess_plan_bars(field_tests)
        bars_summary = (
            f"product_nontrivial={bars.product_nontrivial}/{bars.min_product}, "
            f"integration_nontrivial={bars.integration_nontrivial}/{bars.min_integration}, "
            f"weak_plan={bars.weak_plan}, meets_min_bars={bars.meets_min_bars}"
        )

        task_prompt = (
            f"You are the final adversarial ship-prove evaluator.\n\n"
            f"## Project\n{idea_slug}\n\n"
            f"## Master plan\n{master_plan[:1500]}\n\n"
            f"## Field test plan\n{field_tests[:2500]}\n\n"
            f"## Field test results (durable evidence — do not invent passes)\n"
            f"{field_results[:3000] or '(MISSING — treat as insufficient)'}\n\n"
            f"## Thermo review\n{thermo_review[:2000] or '(skipped)'}\n\n"
            f"## Debug history\n{debug_report[:1500] or '(none)'}\n\n"
            f"## Deterministic plan bars (pre-computed; trust this for counts)\n"
            f"{bars_summary}\n"
            f"Reasons: {'; '.join(bars.reasons)}\n\n"
            f"## Stance\n"
            f"Assume the plan OVERCLAIMS. Baseline B* and help/syntax/import-only "
            f"smoke never prove product aim. You may not invent command results.\n\n"
            f"## Questions\n"
            f"1. Is phase work fully validated?\n"
            f"2. Did field tests prove the stated purpose (not just syntax)?\n"
            f"3. Is the test plan sufficient or should more field tests be generated?\n\n"
            f"Write `{eval_full}` with sections:\n"
            f"## Phase validation\n## Field test adequacy\n## Shippability\n"
            f"## Recommended maturity (M2 field-tested / M3 refactored-debugged)\n"
            f"## Verdict\n"
            f"Under Verdict emit exactly one Adequacy line and one Verdict line:\n"
            f"- Adequacy: ADEQUATE\n"
            f"- Adequacy: NEEDS_MORE_FIELD_TESTS\n"
            f"- Adequacy: SHIP_INSUFFICIENT\n"
            f"And map:\n"
            f"- Adequacy ADEQUATE → Verdict: FIELD_PROVEN "
            f"(only if results show real passes and bars can be met)\n"
            f"- Adequacy NEEDS_MORE_FIELD_TESTS → Verdict: NEEDS_MORE_FIELD_TESTS\n"
            f"- Adequacy SHIP_INSUFFICIENT → Verdict: SHIP_INSUFFICIENT\n"
            f"If plan is weak/baseline-only or bars not met → NEEDS_MORE_FIELD_TESTS "
            f"or SHIP_INSUFFICIENT, never ADEQUATE.\n"
            f"Say DONE when written.\n"
        )

        result = self.call_llm_direct(task_prompt)
        eval_content = self.read_state_file(eval_path)
        if not eval_content.strip():
            eval_content = result.answer or ""
            if eval_content:
                self.write_state_file(eval_path, eval_content)

        # Closed adequacy from Adequacy:/Verdict: lines (last-wins parse)
        adequacy = normalize_adequacy(parse_adequacy_verdict(eval_content))
        if adequacy == VERDICT_INSUFFICIENT:
            raw = self._parse_verdict(eval_content)
            if raw in (VERDICT_ADEQUATE, VERDICT_FIELD_PROVEN, VERDICT_NEEDS_MORE):
                adequacy = normalize_adequacy(raw)

        # Pre-run dual gate: bars + LLM adequacy (optimistic runner=True for bars demotion)
        pre = decide_field_status(
            runner_all_passed=True,
            bars=bars,
            evaluator_verdict=adequacy,
            dual_gate=True,
        )
        if pre.adequacy != adequacy or not pre.field_proven:
            # Persist dual-gate demotion as last lines (last-wins parse will stick)
            if not pre.field_proven and adequacy == VERDICT_ADEQUATE:
                eval_content = (
                    eval_content.rstrip()
                    + "\n\n## Dual-gate override\n"
                    + f"Adequacy forced — {pre.reason}\n"
                    + f"Adequacy: {pre.adequacy}\n"
                    + f"Verdict: {pre.adequacy}\n"
                )
                self.write_state_file(eval_path, eval_content)
                adequacy = pre.adequacy

        outgoing: list[Message] = []

        # LLM (or demoted) NEEDS_MORE → replan without re-run
        if pre.adequacy == VERDICT_NEEDS_MORE or (
            not pre.field_proven and not bars.meets_min_bars
        ):
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
            return AgentOutput(
                success=False,
                answer=result.answer,
                outgoing=outgoing,
                tokens_used=result.tokens_used,
                steps_used=result.steps_used,
            )

        # Explicit LLM SHIP_INSUFFICIENT (not merely weak bars) → park
        if adequacy == VERDICT_INSUFFICIENT and not pre.field_proven:
            self._update_idea_status("ship_insufficient")
            return AgentOutput(
                success=False,
                answer=result.answer,
                outgoing=outgoing,
                tokens_used=result.tokens_used,
                steps_used=result.steps_used,
            )

        # Candidate ADEQUATE path: re-run field tests (sole execution oracle)
        tests_file = self._project_dir / "phases/ship/field_tests.md"
        run = run_all_field_tests(workspace, tests_file, include_baseline=True)
        results_md = format_results_markdown(run)
        self.write_state_file("phases/ship/field_test_results.md", results_md)

        bars2 = assess_plan_bars(tests_file)
        decision = decide_field_status(
            runner_all_passed=run.all_passed,
            bars=bars2,
            evaluator_verdict=adequacy,
            dual_gate=True,
        )

        # Annotate durable evaluation with final dual-gate decision (last-wins)
        note = (
            (self.read_state_file(eval_path) or eval_content).rstrip()
            + "\n\n## Dual-gate post-run\n"
            + f"- Runner: {'PASS' if decision.runner_all_passed else 'FAIL'}\n"
            + f"- Decision status: {decision.status}\n"
            + f"- Reason: {decision.reason}\n"
            + f"Adequacy: {decision.adequacy}\n"
            + f"Verdict: "
            + (
                VERDICT_FIELD_PROVEN
                if decision.field_proven
                else decision.adequacy
            )
            + "\n"
        )
        self.write_state_file(eval_path, note)

        if not decision.runner_all_passed:
            # Classic recovery: field_test_failed + debug (mechanical fail)
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
            return AgentOutput(
                success=False,
                answer=result.answer,
                outgoing=outgoing,
                tokens_used=result.tokens_used,
                steps_used=result.steps_used,
            )

        if decision.field_proven:
            self._update_idea_status("field_proven")
            thermo_done = bool(prov.get("thermo_reviewed")) or not thermo_review
            debug_loops = int(prov.get("debug_loops", 0))
            if thermo_done and (
                debug_loops > 0 or prov.get("field_test_loops", 0) > 0
            ):
                set_maturity(self._project_dir, "M3")
            else:
                set_maturity(self._project_dir, "M2")
            save_provenance(
                self._project_dir,
                {**load_provenance(self._project_dir), "ship_evaluated": True},
            )
            try:
                from pipeline.github_publish import maybe_publish_project

                maybe_publish_project(idea_slug, trigger="field_proven")
            except Exception:
                import logging

                logging.getLogger(__name__).debug(
                    "github_publish after field_proven skipped", exc_info=True
                )
            return AgentOutput(
                success=True,
                answer=result.answer,
                outgoing=outgoing,
                tokens_used=result.tokens_used,
                steps_used=result.steps_used,
            )

        # Green runner but not proven — map shared gate status
        status = decision.status  # typically field_test_passed
        if decision.adequacy == VERDICT_NEEDS_MORE:
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
        else:
            self._update_idea_status(status)
        return AgentOutput(
            success=False,
            answer=result.answer,
            outgoing=outgoing,
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )

    def _parse_verdict(self, content: str) -> str:
        """Parse closed Verdict / Adequacy lines (last-wins via parse_adequacy_verdict)."""
        # Prefer shared last-wins parser; map ADEQUATE alias
        v = parse_adequacy_verdict(content)
        if v != VERDICT_INSUFFICIENT:
            return v
        # Legacy first-match fallback only if shared parser found nothing closed
        if re.search(
            r"(?:Verdict|Adequacy):\s*NEEDS_MORE_FIELD_TESTS", content, re.IGNORECASE
        ):
            return VERDICT_NEEDS_MORE
        if re.search(
            r"(?:Verdict|Adequacy):\s*SHIP_INSUFFICIENT", content, re.IGNORECASE
        ):
            return VERDICT_INSUFFICIENT
        if re.search(r"(?:Verdict|Adequacy):\s*ADEQUATE\b", content, re.IGNORECASE):
            return VERDICT_ADEQUATE
        if re.search(r"Verdict:\s*FIELD_PROVEN", content, re.IGNORECASE):
            return VERDICT_FIELD_PROVEN
        return VERDICT_INSUFFICIENT


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
