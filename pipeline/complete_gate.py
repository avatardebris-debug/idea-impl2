"""
Final gates when marking a project complete.

Re-runs pytest on workspace at complete time. If red (or force_advanced /
quality_risk), status becomes complete_with_bugs so operators can see it.

Env:
  PIPELINE_COMPLETE_PYTEST=1   (default on) run pytest at complete
  PIPELINE_COMPLETE_PYTEST_TIMEOUT=600
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool

STATUS_COMPLETE = "complete"
STATUS_COMPLETE_WITH_BUGS = "complete_with_bugs"


def complete_pytest_enabled() -> bool:
    return env_bool("PIPELINE_COMPLETE_PYTEST", default=True)


def assess_complete_quality(
    project_dir: Path,
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Run final pytest (optional) and decide clean vs complete_with_bugs.

    Returns dict:
      status: complete | complete_with_bugs
      reasons: list[str]
      pytest: dict | None
    """
    project_dir = Path(project_dir)
    workspace = project_dir / "workspace"
    reasons: list[str] = []
    pytest_info: dict[str, Any] | None = None

    # Historical force-advance / quality risk
    if state.get("force_advanced") or state.get("quality_risk"):
        reasons.append("force_advanced or quality_risk set on state")
    rr = state.get("review_result") or {}
    if isinstance(rr, dict) and rr.get("force_advanced"):
        reasons.append("review_result.force_advanced")

    if complete_pytest_enabled() and workspace.is_dir():
        try:
            from pipeline.agents.validator import run_pytest

            timeout = 120
            raw_t = os.environ.get("PIPELINE_COMPLETE_PYTEST_TIMEOUT", "").strip()
            if raw_t:
                try:
                    timeout = max(30, int(raw_t))
                except ValueError:
                    pass
            # run_pytest uses timeout_per_test; overall is internal 600s
            pr = run_pytest(workspace, timeout_per_test=min(120, timeout))
            pytest_info = {
                "returncode": pr.get("returncode"),
                "passed": pr.get("passed"),
                "failed": pr.get("failed"),
                "errors": pr.get("errors"),
                "no_tests": pr.get("no_tests"),
            }
            # Persist report
            report_path = project_dir / "state" / "complete_validation.md"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                _format_complete_validation(pr, reasons_pre=reasons),
                encoding="utf-8",
            )

            no_tests = bool(pr.get("no_tests"))
            rc = int(pr.get("returncode") or 0)
            failed = int(pr.get("failed") or 0)
            errors = int(pr.get("errors") or 0)
            # exit 5 = no tests — soft ok unless REQUIRE_TESTS and has code
            if no_tests or rc == 5:
                has_py = any(workspace.rglob("*.py"))
                if env_bool("PIPELINE_REQUIRE_TESTS", default=False) and has_py:
                    reasons.append("no tests collected but code present (PIPELINE_REQUIRE_TESTS)")
            elif rc != 0 or failed > 0 or errors > 0:
                reasons.append(
                    f"pytest not green at complete: "
                    f"passed={pr.get('passed')} failed={failed} errors={errors} rc={rc}"
                )
        except Exception as exc:
            reasons.append(f"complete pytest error: {exc}")
            pytest_info = {"error": str(exc)}

    if reasons:
        return {
            "status": STATUS_COMPLETE_WITH_BUGS,
            "reasons": reasons,
            "pytest": pytest_info,
        }
    return {
        "status": STATUS_COMPLETE,
        "reasons": [],
        "pytest": pytest_info,
    }


def _format_complete_validation(pr: dict[str, Any], *, reasons_pre: list[str]) -> str:
    tail = (pr.get("stdout") or "")[-6000:]
    return (
        f"# Complete validation\n\n"
        f"- Generated: {datetime.now(timezone.utc).isoformat()}\n"
        f"- Tests: passed={pr.get('passed')} failed={pr.get('failed')} "
        f"errors={pr.get('errors')} rc={pr.get('returncode')} "
        f"no_tests={pr.get('no_tests')}\n"
        f"- Prior risk flags: {reasons_pre or 'none'}\n\n"
        f"## Output (tail)\n```\n{tail}\n```\n"
    )
