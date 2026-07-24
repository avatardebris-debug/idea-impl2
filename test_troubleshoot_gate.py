"""Unit tests for pipeline.troubleshoot_gate (v0 algorithmic recovery)."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.troubleshoot_gate import (
    ACTION_ASK_OPERATOR,
    ACTION_DEBUG_TARGETED,
    ACTION_FIELD_REPAIR_ONCE,
    ACTION_FIX_GATE_ONLY,
    ACTION_PARK,
    ACTION_REPLAN_MASTER,
    ACTION_REPLAN_PHASE,
    CLASS_CREDENTIALS_HUMAN,
    CLASS_GATE_FALSE_BLOCK,
    CLASS_PLAN_INSUFFICIENT,
    CLASS_PRODUCT_BUG,
    CLASS_SCOPE_DRIFT,
    CLASS_SPIN_NO_PROGRESS,
    SCHEMA,
    collect_evidence,
    extract_fail_tags,
    fail_fingerprint,
    main as troubleshoot_main,
    run_troubleshoot_gate,
    set_ship_outcome,
    tags_and_fingerprint,
    write_field_test_results_json,
)


def _write_tasks(project: Path, phase: int, *, open_n: int, done_n: int) -> None:
    d = project / "phases" / f"phase_{phase}"
    d.mkdir(parents=True, exist_ok=True)
    lines = [f"# Phase {phase} Tasks", ""]
    for i in range(1, done_n + 1):
        lines.append(f"- [x] Task {i}: done work {i}")
    for i in range(done_n + 1, done_n + open_n + 1):
        lines.append(f"- [ ] Task {i}: open work {i}")
    (d / "tasks.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _base_proj(
    tmp: Path,
    *,
    slug: str = "proj",
    status: str = "ship_insufficient",
    phase: int = 5,
    total: int = 5,
) -> Path:
    p = tmp / slug
    (p / "workspace").mkdir(parents=True)
    (p / "state").mkdir(parents=True)
    (p / "phases" / "ship").mkdir(parents=True)
    idea = {
        "title": slug,
        "status": status,
        "phase": phase,
        "total_phases": total,
        "engine": "grok_build",
        "slug": slug,
        "field_ship_reason": "field FAIL passed=1 failed=2",
    }
    (p / "state" / "current_idea.json").write_text(
        json.dumps(idea, indent=2), encoding="utf-8"
    )
    return p


def test_extract_fail_tags_auth():
    text = "SMTP auth failed: 401 Unauthorized oauth token invalid"
    tags = extract_fail_tags(text)
    assert "auth" in tags
    assert "credentials" in tags


def test_extract_fail_tags_permission_denied_not_auth():
    """Filesystem ACL noise must not become credentials_human."""
    tags = extract_fail_tags("open('/secret'): Permission denied\nPermissionError: [Errno 13]")
    assert "auth" not in tags
    assert "credentials" not in tags
    assert "env_runtime" in tags


def test_extract_fail_tags_syntax_import():
    text = (
        'File "backend/app/routers/schedules.py", line 14\n'
        "    SyntaxError: invalid syntax\n"
        "ModuleNotFoundError: No module named 'backend.routers'\n"
    )
    tags = extract_fail_tags(text)
    assert "syntax" in tags
    assert "import" in tags


def test_video_management_like_syntax_beats_gate(tmp_path: Path):
    """review PASS + complete_blocked older phase + field syntax → DEBUG_TARGETED."""
    p = _base_proj(tmp_path, slug="video_like", phase=5, total=5)
    _write_tasks(p, 1, open_n=5, done_n=0)
    for ph in range(2, 6):
        _write_tasks(p, ph, open_n=0, done_n=5)
    (p / "phases" / "phase_5" / "review.md").write_text(
        "# Review\n\nVerdict: PASS\n", encoding="utf-8"
    )
    state = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    state["complete_blocked_reason"] = (
        "5 open task checkbox(es) on project (20/25 done). "
        "Open: Task 1: Database models"
    )
    state["review_result"] = {"blocking_bugs": 0, "review_fail": False}
    (p / "state" / "current_idea.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    results = """# Field Test Results
- Passed: 3
- Failed: 2

## B3: No stale local imports — FAIL
- Detail: schedules.py:14 [syntax] invalid syntax

## P1: Package module help — FAIL
```
ModuleNotFoundError: No module named 'backend.routers'
File "backend/main.py", line 6
```

## Verdict: FAIL
"""
    (p / "phases" / "ship" / "field_test_results.md").write_text(
        results, encoding="utf-8"
    )
    decision = run_troubleshoot_gate(
        p, status="ship_insufficient", field_results_text=results, write=True
    )
    assert decision["schema"] == SCHEMA
    assert decision["recommended_action"] == ACTION_DEBUG_TARGETED
    assert decision["primary_class"] == CLASS_PRODUCT_BUG
    assert CLASS_GATE_FALSE_BLOCK in decision["secondary_classes"]
    assert "syntax" in decision["fail_tags"] or "import" in decision["fail_tags"]
    assert (p / "state" / "recovery_decision.json").is_file()
    assert (p / "state" / "recovery_history.jsonl").is_file()
    st = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert st.get("ship_outcome") == "ship_insufficient"
    assert st.get("ship_outcome_at")


def test_video_management_like_gate_only_without_syntax(tmp_path: Path):
    """Same gate pattern but clean field → FIX_GATE_ONLY."""
    p = _base_proj(tmp_path, slug="gate_only", phase=5, total=5)
    _write_tasks(p, 1, open_n=5, done_n=0)
    for ph in range(2, 6):
        _write_tasks(p, ph, open_n=0, done_n=5)
    (p / "phases" / "phase_5" / "review.md").write_text(
        "Verdict: PASS\n", encoding="utf-8"
    )
    state = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    state["complete_blocked_reason"] = "5 open task checkbox(es) on project (20/25 done)."
    state["review_result"] = {"blocking_bugs": 0, "review_fail": False}
    state["field_ship_reason"] = "field FAIL passed=0 failed=1"
    (p / "state" / "current_idea.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    results = """# Field Test Results
- Passed: 0
- Failed: 0

## Verdict: FAIL
"""
    decision = run_troubleshoot_gate(
        p, status="ship_insufficient", field_results_text=results, write=True
    )
    assert decision["recommended_action"] == ACTION_FIX_GATE_ONLY
    assert decision["primary_class"] == CLASS_GATE_FALSE_BLOCK


def test_pocketknife_like_replan_master(tmp_path: Path):
    """TypeError product bug takes priority; feature-gap with open late phases → replan."""
    p = _base_proj(tmp_path, slug="pocket_like", phase=9, total=9)
    _write_tasks(p, 1, open_n=2, done_n=5)
    _write_tasks(p, 2, open_n=0, done_n=6)
    _write_tasks(p, 3, open_n=0, done_n=6)
    for ph in range(4, 10):
        _write_tasks(p, ph, open_n=3, done_n=0)

    type_err = """# Field Test Results
- Passed: 2
- Failed: 4

## P1: create windows — FAIL
```
TypeError: WindowManager.create_window() missing 1 required positional argument
```

## Verdict: FAIL
"""
    decision = run_troubleshoot_gate(
        p, status="ship_insufficient", field_results_text=type_err, write=True
    )
    assert decision["recommended_action"] == ACTION_DEBUG_TARGETED
    assert decision["primary_class"] == CLASS_PRODUCT_BUG
    assert "runtime_error" in decision["fail_tags"]

    results2 = """# Field Test Results
- Passed: 2
- Failed: 3

## P1: feature incomplete — FAIL
```
expected behavior not implemented for multi-window layout
```

## Verdict: FAIL
"""
    decision2 = run_troubleshoot_gate(
        p, status="ship_insufficient", field_results_text=results2, write=True
    )
    assert decision2["recommended_action"] in (ACTION_REPLAN_MASTER, ACTION_REPLAN_PHASE)
    assert decision2["primary_class"] in (CLASS_PLAN_INSUFFICIENT, CLASS_SCOPE_DRIFT)


def test_pocketknife_replan_no_product_errors(tmp_path: Path):
    p = _base_proj(tmp_path, slug="pocket2", phase=9, total=9)
    for ph in range(1, 4):
        _write_tasks(p, ph, open_n=0, done_n=5)
    for ph in range(4, 10):
        _write_tasks(p, ph, open_n=3, done_n=0)
    results = """# Field Test Results
- Passed: 2
- Failed: 2

## P1: feature gap — FAIL
- Detail: expected behavior not implemented

## Verdict: FAIL
"""
    decision = run_troubleshoot_gate(
        p, status="ship_insufficient", field_results_text=results, write=True
    )
    assert decision["recommended_action"] in (ACTION_REPLAN_MASTER, ACTION_REPLAN_PHASE)
    assert decision["primary_class"] in (CLASS_PLAN_INSUFFICIENT, CLASS_SCOPE_DRIFT)


def test_auth_like_ask_operator(tmp_path: Path):
    p = _base_proj(tmp_path, slug="email_auth", phase=3, total=3)
    _write_tasks(p, 3, open_n=0, done_n=4)
    results = """# Field Test Results
- Passed: 1
- Failed: 2

## P1: send mail — FAIL
```
smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')
401 Unauthorized oauth token invalid credentials required
```

## Verdict: FAIL
"""
    decision = run_troubleshoot_gate(
        p, status="ship_insufficient", field_results_text=results, write=True
    )
    assert decision["recommended_action"] == ACTION_ASK_OPERATOR
    assert decision["primary_class"] == CLASS_CREDENTIALS_HUMAN
    assert decision["confidence"] == "high"


def test_plan_mismatch_field_repair(tmp_path: Path):
    p = _base_proj(tmp_path, slug="plan_mm", phase=2, total=3)
    _write_tasks(p, 2, open_n=1, done_n=2)
    results = """# Field Test Results
- Passed: 2
- Failed: 2

## P1: run tool — FAIL
```
'foocli' is not recognized as an internal or external command
command not found
```

## Verdict: FAIL
"""
    decision = run_troubleshoot_gate(
        p, status="ship_insufficient", field_results_text=results, write=True
    )
    assert decision["recommended_action"] == ACTION_FIELD_REPAIR_ONCE
    assert decision["primary_class"] == "plan_mismatch"


def test_plan_failed_reason_field_repair(tmp_path: Path):
    p = _base_proj(tmp_path, slug="plan_fail", phase=1, total=1)
    state = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    state["field_ship_reason"] = "plan failed: no plan backend succeeded"
    (p / "state" / "current_idea.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    decision = run_troubleshoot_gate(
        p,
        status="ship_insufficient",
        field_results_text="",
        write=True,
    )
    assert decision["recommended_action"] == ACTION_FIELD_REPAIR_ONCE
    assert decision["primary_class"] == "plan_mismatch"


def test_set_ship_outcome_sticky(tmp_path: Path):
    p = _base_proj(tmp_path)
    st = set_ship_outcome(p, "field_proven")
    assert st["ship_outcome"] == "field_proven"
    assert "ship_outcome_at" in st
    disk = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert disk["ship_outcome"] == "field_proven"


def test_set_ship_outcome_unknown_noop(tmp_path: Path):
    p = _base_proj(tmp_path)
    before = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    st = set_ship_outcome(p, "not_a_real_outcome")
    assert "ship_outcome" not in st or st.get("ship_outcome") == before.get("ship_outcome")


def test_write_field_test_results_json(tmp_path: Path):
    p = _base_proj(tmp_path)

    class FakeRun:
        passed = 2
        failed = 1
        all_passed = False
        results = [
            {
                "task_id": "P1",
                "title": "x",
                "kind": "product",
                "passed": False,
                "command": "echo hi",
                "output_tail": "boom",
            }
        ]

    path = write_field_test_results_json(p, FakeRun(), plan_engine="heuristic")
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == "field_test_results.v1"
    assert data["failed"] == 1
    assert data["results"][0]["task_id"] == "P1"


def test_explicit_field_text_ignores_stale_json_zero(tmp_path: Path):
    """Caller-provided results_md wins; JSON zero must not clobber via falsy or."""
    p = _base_proj(tmp_path, slug="json_zero")
    (p / "phases" / "ship" / "field_test_results.json").write_text(
        json.dumps({"passed": 0, "failed": 9}), encoding="utf-8"
    )
    md = """# Field Test Results
- Passed: 4
- Failed: 0

## Verdict: PASS
"""
    ev = collect_evidence(p, field_results_text=md)
    assert ev.field_passed == 4
    assert ev.field_failed == 0


def test_json_zero_counts_when_no_explicit_text(tmp_path: Path):
    p = _base_proj(tmp_path, slug="json_disk")
    (p / "phases" / "ship" / "field_test_results.md").write_text(
        "# Field Test Results\n- Passed: 5\n- Failed: 5\n", encoding="utf-8"
    )
    (p / "phases" / "ship" / "field_test_results.json").write_text(
        json.dumps({"passed": 0, "failed": 0}), encoding="utf-8"
    )
    ev = collect_evidence(p)
    assert ev.field_passed == 0
    assert ev.field_failed == 0


def test_dry_run_no_write(tmp_path: Path):
    p = _base_proj(tmp_path)
    decision = run_troubleshoot_gate(
        p,
        status="ship_insufficient",
        field_results_text='## X — FAIL\nSyntaxError: invalid syntax\nFile "a.py"\n',
        write=False,
        set_outcome=False,
    )
    assert decision["recommended_action"] == ACTION_DEBUG_TARGETED
    assert not (p / "state" / "recovery_decision.json").is_file()


def test_history_appends(tmp_path: Path):
    p = _base_proj(tmp_path)
    run_troubleshoot_gate(
        p,
        status="ship_insufficient",
        field_results_text="401 Unauthorized credentials",
        write=True,
    )
    run_troubleshoot_gate(
        p,
        status="ship_insufficient",
        field_results_text="401 Unauthorized credentials",
        write=True,
    )
    lines = (
        (p / "state" / "recovery_history.jsonl")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    )
    assert len(lines) == 2


def test_spin_park_after_repeated_same_fingerprint(tmp_path: Path):
    """Same syntax failure ≥3 times → PARK (spin override), not endless DEBUG."""
    p = _base_proj(tmp_path, slug="spin_syntax")
    results = """# Field Test Results
- Passed: 0
- Failed: 1

## P1: syntax — FAIL
```
File "C:\\Users\\avata\\proj\\workspace\\app.py", line 3
SyntaxError: invalid syntax
```

## Verdict: FAIL
"""
    actions = []
    for _ in range(5):
        d = run_troubleshoot_gate(
            p,
            status="ship_insufficient",
            field_results_text=results,
            write=True,
        )
        actions.append(d["recommended_action"])
    # First two (prior same fp 0 then 1) stay DEBUG; from 3rd (same>=2) → PARK
    assert actions[0] == ACTION_DEBUG_TARGETED
    assert actions[1] == ACTION_DEBUG_TARGETED
    assert actions[2] == ACTION_PARK
    assert actions[-1] == ACTION_PARK
    last = json.loads((p / "state" / "recovery_decision.json").read_text(encoding="utf-8"))
    assert last["primary_class"] == CLASS_SPIN_NO_PROGRESS
    assert CLASS_PRODUCT_BUG in last.get("secondary_classes", [])


def test_fail_fingerprint_stable_across_path_and_number_churn():
    tags = ["syntax", "import"]
    s1 = [
        'File "C:\\Users\\avata\\a\\workspace\\mod.py", line 14: SyntaxError',
        "failed 3 times",
    ]
    s2 = [
        'File "D:\\other\\path\\workspace\\mod.py", line 99: SyntaxError',
        "failed 12 times",
    ]
    fp1 = fail_fingerprint(tags, s1, status="ship_insufficient")
    fp2 = fail_fingerprint(tags, s2, status="ship_insufficient")
    assert fp1 == fp2
    assert len(fp1) == 16


def test_tags_and_fingerprint_includes_field_ship_reason(tmp_path: Path):
    """Annotate/classify share blob — plan-failed reason must affect fingerprint."""
    from pipeline.troubleshoot_gate import EvidenceBundle, tags_and_fingerprint

    ev = EvidenceBundle(
        slug="x",
        status="ship_insufficient",
        field_results_text="",
        field_ship_reason="plan failed: heuristic backend down",
        fail_snippets=[],
    )
    tags, fp, blob = tags_and_fingerprint(ev)
    assert "plan failed" in blob.lower()
    assert fp
    # Same reason → same fp
    _, fp2, _ = tags_and_fingerprint(ev)
    assert fp == fp2


def test_collect_evidence_reads_phases(tmp_path: Path):
    p = _base_proj(tmp_path, phase=3, total=3)
    _write_tasks(p, 1, open_n=2, done_n=0)
    _write_tasks(p, 3, open_n=0, done_n=4)
    ev = collect_evidence(p)
    assert ev.earlier_open == 2
    assert ev.current_phase_done == 4
    assert ev.phase == 3


def test_cli_missing_project_dir_exit_2(tmp_path: Path):
    missing = tmp_path / "does_not_exist"
    rc = troubleshoot_main(["--project-dir", str(missing)])
    assert rc == 2


def test_cli_dry_run(tmp_path: Path, capsys):
    p = _base_proj(tmp_path, slug="cli_dry")
    (p / "phases" / "ship" / "field_test_results.md").write_text(
        "## X — FAIL\nSyntaxError: invalid syntax\nFile \"a.py\"\n",
        encoding="utf-8",
    )
    rc = troubleshoot_main(["--project-dir", str(p), "--dry-run", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["recommended_action"] == ACTION_DEBUG_TARGETED
    assert not (p / "state" / "recovery_decision.json").is_file()


def test_thin_ship_hooks_troubleshoot(tmp_path: Path, monkeypatch):
    """End-to-end: failing thin ship writes recovery_decision + ship_outcome."""
    from pipeline.engines.field_ship import run_thin_field_ship

    p = _base_proj(tmp_path, slug="hook_proj", status="complete", phase=1, total=1)
    (p / "workspace" / "cli.py").write_text(
        "import sys\nsys.exit(1)\n", encoding="utf-8"
    )
    py = __import__("sys").executable
    (p / "phases" / "ship" / "field_tests.md").write_text(
        f"""# Field Tests
## Product tests
- [ ] Task P1: fail always
  - Kind: product
  - Command: `{py} cli.py`
  - Expect: exit 0
## Integration tests
- [ ] Task I1: also fail
  - Kind: integration
  - Command: `{py} cli.py`
  - Expect: exit 0
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("FIELD_PLAN_ENGINE", "none")
    monkeypatch.setenv("GROK_BUILD_THIN_SHIP", "1")
    monkeypatch.setenv("FIELD_SHIP_REPAIR", "0")
    monkeypatch.setenv("FIELD_SHIP_USEFULNESS", "0")
    state = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    result = run_thin_field_ship(p, state, slug="hook_proj")
    assert result.status == "ship_insufficient"
    assert (p / "state" / "recovery_decision.json").is_file()
    assert (p / "phases" / "ship" / "field_test_results.json").is_file()
    st = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert st.get("ship_outcome") == "ship_insufficient"
    assert st.get("last_recovery_action")


def test_pre_field_park_runs_gate(tmp_path: Path, monkeypatch):
    """deeper_work_needed pre-field park still gets sticky outcome + recovery_decision."""
    from pipeline.engines.field_ship import run_thin_field_ship

    p = _base_proj(tmp_path, slug="park_pre", status="complete", phase=1, total=1)
    (p / "workspace" / "cli.py").write_text("print('ok')\n", encoding="utf-8")
    state = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    # Force over budget
    state["field_rework_attempts"] = 99
    state["field_rework_minutes"] = 999.0
    (p / "state" / "current_idea.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )
    monkeypatch.setenv("GROK_BUILD_THIN_SHIP", "1")
    monkeypatch.setenv("FIELD_SHIP_REPAIR", "0")
    result = run_thin_field_ship(p, state, slug="park_pre")
    assert result.status == "deeper_work_needed"
    st = json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))
    assert st.get("ship_outcome") == "deeper_work_needed"
    assert (p / "state" / "recovery_decision.json").is_file()
    assert st.get("last_recovery_action")
