"""
pipeline/corpus_gate.py
Deterministic closeout gate before finetune corpus collection.

Inspired by OpenClaw autoreview (code closeout) but runs on project artifacts —
validation/review reports, workspace syntax, and optional quality_scorer — not git diffs.

Environment:
    CORPUS_GATE_POLICY     off | warn | enforce  (default: warn)
    CORPUS_GATE_MIN_SCORE  0-100 quality_scorer minimum (default: 50, enforce only)
    CORPUS_GATE_RUN_TESTS  1 to run pytest in quality_scorer (default: 0)

Usage:
    python -m pipeline.corpus_gate --audit
    python -m pipeline.corpus_gate --audit my_project_slug
"""

from __future__ import annotations

import ast
import json
import logging
import os
import pathlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

logger = logging.getLogger(__name__)

GatePolicy = Literal["off", "warn", "enforce"]

_VERDICT_PASS = re.compile(
    r"(?:^|\n)\s*(?:##\s*)?Verdict\s*:?\s*PASS\b",
    re.IGNORECASE | re.MULTILINE,
)
_VERDICT_FAIL = re.compile(
    r"(?:^|\n)\s*(?:##\s*)?Verdict\s*:?\s*FAIL\b",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class GateCheck:
    name: str
    passed: bool
    severity: Literal["blocker", "warning", "info"]
    message: str


@dataclass
class CollectGateResult:
    passed: bool
    policy: GatePolicy
    allow_collect: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[GateCheck] = field(default_factory=list)
    quality_total: float | None = None
    quality_grade: str | None = None
    recommend_polish: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "policy": self.policy,
            "allow_collect": self.allow_collect,
            "blockers": self.blockers,
            "warnings": self.warnings,
            "quality_total": self.quality_total,
            "quality_grade": self.quality_grade,
            "recommend_polish": self.recommend_polish,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "severity": c.severity,
                    "message": c.message,
                }
                for c in self.checks
            ],
            "audited_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


def gate_policy() -> GatePolicy:
    raw = os.environ.get("CORPUS_GATE_POLICY", "warn").strip().lower()
    if raw in ("off", "warn", "enforce"):
        return raw  # type: ignore[return-value]
    return "warn"


def _min_quality_score() -> float:
    try:
        return float(os.environ.get("CORPUS_GATE_MIN_SCORE", "50"))
    except ValueError:
        return 50.0


def _read_text(path: pathlib.Path, limit: int = 0) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        if limit and len(text) > limit:
            return text[:limit]
        return text
    except OSError:
        return ""


def _verdict_from_report(text: str) -> str:
    if not text.strip():
        return "UNKNOWN"
    if _VERDICT_FAIL.search(text):
        return "FAIL"
    if _VERDICT_PASS.search(text):
        return "PASS"
    if "Verdict: PASS" in text or "## Verdict\nPASS" in text:
        return "PASS"
    return "UNKNOWN"


def _check_workspace_code(project_dir: pathlib.Path) -> list[GateCheck]:
    workspace = project_dir / "workspace"
    checks: list[GateCheck] = []
    if not workspace.exists():
        checks.append(GateCheck(
            "workspace_exists",
            False,
            "blocker",
            "workspace/ directory missing",
        ))
        return checks

    py_files = [
        p for p in workspace.rglob("*.py")
        if p.is_file() and "__pycache__" not in p.parts
    ]
    if not py_files:
        checks.append(GateCheck(
            "workspace_has_python",
            False,
            "blocker",
            "no .py files under workspace/",
        ))
        return checks

    checks.append(GateCheck(
        "workspace_has_python",
        True,
        "info",
        f"{len(py_files)} python file(s) in workspace",
    ))

    syntax_errors: list[str] = []
    for fp in py_files[:200]:
        try:
            ast.parse(fp.read_text(encoding="utf-8", errors="replace"), filename=str(fp))
        except SyntaxError as exc:
            rel = fp.relative_to(workspace).as_posix()
            syntax_errors.append(f"{rel}:{exc.lineno}: {exc.msg}")

    if syntax_errors:
        preview = "; ".join(syntax_errors[:3])
        extra = f" (+{len(syntax_errors) - 3} more)" if len(syntax_errors) > 3 else ""
        checks.append(GateCheck(
            "python_syntax",
            False,
            "blocker",
            f"syntax errors: {preview}{extra}",
        ))
    else:
        checks.append(GateCheck(
            "python_syntax",
            True,
            "info",
            "all workspace .py files parse",
        ))
    return checks


def _check_phase_artifacts(project_dir: pathlib.Path, total_phases: int) -> list[GateCheck]:
    checks: list[GateCheck] = []
    for phase_num in range(1, max(total_phases, 1) + 1):
        tasks = project_dir / "phases" / f"phase_{phase_num}" / "tasks.md"
        val_report = project_dir / "phases" / f"phase_{phase_num}" / "validation_report.md"
        review = project_dir / "phases" / f"phase_{phase_num}" / "review.md"

        if not tasks.exists() or not _read_text(tasks, 50).strip():
            checks.append(GateCheck(
                f"phase_{phase_num}_tasks",
                False,
                "blocker",
                f"phases/phase_{phase_num}/tasks.md missing or empty",
            ))
        else:
            checks.append(GateCheck(
                f"phase_{phase_num}_tasks",
                True,
                "info",
                "tasks.md present",
            ))

        val_text = _read_text(val_report)
        val_v = _verdict_from_report(val_text)
        if val_v == "FAIL":
            checks.append(GateCheck(
                f"phase_{phase_num}_validation",
                False,
                "blocker",
                "validation_report.md verdict FAIL",
            ))
        elif val_v == "UNKNOWN" and val_text.strip():
            checks.append(GateCheck(
                f"phase_{phase_num}_validation",
                True,
                "warning",
                "validation verdict unclear (no PASS/FAIL marker)",
            ))
        elif val_v == "UNKNOWN":
            checks.append(GateCheck(
                f"phase_{phase_num}_validation",
                True,
                "warning",
                "validation_report.md missing or empty",
            ))
        else:
            checks.append(GateCheck(
                f"phase_{phase_num}_validation",
                True,
                "info",
                "validation PASS",
            ))

        review_text = _read_text(review)
        review_v = _verdict_from_report(review_text)
        if review_v == "FAIL":
            checks.append(GateCheck(
                f"phase_{phase_num}_review",
                False,
                "blocker",
                "review.md verdict FAIL",
            ))
        elif review_v == "UNKNOWN" and review_text.strip():
            checks.append(GateCheck(
                f"phase_{phase_num}_review",
                True,
                "warning",
                "review verdict unclear",
            ))
        elif review_v == "UNKNOWN":
            checks.append(GateCheck(
                f"phase_{phase_num}_review",
                True,
                "warning",
                "review.md missing or empty",
            ))
        else:
            checks.append(GateCheck(
                f"phase_{phase_num}_review",
                True,
                "info",
                "review PASS",
            ))

    return checks


def _check_quality_score(slug: str, *, policy: GatePolicy) -> list[GateCheck]:
    checks: list[GateCheck] = []
    run_tests = os.environ.get("CORPUS_GATE_RUN_TESTS", "").strip() in ("1", "true", "yes")
    try:
        from quality_scorer import score_project

        ps = score_project(slug, run_tests=run_tests)
    except Exception as exc:
        checks.append(GateCheck(
            "quality_scorer",
            True,
            "warning",
            f"quality_scorer skipped: {exc}",
        ))
        return checks

    if ps is None:
        checks.append(GateCheck(
            "quality_scorer",
            True,
            "warning",
            "quality_scorer could not load project",
        ))
        return checks

    total = ps.total
    grade = ps.grade()
    min_score = _min_quality_score()
    if total < min_score:
        checks.append(GateCheck(
            "quality_scorer",
            False,
            "blocker" if policy == "enforce" else "warning",
            f"quality score {total:.0f}/100 (grade {grade}) below minimum {min_score:.0f}",
        ))
    else:
        checks.append(GateCheck(
            "quality_scorer",
            True,
            "info",
            f"quality score {total:.0f}/100 (grade {grade})",
        ))
    return checks


def run_collect_gate(
    project_dir: pathlib.Path,
    state: dict[str, Any],
    *,
    policy: GatePolicy | None = None,
) -> CollectGateResult:
    """
    Run closeout checks before writing finetune corpus rows.
    """
    policy = policy or gate_policy()
    slug = state.get("_slug") or project_dir.name
    total_phases = int(state.get("total_phases", 1))
    status = state.get("status", "")

    if policy == "off":
        return CollectGateResult(
            passed=True,
            policy=policy,
            allow_collect=True,
        )

    checks: list[GateCheck] = []
    checks.extend(_check_workspace_code(project_dir))
    checks.extend(_check_phase_artifacts(project_dir, total_phases))
    checks.extend(_check_quality_score(slug, policy=policy))

    if status == "budget_exceeded":
        checks.append(GateCheck(
            "terminal_status",
            True,
            "warning",
            "project ended with budget_exceeded — corpus may be incomplete",
        ))

    blockers = [c.message for c in checks if not c.passed and c.severity == "blocker"]
    warnings = [c.message for c in checks if c.severity == "warning" or (not c.passed and c.severity != "blocker")]

    passed = len(blockers) == 0
    if policy == "enforce":
        allow_collect = passed
    else:
        allow_collect = True

    quality_total: float | None = None
    quality_grade: str | None = None
    for c in checks:
        if c.name == "quality_scorer" and "quality score" in c.message:
            m = re.search(r"quality score ([\d.]+)/100 \(grade ([A-F])\)", c.message)
            if m:
                quality_total = float(m.group(1))
                quality_grade = m.group(2)

    recommend_polish = bool(blockers) or any(
        c.severity == "warning" and "validation" in c.name for c in checks
    )

    return CollectGateResult(
        passed=passed,
        policy=policy,
        allow_collect=allow_collect,
        blockers=blockers,
        warnings=warnings,
        checks=checks,
        quality_total=quality_total,
        quality_grade=quality_grade,
        recommend_polish=recommend_polish,
    )


def persist_gate_result(project_dir: pathlib.Path, result: CollectGateResult) -> None:
    path = project_dir / "state" / "corpus_gate.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    except OSError as exc:
        logger.debug("corpus_gate: could not write %s: %s", path, exc)


def print_gate_result(slug: str, result: CollectGateResult) -> None:
    if result.policy == "off":
        return
    if result.allow_collect and not result.warnings and result.passed:
        print(f"  [corpus-gate] {slug}: closeout OK")
        return
    if not result.allow_collect:
        print(f"  [corpus-gate] {slug}: BLOCKED corpus collect ({result.policy})")
        for msg in result.blockers[:5]:
            print(f"    - {msg}")
        if len(result.blockers) > 5:
            print(f"    - ... +{len(result.blockers) - 5} more")
        print("  [corpus-gate] Fix issues, run --polish / --resume, then re-complete or use CORPUS_GATE_POLICY=warn")
        return
    print(f"  [corpus-gate] {slug}: collect allowed with warnings")
    for msg in result.warnings[:5]:
        print(f"    - {msg}")


def audit_closeout_on_complete(project_dir: pathlib.Path, state: dict[str, Any]) -> CollectGateResult:
    """
    Advisory closeout at project completion (does not block runner).
    Persists corpus_gate.json and tags state when polish is recommended.
    """
    result = run_collect_gate(project_dir, state, policy=gate_policy())
    persist_gate_result(project_dir, result)
    slug = state.get("_slug") or project_dir.name
    print_gate_result(slug, result)

    if result.recommend_polish and not result.passed:
        state["corpus_closeout_recommend_polish"] = True
        state_path = project_dir / "state" / "current_idea.json"
        try:
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except OSError:
            pass
    return result


def should_skip_collect(
    project_dir: pathlib.Path,
    state: dict[str, Any],
    *,
    skip_gate: bool = False,
) -> tuple[bool, CollectGateResult | None]:
    if skip_gate or gate_policy() == "off":
        return False, None
    result = run_collect_gate(project_dir, state)
    persist_gate_result(project_dir, result)
    slug = state.get("_slug") or project_dir.name
    print_gate_result(slug, result)
    return not result.allow_collect, result


def audit_all_projects(*, only_complete: bool = True) -> list[tuple[str, CollectGateResult]]:
    from pipeline.paths import projects_dir

    rows: list[tuple[str, CollectGateResult]] = []
    if not projects_dir().exists():
        return rows

    for proj in sorted(projects_dir().iterdir()):
        if not proj.is_dir():
            continue
        state_path = proj / "state" / "current_idea.json"
        if not state_path.exists():
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if only_complete and state.get("status") not in ("complete", "budget_exceeded"):
            continue
        result = run_collect_gate(proj, state)
        rows.append((proj.name, result))
    return rows


def _cli() -> None:
    import argparse
    import sys

    from pipeline.paths import projects_dir

    parser = argparse.ArgumentParser(description="Corpus collection closeout gate (autoreview-style)")
    parser.add_argument("--audit", nargs="?", const="__all__", metavar="SLUG")
    parser.add_argument("--policy", choices=["off", "warn", "enforce"], default=None)
    parser.add_argument("--all-statuses", action="store_true")
    args = parser.parse_args()

    if args.policy:
        os.environ["CORPUS_GATE_POLICY"] = args.policy

    if args.audit is None:
        parser.print_help()
        sys.exit(0)

    if args.audit == "__all__":
        rows = audit_all_projects(only_complete=not args.all_statuses)
        blocked = sum(1 for _, r in rows if not r.allow_collect)
        warned = sum(1 for _, r in rows if r.warnings)
        print(f"\n{'='*50}")
        print(f"  Corpus gate audit ({len(rows)} projects)")
        print(f"{'='*50}")
        print(f"  Would block collect: {blocked}")
        print(f"  With warnings:       {warned}")
        for slug, result in rows:
            if result.allow_collect and not result.warnings:
                continue
            flag = "BLOCK" if not result.allow_collect else "WARN"
            first = (result.blockers or result.warnings or ["?"])[0]
            print(f"  [{flag}] {slug}: {first[:70]}")
        print("=" * 50)
        return

    proj = projects_dir() / args.audit
    state_path = proj / "state" / "current_idea.json"
    if not state_path.exists():
        print(f"Project not found: {proj}")
        sys.exit(1)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    result = run_collect_gate(proj, state)
    persist_gate_result(proj, result)
    print(json.dumps(result.to_dict(), indent=2))
    sys.exit(0 if result.allow_collect else 1)


if __name__ == "__main__":
    _cli()
