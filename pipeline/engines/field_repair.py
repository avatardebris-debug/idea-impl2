"""
Field fail repair bridge — not full grok_build.

After thin field ship FAIL:
  1. field_fail_repair   (field-test skill style: replan + minimal product fix)
  2. field_systematic_debug
  3. field_code_review   (focused; optional tiny fix)
  4. field_comprehensive_report (advisory only)

Each step re-runs field_test_runner. Stops on PASS or max steps.

Env:
  FIELD_SHIP_REPAIR=1          enable (default on for thin ship if LLM/CLI available)
  FIELD_SHIP_REPAIR_MAX=3      max repair invocations (default 3 = steps 1–3; 4 includes comprehensive)
  FIELD_SHIP_REPAIR_BACKEND=auto|cli|pipeline_llm
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool
from pipeline.engines.base import EngineResult

REPAIR_CHAIN: list[str] = [
    "field_fail_repair",
    "field_systematic_debug",
    "field_code_review",
    "field_comprehensive_report",
]


@dataclass
class RepairOutcome:
    passed: bool = False
    steps_run: list[str] = field(default_factory=list)
    classification: str = ""
    final_passed: int = 0
    final_failed: int = 0
    reports: dict[str, str] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "steps_run": self.steps_run,
            "classification": self.classification,
            "final_passed": self.final_passed,
            "final_failed": self.final_failed,
            "reports": self.reports,
            "reason": self.reason,
        }


def repair_enabled() -> bool:
    return env_bool("FIELD_SHIP_REPAIR", default=True)


def repair_max_steps() -> int:
    raw = os.environ.get("FIELD_SHIP_REPAIR_MAX", "3").strip()
    try:
        return max(0, min(4, int(raw)))
    except ValueError:
        return 3


def classify_field_failure(results_md: str) -> str:
    """Heuristic classification from field_test_results.md text."""
    text = results_md or ""
    low = text.lower()
    fails = re.findall(r"##\s+([^\n]+FAIL[^\n]*)", text, re.I)
    n_fail = len(fails) or text.lower().count("— fail") or text.lower().count("- fail")

    pytest_fail = "pytest" in low and ("fail" in low or "failed" in low)
    help_fail = any(
        x in low for x in ("--help", "entrypoint", "cli.py", "main.py", "usage")
    ) and "fail" in low
    import_fail = "import" in low and ("error" in low or "fail" in low)
    no_module = "no module named" in low or "modulenotfound" in low
    command_missing = "no command" in low or "not found" in low

    if no_module or command_missing:
        return "bad_plan"
    if pytest_fail and n_fail <= 2 and not help_fail:
        return "product_bug"
    if pytest_fail and n_fail >= 3:
        return "product_bug"  # then debug → review
    if help_fail or import_fail:
        return "product_bug"
    if n_fail == 0:
        return "unknown"
    return "mixed"


def _ship_paths(project_dir: Path) -> dict[str, Path]:
    ship = project_dir / "phases" / "ship"
    ship.mkdir(parents=True, exist_ok=True)
    return {
        "field_tests": ship / "field_tests.md",
        "field_results": ship / "field_test_results.md",
        "fix_report": ship / "field_fix_report.md",
        "debug_report": ship / "field_debug_report.md",
        "review": ship / "field_code_review.md",
        "comprehensive": ship / "field_comprehensive_report.md",
        "repair_log": ship / "field_repair_log.md",
        "evaluation": ship / "field_evaluation.md",
    }


def write_field_evaluation_report(
    project_dir: Path,
    *,
    slug: str,
    classification: str,
    steps_run: list[str],
    final_passed: int,
    final_failed: int,
    results_md: str = "",
    invoke_errors: list[str] | None = None,
) -> Path:
    """After repair chain exhausts without PASS — evaluation + recommended next steps.

    Always written (deterministic). Not a 4th fix attempt; closes the loop.
    """
    from datetime import datetime, timezone

    project_dir = Path(project_dir)
    paths = _ship_paths(project_dir)
    path = paths["evaluation"]

    fail_heads = re.findall(r"##\s+([^\n]+FAIL[^\n]*)", results_md or "", re.I)
    fail_list = "\n".join(f"- {h.strip()}" for h in fail_heads[:15]) or "- (see field_test_results.md)"

    errs = invoke_errors or []
    err_block = "\n".join(f"- {e}" for e in errs[:12]) or "- (none recorded)"

    # Recommend next based on classification + errors
    next_steps: list[str] = []
    if any("not found" in e.lower() or "404" in e for e in errs):
        next_steps.append(
            "Repair LLM/CLI was unavailable — re-run with GROK_BUILD_CMD or a pulled Ollama model "
            "(`FIELD_SHIP_REPAIR_BACKEND=cli` or set PIPELINE_MODEL to an installed tag)."
        )
    if classification == "bad_plan":
        next_steps.append(
            "Replan field tests against real modules (`FIELD_PLAN_ENGINE=pipeline_llm|grok` "
            "or interactive `/field-test`), then re-run with `FIELD_PLAN_ENGINE=none`."
        )
    if classification in ("product_bug", "mixed"):
        next_steps.append(
            "Human or targeted fix: address failing Commands in workspace; re-run thin field ship."
        )
        next_steps.append(
            "If pytest is deeply red: open a polish/fix phase or optional full grok_build re-implement "
            "for this slug only (expensive)."
        )
    if not next_steps:
        next_steps.append("Inspect field_test_results.md and field_repair_log.md; fix or accept ship_insufficient.")

    next_steps.append("Do **not** mark field_proven until field suite is green.")
    next_steps.append("Optional: accept ship_insufficient and move on; harvest other field_proven for RSI.")

    body = f"""# Field evaluation (repair exhausted)

- Project: `{slug}`
- Generated: {datetime.now(timezone.utc).isoformat()}
- Status recommendation: **ship_insufficient** (unless you fix and re-run)
- Classification: `{classification}`
- Repair steps run: {", ".join(steps_run) or "(none)"} (max retries, not infinite)
- Last field score: passed={final_passed} failed={final_failed}

## Failed tasks (from results)
{fail_list}

## Repair invoke errors (if any)
{err_block}

## What was tried
The thin-ship **repair bridge** (not full grok_build) attempted up to
`FIELD_SHIP_REPAIR_MAX` steps: field-test style repair → systematic debug →
focused code review. Field was re-run after each fix step. After those retries
without a green suite, this evaluation is written instead of looping further.

## Recommended next steps
{chr(10).join(f"{i}. {s}" for i, s in enumerate(next_steps, 1))}

## Artifacts to read
- `phases/ship/field_test_results.md`
- `phases/ship/field_repair_log.md`
- `phases/ship/field_fix_report.md` (if written)
- `phases/ship/field_debug_report.md` (if written)
- `phases/ship/field_code_review.md` (if written)
- `state/capability_claims.md` / usefulness_report.md

## Operator one-liner re-run (after fix)
```text
FIELD_SHIP_REPAIR=1 FIELD_PLAN_ENGINE=none python scripts/bulk_thin_field_ship.py --slug {slug[:40]} --include-classic --retry-insufficient --prefer-existing-plan --repair --limit 1
```
"""
    path.write_text(body, encoding="utf-8")
    return path


def _invoke_repair_step(
    step: str,
    *,
    project_dir: Path,
    workspace: Path,
    slug: str,
    phase: int,
) -> EngineResult:
    """Run one repair skill via same backends as grok_build (CLI or pipeline_llm)."""
    from pipeline.engines.grok_build import run_phase_step

    # Prefer pipeline_llm if no CLI, same as auto backend
    backend = (os.environ.get("FIELD_SHIP_REPAIR_BACKEND") or "auto").strip().lower()
    old_backend = os.environ.get("GROK_BUILD_BACKEND")
    try:
        if backend in ("cli", "pipeline_llm"):
            os.environ["GROK_BUILD_BACKEND"] = backend
        # else leave auto
        return run_phase_step(
            slug,
            phase,
            step,
            project_dir=project_dir,
            workspace=workspace,
        )
    finally:
        if old_backend is None:
            os.environ.pop("GROK_BUILD_BACKEND", None)
        else:
            os.environ["GROK_BUILD_BACKEND"] = old_backend


def _rerun_field(
    project_dir: Path, workspace: Path
) -> tuple[Any, str]:
    from pipeline.field_test_runner import format_results_markdown, run_all_field_tests

    paths = _ship_paths(project_dir)
    field_path = paths["field_tests"]
    run = run_all_field_tests(workspace, field_path, include_baseline=True)
    md = format_results_markdown(run)
    paths["field_results"].write_text(md, encoding="utf-8")
    return run, md


def run_field_repair_chain(
    project_dir: Path,
    workspace: Path,
    *,
    slug: str = "",
    phase: int = 1,
    initial_results_md: str = "",
) -> RepairOutcome:
    """
    Bridge after first field FAIL. Does not run full grok_build implement chain.
    """
    project_dir = Path(project_dir)
    workspace = Path(workspace)
    slug = slug or project_dir.name
    out = RepairOutcome()
    paths = _ship_paths(project_dir)

    if not repair_enabled():
        out.reason = "FIELD_SHIP_REPAIR disabled"
        return out

    max_steps = repair_max_steps()
    if max_steps <= 0:
        out.reason = "FIELD_SHIP_REPAIR_MAX=0"
        return out

    results_md = initial_results_md
    if not results_md and paths["field_results"].is_file():
        results_md = paths["field_results"].read_text(encoding="utf-8", errors="replace")

    out.classification = classify_field_failure(results_md)
    # Only the first 3 chain entries are fix attempts; comprehensive is optional 4th
    fix_steps = [s for s in REPAIR_CHAIN if s != "field_comprehensive_report"][:max_steps]
    log_lines = [
        f"# Field repair log",
        f"- slug: {slug}",
        f"- initial classification: {out.classification}",
        f"- max_steps: {max_steps} (no infinite loop)",
        "",
    ]
    invoke_errors: list[str] = []

    for step in fix_steps:
        out.steps_run.append(step)
        log_lines.append(f"## Step `{step}`")
        inv = _invoke_repair_step(
            step,
            project_dir=project_dir,
            workspace=workspace,
            slug=slug,
            phase=phase,
        )
        log_lines.append(
            f"- invoke success={inv.success} exit={inv.exit_code} err={inv.error}"
        )
        log_lines.append(f"- summary: {(inv.summary or '')[:300]}")
        if inv.error:
            invoke_errors.append(f"{step}: {inv.error}")

        for key, p in (
            ("fix_report", paths["fix_report"]),
            ("debug_report", paths["debug_report"]),
            ("review", paths["review"]),
        ):
            if p.is_file():
                out.reports[key] = str(p)

        run, results_md = _rerun_field(project_dir, workspace)
        out.final_passed = run.passed
        out.final_failed = run.failed
        log_lines.append(
            f"- re-field pass={run.passed} fail={run.failed} all={run.all_passed}"
        )

        if run.all_passed:
            out.passed = True
            out.reason = f"field PASS after {step}"
            log_lines.append(f"- STOP: {out.reason}")
            break

        out.classification = classify_field_failure(results_md)

    # After max fix retries without PASS → evaluation write-up (always)
    if not out.passed:
        out.reason = (
            f"repair exhausted after {len(out.steps_run)} step(s); "
            f"pass={out.final_passed} fail={out.final_failed}"
        )
        log_lines.append("## Evaluation (repair exhausted)")
        try:
            ev = write_field_evaluation_report(
                project_dir,
                slug=slug,
                classification=out.classification,
                steps_run=out.steps_run,
                final_passed=out.final_passed,
                final_failed=out.final_failed,
                results_md=results_md,
                invoke_errors=invoke_errors,
            )
            out.reports["evaluation"] = str(ev)
            log_lines.append(f"- wrote {ev}")
        except Exception as exc:
            log_lines.append(f"- evaluation write failed: {exc}")

        # Optional LLM comprehensive if MAX>=4 and backend available
        if max_steps >= 4:
            log_lines.append("## Optional comprehensive LLM report")
            inv = _invoke_repair_step(
                "field_comprehensive_report",
                project_dir=project_dir,
                workspace=workspace,
                slug=slug,
                phase=phase,
            )
            out.steps_run.append("field_comprehensive_report")
            log_lines.append(
                f"- invoke success={inv.success} err={inv.error}"
            )
            if paths["comprehensive"].is_file():
                out.reports["comprehensive"] = str(paths["comprehensive"])

    try:
        paths["repair_log"].write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        out.reports["repair_log"] = str(paths["repair_log"])
    except OSError:
        pass

    return out
