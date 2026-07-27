"""
Field-prove dual gate: author ≠ runner ≠ evaluator.

Statuses:
  field_test_passed  — mechanical: runner all_passed (commands green)
  field_proven       — runner all_passed AND min product/integration bars
                       AND adequacy ADEQUATE (deterministic and/or LLM)

Runner is the sole execution oracle. Evaluator must not invent command passes.
Baseline B* never counts toward product/integration bars.

Env:
  FIELD_SHIP_DUAL_GATE=1          (default on) dual-gate honesty on thin ship
  FIELD_MIN_PRODUCT=1             min non-trivial product (P*) tasks
  FIELD_MIN_INTEGRATION=1         min non-trivial integration (I*) tasks
  FIELD_SHIP_EVALUATOR_LLM=0      (default off) optional LLM adequacy on thin ship
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool, env_int
from pipeline.field_test_runner import FieldTestTask, parse_field_tests_md

# Documented defaults (override via env)
DEFAULT_MIN_PRODUCT = 1
DEFAULT_MIN_INTEGRATION = 1

# Closed adequacy / evaluator verdicts
VERDICT_ADEQUATE = "ADEQUATE"
VERDICT_NEEDS_MORE = "NEEDS_MORE_FIELD_TESTS"
VERDICT_INSUFFICIENT = "SHIP_INSUFFICIENT"
# Legacy alias still accepted from ship_evaluator markdown
VERDICT_FIELD_PROVEN = "FIELD_PROVEN"

CLOSED_ADEQUACY_VERDICTS = frozenset(
    {
        VERDICT_ADEQUATE,
        VERDICT_NEEDS_MORE,
        VERDICT_INSUFFICIENT,
        VERDICT_FIELD_PROVEN,
    }
)

# Commands that never prove product aim alone (smoke / harness)
_TRIVIAL_CMD_RES = (
    re.compile(r"--help\b", re.I),
    re.compile(r"-m\s+py_compile\b", re.I),
    re.compile(r"\bpy_compile\b", re.I),
    re.compile(r"""print\s*\(\s*['\"]IMPORT_OK['\"]\s*\)""", re.I),
    re.compile(r"""print\s*\(\s*['\"]ok['\"]\s*\)""", re.I),
    re.compile(r"^\s*(echo|true|rem)\b", re.I),
    # shell no-ops / empty product
    re.compile(r"^\s*(exit\s+0|:)\s*$", re.I),
    re.compile(r"^\s*cmd\s*/c\s+(echo|exit)\b", re.I),
)

# python -c "print('…')" only — no product import/module reference
_PRINT_ONLY_C = re.compile(
    r"""-c\s+["']\s*print\s*\([^)]*\)\s*["']\s*$""",
    re.I,
)
# python -c without importing/referencing a real module path (print-only body)
_C_FLAG_BODY = re.compile(r"""-c\s+["']([^"']+)["']""", re.I)
_PRODUCT_SIGNAL = re.compile(
    r"\b(import|from)\s+\w|\b(open|Path|json|argparse|sys\.argv|__main__|"
    r"write_text|read_text|main\(|cli\.|app\.)",
    re.I,
)

_TRIVIAL_TITLE_RES = (
    re.compile(r"\bhelp\b", re.I),
    re.compile(r"\bsyntax[- ]?check\b", re.I),
    re.compile(r"\bimport\b.*\bmodule", re.I),
    re.compile(r"^import\b", re.I),
)

_WEAK_EXPECT_RES = (
    re.compile(r"^exit\s+0\s*$", re.I),
    re.compile(r"^IMPORT_OK$", re.I),
    re.compile(r"^ok$", re.I),
)

# Closed Adequacy/Verdict line patterns (for last-wins parse)
_CLOSED_VERDICT_LINE = re.compile(
    r"(?:Adequacy|Verdict)\s*:\s*"
    r"(ADEQUATE|FIELD_PROVEN|NEEDS_MORE_FIELD_TESTS|SHIP_INSUFFICIENT)\b",
    re.IGNORECASE,
)


def dual_gate_enabled() -> bool:
    """Thin ship dual-gate (default on for honesty)."""
    return env_bool("FIELD_SHIP_DUAL_GATE", default=True)


def min_product_tasks() -> int:
    return max(0, env_int("FIELD_MIN_PRODUCT", default=DEFAULT_MIN_PRODUCT))


def min_integration_tasks() -> int:
    return max(0, env_int("FIELD_MIN_INTEGRATION", default=DEFAULT_MIN_INTEGRATION))


def is_trivial_task(task: FieldTestTask) -> bool:
    """True if task is baseline-style smoke (help/syntax/import/print-only).

    Known limit: not a full adversarial plan judge — gaming with complex
    non-product shell still possible; Phase 2 bars close pure smoke overclaim.
    """
    kind = (task.kind or "").lower()
    if kind == "baseline":
        return True
    cmd = (task.command or "").strip()
    title = (task.title or "").strip()
    if not cmd:
        return True
    for rx in _TRIVIAL_CMD_RES:
        if rx.search(cmd):
            return True
    # print-only python -c (no product import / I/O)
    if _PRINT_ONLY_C.search(cmd):
        return True
    c_body = _C_FLAG_BODY.search(cmd)
    if c_body:
        body = c_body.group(1)
        # -c body that is only print(...) or constants — no product signal
        if re.match(r"^\s*print\s*\(", body, re.I) and not _PRODUCT_SIGNAL.search(body):
            return True
        if not _PRODUCT_SIGNAL.search(body) and re.search(
            r"^\s*(print|pass)\b", body, re.I
        ):
            return True
    # Bare import with only IMPORT_OK style expect
    if re.search(r"""-c\s+["'].*\bimport\b""", cmd) and not re.search(
        r"\b(assert|write|open|Path|json|main|run|cli|argparse|sys\.argv)\b",
        cmd,
        re.I,
    ):
        expect = (task.expect_substr or "").strip() or (
            f"exit {task.expect_exit}" if task.expect_exit is not None else ""
        )
        if any(rx.match(expect) for rx in _WEAK_EXPECT_RES) or not expect:
            return True
    for rx in _TRIVIAL_TITLE_RES:
        if rx.search(title) and any(r.search(cmd) for r in _TRIVIAL_CMD_RES):
            return True
    return False


def is_nontrivial_expect(task: FieldTestTask) -> bool:
    """Expect must exist; pure exit-0 on trivial cmd is not enough alone."""
    if task.expect_exit is None and not (task.expect_substr or "").strip():
        return False
    if is_trivial_task(task):
        return False
    # Non-trivial task with any Expect (exit N or substring) counts
    if (task.expect_substr or "").strip():
        return True
    if task.expect_exit is not None:
        return True
    return False


@dataclass
class PlanBarsResult:
    product_total: int = 0
    integration_total: int = 0
    product_nontrivial: int = 0
    integration_nontrivial: int = 0
    baseline_only: bool = False
    weak_plan: bool = False
    meets_min_bars: bool = False
    min_product: int = DEFAULT_MIN_PRODUCT
    min_integration: int = DEFAULT_MIN_INTEGRATION
    reasons: list[str] = field(default_factory=list)
    product_ids: list[str] = field(default_factory=list)
    integration_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_total": self.product_total,
            "integration_total": self.integration_total,
            "product_nontrivial": self.product_nontrivial,
            "integration_nontrivial": self.integration_nontrivial,
            "baseline_only": self.baseline_only,
            "weak_plan": self.weak_plan,
            "meets_min_bars": self.meets_min_bars,
            "min_product": self.min_product,
            "min_integration": self.min_integration,
            "reasons": list(self.reasons),
            "product_ids": list(self.product_ids),
            "integration_ids": list(self.integration_ids),
        }


def assess_plan_bars(
    field_tests_md: str | Path,
    *,
    min_product: int | None = None,
    min_integration: int | None = None,
) -> PlanBarsResult:
    """
    Count product/integration tasks with non-trivial Expect.
    Baseline B* never counts. Help/syntax/import-only plans are weak.
    """
    if isinstance(field_tests_md, Path):
        content = (
            field_tests_md.read_text(encoding="utf-8", errors="replace")
            if field_tests_md.is_file()
            else ""
        )
    else:
        content = field_tests_md or ""

    tasks = parse_field_tests_md(content)
    min_p = min_product if min_product is not None else min_product_tasks()
    min_i = min_integration if min_integration is not None else min_integration_tasks()

    result = PlanBarsResult(min_product=min_p, min_integration=min_i)
    products: list[FieldTestTask] = []
    integrations: list[FieldTestTask] = []

    for t in tasks:
        kind = (t.kind or "product").lower()
        tid = (t.task_id or "").upper()
        if kind == "baseline" or tid.startswith("B"):
            continue
        if kind == "integration" or tid.startswith("I"):
            integrations.append(t)
            result.integration_total += 1
            if not is_trivial_task(t) and is_nontrivial_expect(t):
                result.integration_nontrivial += 1
                result.integration_ids.append(t.task_id)
        else:
            products.append(t)
            result.product_total += 1
            if not is_trivial_task(t) and is_nontrivial_expect(t):
                result.product_nontrivial += 1
                result.product_ids.append(t.task_id)

    if not products and not integrations:
        result.baseline_only = True
        result.weak_plan = True
        result.reasons.append("no product/integration tasks (baseline-only or empty plan)")

    if result.product_nontrivial < min_p:
        result.reasons.append(
            f"product non-trivial {result.product_nontrivial} < min {min_p}"
        )
    if result.integration_nontrivial < min_i:
        result.reasons.append(
            f"integration non-trivial {result.integration_nontrivial} < min {min_i}"
        )

    # Weak: only trivial smoke even if counts of task rows exist
    if products or integrations:
        all_trivial = all(is_trivial_task(t) for t in products + integrations)
        if all_trivial:
            result.weak_plan = True
            result.reasons.append(
                "all product/integration tasks are help/syntax/import smoke"
            )

    result.meets_min_bars = (
        result.product_nontrivial >= min_p
        and result.integration_nontrivial >= min_i
        and not result.baseline_only
        and not result.weak_plan
    )
    if result.meets_min_bars and not result.reasons:
        result.reasons.append("min product/integration bars met")
    return result


def parse_adequacy_verdict(content: str) -> str:
    """
    Parse closed verdict from ship_evaluation.md (or thin adequacy note).

    Accepts ADEQUATE | NEEDS_MORE_FIELD_TESTS | SHIP_INSUFFICIENT | FIELD_PROVEN.

    **Last-wins:** when dual-gate overrides append new Adequacy/Verdict lines after
    an earlier ADEQUATE, the **last** closed line decides (so demotions stick in
    the durable file). Among last-line candidates, SHIP_INSUFFICIENT and
    NEEDS_MORE_FIELD_TESTS outrank ADEQUATE/FIELD_PROVEN if both appear on the
    same final pair (Adequacy + Verdict).

    Default when missing/unknown: SHIP_INSUFFICIENT (safe).
    """
    text = content or ""
    matches = list(_CLOSED_VERDICT_LINE.finditer(text))
    if not matches:
        return VERDICT_INSUFFICIENT

    # Collect trailing closed lines (last Adequacy: and last Verdict: if both present
    # at end of dual-gate override blocks — take the final match overall).
    last = matches[-1].group(1).upper()
    # If the last two closed lines differ (e.g. Adequacy: NEEDS_MORE + Verdict: NEEDS_MORE
    # after earlier ADEQUATE), last alone is enough. If last is ADEQUATE/FIELD_PROVEN
    # but a later-same-block negative exists, prefer strongest among the final *pair*.
    # Strength: SHIP_INSUFFICIENT > NEEDS_MORE > ADEQUATE/FIELD_PROVEN.
    _rank = {
        VERDICT_INSUFFICIENT: 3,
        VERDICT_NEEDS_MORE: 2,
        VERDICT_ADEQUATE: 1,
        VERDICT_FIELD_PROVEN: 1,
    }
    # Prefer last match; if the final two matches are adjacent (override block),
    # take the stronger of those two so Adequacy: X / Verdict: Y is consistent.
    if len(matches) >= 2:
        a = matches[-2].group(1).upper()
        b = matches[-1].group(1).upper()
        # Only blend last pair when both are near the end of the document
        # (same dual-gate override region — within 400 chars of EOF).
        tail = text[matches[-2].start() :]
        if len(text) - matches[-2].start() <= 400:
            pick = a if _rank.get(a, 0) >= _rank.get(b, 0) else b
            return pick
    return last


def normalize_adequacy(verdict: str) -> str:
    """Map FIELD_PROVEN → ADEQUATE; unknown → SHIP_INSUFFICIENT."""
    v = (verdict or "").strip().upper()
    if v == VERDICT_FIELD_PROVEN:
        return VERDICT_ADEQUATE
    if v in (VERDICT_ADEQUATE, VERDICT_NEEDS_MORE, VERDICT_INSUFFICIENT):
        return v
    return VERDICT_INSUFFICIENT


def deterministic_adequacy(bars: PlanBarsResult, *, runner_all_passed: bool) -> str:
    """
    Closed-form adequacy without LLM.
    ADEQUATE only when runner green and min bars met (not weak/baseline-only).
    """
    if not runner_all_passed:
        return VERDICT_INSUFFICIENT
    if bars.meets_min_bars:
        return VERDICT_ADEQUATE
    if bars.weak_plan or bars.baseline_only:
        return VERDICT_NEEDS_MORE
    if bars.product_nontrivial < bars.min_product or bars.integration_nontrivial < bars.min_integration:
        return VERDICT_NEEDS_MORE
    return VERDICT_INSUFFICIENT


@dataclass
class DualGateDecision:
    """Outcome of dual-gate (mechanical + adequacy + bars)."""

    status: str
    mechanical_status: str  # field_test_passed | field_test_failed | (empty)
    runner_all_passed: bool
    adequacy: str
    bars: PlanBarsResult
    field_proven: bool
    reason: str
    ok: bool = False  # True only when field_proven

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mechanical_status": self.mechanical_status,
            "runner_all_passed": self.runner_all_passed,
            "adequacy": self.adequacy,
            "bars": self.bars.to_dict(),
            "field_proven": self.field_proven,
            "reason": self.reason,
            "ok": self.ok,
        }


def decide_field_status(
    *,
    runner_all_passed: bool,
    bars: PlanBarsResult | None = None,
    evaluator_verdict: str | None = None,
    dual_gate: bool | None = None,
    field_tests_md: str | Path = "",
) -> DualGateDecision:
    """
    Decide terminal/intermediate ship status.

    Dual gate ON (default):
      runner fail  → cannot field_proven (status ship_insufficient / field_test_failed)
      runner pass  → mechanical field_test_passed
      field_proven only if ADEQUATE + min bars

    Dual gate OFF (legacy):
      runner pass → field_proven (no adequacy required)
    """
    use_dual = dual_gate_enabled() if dual_gate is None else dual_gate
    if bars is None:
        bars = assess_plan_bars(field_tests_md)

    if not runner_all_passed:
        # LLM cannot invent passes
        return DualGateDecision(
            status="ship_insufficient",
            mechanical_status="field_test_failed",
            runner_all_passed=False,
            adequacy=VERDICT_INSUFFICIENT,
            bars=bars,
            field_proven=False,
            reason="runner failed — sole execution oracle; not field_proven",
            ok=False,
        )

    mechanical = "field_test_passed"

    if not use_dual:
        return DualGateDecision(
            status="field_proven",
            mechanical_status=mechanical,
            runner_all_passed=True,
            adequacy=VERDICT_ADEQUATE,
            bars=bars,
            field_proven=True,
            reason="legacy single-gate: runner all_passed",
            ok=True,
        )

    # Adequacy: explicit evaluator wins if provided; else deterministic
    if evaluator_verdict:
        adequacy = normalize_adequacy(evaluator_verdict)
        # Never promote LLM ADEQUATE without bars
        if adequacy == VERDICT_ADEQUATE and not bars.meets_min_bars:
            adequacy = VERDICT_NEEDS_MORE
    else:
        adequacy = deterministic_adequacy(bars, runner_all_passed=True)

    if adequacy == VERDICT_ADEQUATE and bars.meets_min_bars:
        return DualGateDecision(
            status="field_proven",
            mechanical_status=mechanical,
            runner_all_passed=True,
            adequacy=VERDICT_ADEQUATE,
            bars=bars,
            field_proven=True,
            reason="runner pass + ADEQUATE + min product/integration bars",
            ok=True,
        )

    if adequacy == VERDICT_NEEDS_MORE or not bars.meets_min_bars:
        why = "; ".join(bars.reasons) if bars.reasons else adequacy
        return DualGateDecision(
            status="field_test_passed",
            mechanical_status=mechanical,
            runner_all_passed=True,
            adequacy=VERDICT_NEEDS_MORE
            if adequacy != VERDICT_INSUFFICIENT
            else adequacy,
            bars=bars,
            field_proven=False,
            reason=f"mechanical pass only — not field_proven ({why})",
            ok=False,
        )

    return DualGateDecision(
        status="field_test_passed",
        mechanical_status=mechanical,
        runner_all_passed=True,
        adequacy=adequacy,
        bars=bars,
        field_proven=False,
        reason=f"mechanical pass only — adequacy={adequacy}",
        ok=False,
    )


def write_adequacy_note(
    project_dir: Path,
    decision: DualGateDecision,
    *,
    plan_engine: str = "",
) -> Path:
    """Write phases/ship/ship_evaluation.md with closed dual-gate verdict (no LLM invent)."""
    project_dir = Path(project_dir)
    path = project_dir / "phases" / "ship" / "ship_evaluation.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    bars = decision.bars
    body = f"""# Ship Evaluation (dual gate)

- Plan engine: {plan_engine or "n/a"}
- Runner (sole oracle): {"PASS" if decision.runner_all_passed else "FAIL"}
- Mechanical status: {decision.mechanical_status}
- Min bars: product_nontrivial={bars.product_nontrivial}/{bars.min_product}, integration_nontrivial={bars.integration_nontrivial}/{bars.min_integration}
- Weak plan: {bars.weak_plan}
- Baseline only: {bars.baseline_only}

## Phase validation
- Thin dual-gate path (deterministic bars; optional LLM elsewhere).

## Field test adequacy
- Non-trivial product tasks: {", ".join(bars.product_ids) or "(none)"}
- Non-trivial integration tasks: {", ".join(bars.integration_ids) or "(none)"}
- Reasons: {"; ".join(bars.reasons) or "n/a"}

## Shippability
- field_proven requires: runner all_passed AND Adequacy ADEQUATE AND min bars.
- Baseline B* and help/syntax/import-only plans never suffice alone.

## Recommended maturity (M2 field-tested / M3 refactored-debugged)
- {"M2" if decision.field_proven else "n/a — not field_proven"}

## Verdict
Adequacy: {decision.adequacy}
Verdict: {VERDICT_FIELD_PROVEN if decision.field_proven else decision.adequacy}

## Dual-gate decision
- Final status: {decision.status}
- Reason: {decision.reason}
"""
    path.write_text(body, encoding="utf-8")
    return path
