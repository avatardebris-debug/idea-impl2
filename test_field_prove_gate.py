"""Tests for dual-gate field prove (min bars + ADEQUATE; runner sole oracle)."""

from __future__ import annotations

from pathlib import Path

from pipeline.field_prove_gate import (
    VERDICT_ADEQUATE,
    VERDICT_INSUFFICIENT,
    VERDICT_NEEDS_MORE,
    assess_plan_bars,
    decide_field_status,
    deterministic_adequacy,
    is_trivial_task,
    normalize_adequacy,
    parse_adequacy_verdict,
)
from pipeline.field_test_runner import FieldTestTask, parse_field_tests_md


WEAK_PLAN = """# Field Tests

## Product tests
- [ ] Task P1: help
  - Kind: product
  - Command: `python cli.py --help`
  - Expect: exit 0

- [ ] Task P2: syntax
  - Kind: product
  - Command: `python -m py_compile cli.py`
  - Expect: exit 0

## Integration tests
- [ ] Task I1: import
  - Kind: integration
  - Command: `python -c "import cli; print('IMPORT_OK')"`
  - Expect: IMPORT_OK
"""

STRONG_PLAN = """# Field Tests

## Product tests
- [ ] Task P1: core greet path
  - Kind: product
  - Command: `python cli.py --greet world`
  - Expect: GREET:world

## Integration tests
- [ ] Task I1: write out.json
  - Kind: integration
  - Command: `python cli.py --out out.json`
  - Expect: exit 0
"""

BASELINE_ONLY = """# Field Tests

(no LLM tests generated)
"""


def test_parse_weak_and_strong_counts():
    weak = assess_plan_bars(WEAK_PLAN)
    assert weak.weak_plan is True
    assert weak.meets_min_bars is False
    assert weak.product_nontrivial == 0
    assert weak.integration_nontrivial == 0

    strong = assess_plan_bars(STRONG_PLAN)
    assert strong.weak_plan is False
    assert strong.meets_min_bars is True
    assert strong.product_nontrivial >= 1
    assert strong.integration_nontrivial >= 1


def test_baseline_only_rejected():
    bars = assess_plan_bars(BASELINE_ONLY)
    assert bars.baseline_only or not bars.meets_min_bars
    assert bars.meets_min_bars is False


def test_trivial_task_detection():
    t_help = FieldTestTask(
        task_id="P1",
        title="help",
        kind="product",
        command="python main.py --help",
        expect_exit=0,
    )
    t_real = FieldTestTask(
        task_id="P2",
        title="greet",
        kind="product",
        command="python main.py --greet x",
        expect_substr="GREET:x",
    )
    t_print_only = FieldTestTask(
        task_id="P3",
        title="fake greet",
        kind="product",
        command="""python -c "print('GREET:world')" """,
        expect_substr="GREET:world",
    )
    assert is_trivial_task(t_help) is True
    assert is_trivial_task(t_real) is False
    assert is_trivial_task(t_print_only) is True


def test_print_only_plan_does_not_meet_bars():
    plan = """# Field Tests
## Product tests
- [ ] Task P1: fake
  - Kind: product
  - Command: `python -c "print('GREET:world')"`
  - Expect: GREET:world
## Integration tests
- [ ] Task I1: echo
  - Kind: integration
  - Command: `echo ok`
  - Expect: exit 0
"""
    bars = assess_plan_bars(plan)
    assert bars.meets_min_bars is False
    assert bars.product_nontrivial == 0


def test_decide_runner_fail_never_proven():
    bars = assess_plan_bars(STRONG_PLAN)
    d = decide_field_status(
        runner_all_passed=False,
        bars=bars,
        evaluator_verdict=VERDICT_ADEQUATE,
        dual_gate=True,
    )
    assert d.field_proven is False
    assert d.status != "field_proven"
    assert d.mechanical_status == "field_test_failed"


def test_decide_weak_plan_green_runner_not_proven():
    bars = assess_plan_bars(WEAK_PLAN)
    d = decide_field_status(
        runner_all_passed=True,
        bars=bars,
        dual_gate=True,
    )
    assert d.runner_all_passed is True
    assert d.mechanical_status == "field_test_passed"
    assert d.status == "field_test_passed"
    assert d.field_proven is False
    assert d.ok is False


def test_decide_strong_plan_green_proven():
    bars = assess_plan_bars(STRONG_PLAN)
    d = decide_field_status(
        runner_all_passed=True,
        bars=bars,
        dual_gate=True,
    )
    assert d.field_proven is True
    assert d.status == "field_proven"
    assert d.adequacy == VERDICT_ADEQUATE
    assert d.ok is True


def test_llm_adequate_cannot_override_weak_bars():
    bars = assess_plan_bars(WEAK_PLAN)
    d = decide_field_status(
        runner_all_passed=True,
        bars=bars,
        evaluator_verdict=VERDICT_ADEQUATE,
        dual_gate=True,
    )
    assert d.field_proven is False
    assert d.status == "field_test_passed"


def test_legacy_dual_gate_off():
    bars = assess_plan_bars(WEAK_PLAN)
    d = decide_field_status(
        runner_all_passed=True,
        bars=bars,
        dual_gate=False,
    )
    assert d.field_proven is True
    assert d.status == "field_proven"


def test_parse_adequacy_verdicts():
    assert (
        parse_adequacy_verdict("## Verdict\nAdequacy: ADEQUATE\nVerdict: FIELD_PROVEN\n")
        in (VERDICT_ADEQUATE, "FIELD_PROVEN")
    )
    assert (
        parse_adequacy_verdict("Verdict: NEEDS_MORE_FIELD_TESTS\n") == VERDICT_NEEDS_MORE
    )
    assert parse_adequacy_verdict("Verdict: FIELD_PROVEN\n") == "FIELD_PROVEN"
    assert normalize_adequacy("FIELD_PROVEN") == VERDICT_ADEQUATE
    assert parse_adequacy_verdict("no verdict here") == VERDICT_INSUFFICIENT


def test_parse_adequacy_last_wins_override():
    """Appended dual-gate demotion must win over earlier ADEQUATE."""
    body = """# Ship Evaluation
## Verdict
Adequacy: ADEQUATE
Verdict: FIELD_PROVEN

## Dual-gate override
Adequacy forced — bars not met
Adequacy: NEEDS_MORE_FIELD_TESTS
Verdict: NEEDS_MORE_FIELD_TESTS
"""
    assert parse_adequacy_verdict(body) == VERDICT_NEEDS_MORE
    assert normalize_adequacy(parse_adequacy_verdict(body)) == VERDICT_NEEDS_MORE

    insuff = body + "\nAdequacy: SHIP_INSUFFICIENT\nVerdict: SHIP_INSUFFICIENT\n"
    assert parse_adequacy_verdict(insuff) == VERDICT_INSUFFICIENT


def test_dual_gate_enabled_default_on(monkeypatch):
    from pipeline.field_prove_gate import dual_gate_enabled

    monkeypatch.delenv("FIELD_SHIP_DUAL_GATE", raising=False)
    assert dual_gate_enabled() is True


def test_deterministic_adequacy():
    weak = assess_plan_bars(WEAK_PLAN)
    strong = assess_plan_bars(STRONG_PLAN)
    assert deterministic_adequacy(weak, runner_all_passed=True) == VERDICT_NEEDS_MORE
    assert deterministic_adequacy(strong, runner_all_passed=True) == VERDICT_ADEQUATE
    assert deterministic_adequacy(strong, runner_all_passed=False) == VERDICT_INSUFFICIENT


def test_ship_evaluator_parse_and_bars_override():
    """Unit-level: decide_field_status demotes weak plan ADEQUATE (shared gate)."""
    from pipeline.agents.ship_evaluator import ShipEvaluatorAgent

    agent = ShipEvaluatorAgent.__new__(ShipEvaluatorAgent)
    content = "## Verdict\nAdequacy: ADEQUATE\nVerdict: FIELD_PROVEN\n"
    assert agent._parse_verdict(content) in (VERDICT_ADEQUATE, "FIELD_PROVEN")
    bars = assess_plan_bars(WEAK_PLAN)
    assert bars.meets_min_bars is False
    d = decide_field_status(
        runner_all_passed=True,
        bars=bars,
        evaluator_verdict=normalize_adequacy(parse_adequacy_verdict(content)),
        dual_gate=True,
    )
    assert d.field_proven is False
    assert d.adequacy == VERDICT_NEEDS_MORE


def test_min_bars_env(monkeypatch):
    monkeypatch.setenv("FIELD_MIN_PRODUCT", "2")
    monkeypatch.setenv("FIELD_MIN_INTEGRATION", "1")
    # Strong plan has only 1 product → fails when min_product=2
    bars = assess_plan_bars(STRONG_PLAN)
    assert bars.min_product == 2
    assert bars.meets_min_bars is False
