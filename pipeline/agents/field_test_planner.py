"""
pipeline/agents/field_test_planner.py
Generate LLM field tests after status=complete, run hybrid runner, route failures to executor.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from pipeline.agent_process import AgentProcess, AgentOutput
from pipeline.field_test_runner import (
    baseline_tasks,
    format_results_markdown,
    run_all_field_tests,
)
from pipeline.import_graph import scan_workspace
from pipeline.message_bus import Message
from pipeline.ship_provenance import load_provenance, set_maturity


class FieldTestPlannerAgent(AgentProcess):
    role = "field_test_planner"
    model_tier = "light"
    num_ctx = 8192
    max_steps = 8
    phase_timeout = 900
    temperature = 0.35
    think = False

    def handle(self, msg: Message) -> AgentOutput:
        idea_slug = msg.payload.get("idea_slug", self._current_slug)
        workspace = self.get_workspace_path()
        tests_path = "phases/ship/field_tests.md"
        results_path = "phases/ship/field_test_results.md"
        tests_full = self._project_path(tests_path)
        results_full = self._project_path(results_path)

        self._update_idea_status("field_test_planning")

        master_plan = self.read_state_file("state/master_plan.md") or ""
        title = ""
        try:
            st = self.read_json_state("state/current_idea.json")
            title = st.get("title", idea_slug)
        except Exception:
            title = idea_slug

        prov = load_provenance(self._project_dir)
        graph = scan_workspace(workspace)
        graph_block = graph.format_block()

        # Workspace file summary for planner
        file_lines: list[str] = []
        if workspace.exists():
            for p in sorted(workspace.rglob("*.py"))[:25]:
                if p.is_file():
                    rel = p.relative_to(workspace)
                    try:
                        preview = p.read_text(encoding="utf-8", errors="replace")[:400]
                    except OSError:
                        preview = ""
                    file_lines.append(f"### {rel}\n```\n{preview}\n```")
        files_block = "\n\n".join(file_lines) or "(no .py files)"

        tag_lines = []
        if prov.get("goal_id"):
            tag_lines.append(f"- goal_id: {prov['goal_id']}")
        if prov.get("system_id"):
            tag_lines.append(f"- system_id: {prov['system_id']}")
        for m in prov.get("mission_tags") or []:
            tag_lines.append(f"- mission: {m}")
        for v in prov.get("value_tags") or []:
            tag_lines.append(f"- value ({v.get('kind', 'soft')}): {v.get('rule', '')}")
        tags_block = "\n".join(tag_lines) or "(none)"

        task_prompt = (
            f"You are planning FIELD TESTS for a completed software project.\n\n"
            f"## Project\nTitle: {title}\nSlug: {idea_slug}\nWorkspace: {workspace}\n\n"
            f"## Tags\n{tags_block}\n\n"
            f"## Master plan\n{master_plan[:2500]}\n\n"
            f"## Stale-reference scan (address in integration tests)\n{graph_block}\n\n"
            f"## Workspace code (preview)\n{files_block}\n\n"
            f"## Your job\n"
            f"Write product and integration field tests to `{tests_full}`.\n"
            f"Baseline tests (entrypoint run, syntax, stale imports) are added automatically — "
            f"do NOT duplicate them.\n\n"
            f"Include:\n"
            f"1. **Harness plan** (optional): if system_id or goal_id is set, 3-5 bullets on how "
            f"future goals could use this software.\n"
            f"2. **Product tests** (4-8): realistic scenarios proving the software delivers its purpose.\n"
            f"3. **Integration tests** (2-4): cross-module, CLI end-to-end, stale-import checks.\n\n"
            f"Use EXACTLY this task format for each test:\n"
            f"```\n"
            f"- [ ] Task P1: <short title>\n"
            f"  - Kind: product\n"
            f"  - Command: `<shell command run from workspace root>`\n"
            f"  - Expect: <substring that must appear in stdout/stderr, or 'exit 0'>\n"
            f"```\n\n"
            f"Kind must be product or integration. Commands must use relative paths only.\n"
            f"Say DONE when the file is written.\n"
        )

        self._update_idea_status("field_testing")
        result = self.call_llm_direct(task_prompt)

        llm_tests = self.read_state_file(tests_path)
        if not llm_tests.strip():
            llm_tests = self._extract_tests_markdown(result.answer)
            if llm_tests:
                self.write_state_file(tests_path, llm_tests)

        # Prepend baseline section (documented; runner merges programmatically)
        baseline_doc = "# Field Tests\n\n## Baseline (automatic)\n"
        for t in baseline_tasks(workspace):
            baseline_doc += f"- {t.task_id}: {t.title}\n"
        if llm_tests and not llm_tests.startswith("# Field Tests"):
            self.write_state_file(tests_path, baseline_doc + "\n## LLM tests\n\n" + llm_tests)
        elif not self.read_state_file(tests_path).strip():
            self.write_state_file(tests_path, baseline_doc + "\n(no LLM tests generated)\n")

        run = run_all_field_tests(
            workspace,
            self._project_dir / tests_path,
            include_baseline=True,
        )
        results_md = format_results_markdown(run)
        self.write_state_file(results_path, results_md)

        outgoing: list[Message] = []
        if run.all_passed:
            self._update_idea_status("field_proven")
            set_maturity(self._project_dir, "M2")
        else:
            loops = int(prov.get("field_test_loops", 0)) + 1
            from pipeline.ship_provenance import save_provenance

            save_provenance(
                self._project_dir,
                {**prov, "field_test_loops": loops},
            )
            max_loops = int(__import__("os").environ.get("MAX_FIELD_TEST_LOOPS", "3"))
            if loops >= max_loops:
                self._update_idea_status("ship_insufficient")
                return AgentOutput(
                    success=False,
                    answer=result.answer,
                    outgoing=[],
                    tokens_used=result.tokens_used,
                    steps_used=result.steps_used,
                )
            self._update_idea_status("field_test_failed")
            outgoing.append(
                Message.create(
                    from_agent=self.role,
                    to_agent="executor",
                    type="task",
                    payload={
                        "phase": msg.payload.get("phase", 1),
                        "idea_slug": idea_slug,
                        "ship_fix": True,
                        "field_test_results_path": results_path,
                        "tasks_path": f"phases/phase_{msg.payload.get('phase', 1)}/tasks.md",
                        "workspace_path": str(workspace),
                        "fix_required": True,
                        "error_summary": (
                            f"Field tests failed ({run.failed} failed, {run.passed} passed). "
                            f"See {results_path}."
                        ),
                        "validation_report": results_md[:4000],
                    },
                    priority=1,
                )
            )

        return AgentOutput(
            success=run.all_passed,
            answer=result.answer,
            outgoing=outgoing,
            tokens_used=result.tokens_used,
            steps_used=result.steps_used,
        )

    def _extract_tests_markdown(self, text: str) -> str:
        if not text:
            return ""
        fenced = re.search(r"```(?:markdown)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1).strip()
        if "- [ ]" in text:
            idx = text.find("- [ ]")
            return text[idx:].strip()
        return ""


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
        format="%(asctime)s [field_test_planner] %(message)s",
    )
    agent = FieldTestPlannerAgent(provider=args.provider, model=args.model)
    agent.run_loop()


if __name__ == "__main__":
    main()
