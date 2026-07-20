"""
Thin field ship for engine=grok_build (closed loop after complete).

Plan backends (FIELD_PLAN_ENGINE):
  auto         — existing file → grok CLI → pipeline_llm → heuristic
  grok         — GROK_BUILD_CMD + field_test_plan prompt pack
  pipeline_llm — get_llm(provider/model) e.g. ollama/qwen (no Grok CLI key)
  heuristic    — deterministic smoke plan (no LLM)
  none         — only run if field_tests.md already exists

Run is always local via field_test_runner (no API).

Env:
  GROK_BUILD_THIN_SHIP=1       (default on) run thin ship after grok complete
  FIELD_PLAN_ENGINE=auto|...
  FIELD_SHIP_USEFULNESS=1      (default on) write usefulness_report.md
  PIPELINE_PROVIDER / PIPELINE_MODEL — for pipeline_llm plan backend
  FIELD_PLAN_PROVIDER / FIELD_PLAN_MODEL — optional overrides for plan only
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool
from pipeline.engines.selection import ENGINE_GROK_BUILD, get_project_engine

FIELD_TESTS_REL = Path("phases/ship/field_tests.md")
FIELD_RESULTS_REL = Path("phases/ship/field_test_results.md")
USEFULNESS_REL = Path("phases/ship/usefulness_report.md")
CAPABILITY_CLAIMS_REL = Path("state/capability_claims.md")


@dataclass
class FieldShipResult:
    ok: bool = False
    planned: bool = False
    plan_engine: str = ""
    passed: int = 0
    failed: int = 0
    status: str = ""
    reason: str = ""
    field_tests_path: str = ""
    results_path: str = ""
    usefulness_path: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "planned": self.planned,
            "plan_engine": self.plan_engine,
            "passed": self.passed,
            "failed": self.failed,
            "status": self.status,
            "reason": self.reason,
            "field_tests_path": self.field_tests_path,
            "results_path": self.results_path,
            "usefulness_path": self.usefulness_path,
            "extra": self.extra,
        }


def thin_ship_enabled(
    state: dict[str, Any] | None = None,
    *,
    force: bool = False,
) -> bool:
    """Whether thin field ship may run for this project.

    - grok_build: on by default (GROK_BUILD_THIN_SHIP, default true)
    - classic: only if FIELD_SHIP_ALLOW_CLASSIC=1 or FIELD_SHIP_BULK=1
    - force=True: always (bulk CLI / ops)
    """
    if force:
        return True
    if env_bool("FIELD_SHIP_BULK", default=False):
        return True
    eng = get_project_engine(state) if state is not None else ENGINE_GROK_BUILD
    if eng == ENGINE_GROK_BUILD:
        return env_bool("GROK_BUILD_THIN_SHIP", default=True)
    # classic / other
    return env_bool("FIELD_SHIP_ALLOW_CLASSIC", default=False)


def field_ship_status_eligible(status: str) -> bool:
    """Statuses that bulk / ship-prove may pick for thin field ship."""
    raw = os.environ.get("FIELD_SHIP_STATUSES", "complete").strip()
    allowed = {s.strip() for s in raw.split(",") if s.strip()}
    if not allowed:
        allowed = {"complete"}
    return (status or "").strip() in allowed


def resolve_plan_engine(explicit: str | None = None) -> str:
    raw = (explicit or os.environ.get("FIELD_PLAN_ENGINE", "auto") or "auto")
    val = raw.strip().lower()
    if val in ("auto", "grok", "pipeline_llm", "heuristic", "none"):
        return val
    return "auto"


def _py() -> str:
    return sys.executable


def _ship_dir(project_dir: Path) -> Path:
    d = project_dir / "phases" / "ship"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _workspace_listing(workspace: Path, limit: int = 40) -> str:
    if not workspace.is_dir():
        return "(no workspace)"
    lines: list[str] = []
    for p in sorted(workspace.rglob("*")):
        if not p.is_file():
            continue
        if any(x in p.parts for x in ("__pycache__", ".pytest_cache", ".git", ".field_out")):
            continue
        try:
            rel = p.relative_to(workspace).as_posix()
        except ValueError:
            continue
        lines.append(rel)
        if len(lines) >= limit:
            lines.append("…")
            break
    return "\n".join(lines) if lines else "(empty)"


def _idea_excerpt(project_dir: Path, limit: int = 1200) -> str:
    for rel in ("state/master_plan.md", "state/current_idea.json", "workspace/idea.md"):
        p = project_dir / rel
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:limit]
            except OSError:
                continue
    return ""


def _extract_markdown_doc(text: str) -> str:
    """Prefer fenced markdown block; else body after first # Field Tests."""
    text = (text or "").strip()
    if not text:
        return ""
    fence = re.search(r"```(?:markdown|md)?\s*\n(.*?)```", text, re.DOTALL | re.I)
    if fence:
        return fence.group(1).strip()
    m = re.search(r"(#\s*Field Tests\b.*)", text, re.DOTALL | re.I)
    if m:
        return m.group(1).strip()
    return text


def plan_heuristic(project_dir: Path, workspace: Path) -> str:
    """Deterministic field plan from layout — no LLM."""
    py = _py()
    lines = [
        "# Field Tests",
        "",
        "## Product tests",
    ]
    n = 1

    def add_product(title: str, cmd: str, expect: str) -> None:
        nonlocal n
        lines.append(f"- [ ] Task P{n}: {title}")
        lines.append("  - Kind: product")
        lines.append(f"  - Command: `{cmd}`")
        lines.append(f"  - Expect: {expect}")
        lines.append("")
        n += 1

    # CLI-ish entrypoints
    for name in ("bp_prompts.py", "cli.py", "main.py", "app.py"):
        p = workspace / name
        if p.is_file():
            add_product(
                f"Help for {name}",
                f"{py} {name} --help",
                "exit 0",
            )
            break

    # package main
    for child in sorted(workspace.iterdir()) if workspace.is_dir() else []:
        if child.is_dir() and (child / "__init__.py").is_file():
            if (child / "main.py").is_file() or (child / "__main__.py").is_file():
                mod = child.name
                add_product(
                    f"Package module help {mod}",
                    f"{py} -m {mod}.main --help",
                    "exit 0",
                )
                break

    # syntax check any top-level py
    top_py = sorted(workspace.glob("*.py"))
    if top_py:
        rel = top_py[0].name
        add_product(
            f"Syntax-check {rel}",
            f"{py} -m py_compile {rel}",
            "exit 0",
        )

    lines.append("## Integration tests")
    i = 1
    tests_dir = workspace / "tests"
    if tests_dir.is_dir() and any(tests_dir.glob("test_*.py")):
        lines.append(f"- [ ] Task I{i}: Pytest suite")
        lines.append("  - Kind: integration")
        lines.append(f"  - Command: `{py} -m pytest -q`")
        lines.append("  - Expect: exit 0")
        lines.append("")
        i += 1
    else:
        lines.append(f"- [ ] Task I{i}: Import workspace root modules")
        lines.append("  - Kind: integration")
        # pick first non-test module
        mod = None
        for p in top_py:
            if not p.name.startswith("test_"):
                mod = p.stem
                break
        if mod:
            lines.append(
                f"  - Command: `{py} -c \"import {mod}; print('IMPORT_OK')\"`"
            )
            lines.append("  - Expect: IMPORT_OK")
        else:
            lines.append(f"  - Command: `{py} -c \"print('IMPORT_OK')\"`")
            lines.append("  - Expect: IMPORT_OK")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def plan_via_pipeline_llm(
    project_dir: Path,
    workspace: Path,
    *,
    provider: str | None = None,
    model: str | None = None,
    slug: str = "",
    phase: int = 1,
) -> tuple[bool, str]:
    """Call pipeline LLM (ollama/qwen/grok API/…) to author field_tests.md body."""
    from pipeline.engines.grok_build import render_prompt_for_phase

    # Ensure field_tests_path placeholder is available
    field_path = project_dir / FIELD_TESTS_REL
    pfile, err = render_prompt_for_phase(
        "field_test_plan",
        project_dir=project_dir,
        workspace=workspace,
        slug=slug or project_dir.name,
        phase=phase,
    )
    if err and not pfile:
        return False, f"prompt render failed: {err}"

    base = ""
    if pfile and pfile.is_file():
        base = pfile.read_text(encoding="utf-8", errors="replace")
    else:
        base = (
            f"Write field tests for workspace {workspace}. "
            f"Output # Field Tests markdown with P1/I1 Command/Expect lines."
        )

    context = (
        f"\n\n## Workspace files\n{_workspace_listing(workspace)}\n\n"
        f"## Idea / plan excerpt\n{_idea_excerpt(project_dir)}\n\n"
        f"Write the complete field_tests.md content now. "
        f"Target path: {field_path}\n"
    )

    prov = (
        provider
        or os.environ.get("FIELD_PLAN_PROVIDER")
        or os.environ.get("PIPELINE_PROVIDER")
        or "ollama"
    ).strip()
    mod = (
        model
        or os.environ.get("FIELD_PLAN_MODEL")
        or os.environ.get("PIPELINE_MODEL")
        or ""
    ).strip() or None

    try:
        from llm_interface import get_llm

        llm = get_llm(prov, model=mod, temperature=0.2, slug=slug or project_dir.name)
        msg = llm.chat(
            [
                {
                    "role": "system",
                    "content": (
                        "You write runnable field-test plans for a software project. "
                        "Output only markdown matching the Field Tests contract."
                    ),
                },
                {"role": "user", "content": base + context},
            ]
        )
        body = _extract_markdown_doc(msg.content or "")
        if "# Field Tests" not in body and "Task P" not in body:
            return False, "pipeline_llm response missing Field Tests structure"
        field_path.parent.mkdir(parents=True, exist_ok=True)
        field_path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
        return True, f"pipeline_llm:{prov}:{mod or 'default'}"
    except Exception as exc:
        return False, f"pipeline_llm failed: {exc}"


def plan_via_grok_cli(
    project_dir: Path,
    workspace: Path,
    *,
    slug: str = "",
    phase: int = 1,
) -> tuple[bool, str]:
    """Use GROK_BUILD_CMD with field_test_plan prompt pack."""
    if not os.environ.get("GROK_BUILD_CMD", "").strip():
        return False, "GROK_BUILD_CMD unset"
    from pipeline.engines.grok_build import run_phase_step

    result = run_phase_step(
        slug or project_dir.name,
        phase,
        "field_test_plan",
        project_dir=project_dir,
        workspace=workspace,
    )
    field_path = project_dir / FIELD_TESTS_REL
    if field_path.is_file() and field_path.stat().st_size > 40:
        return True, f"grok_cli exit={result.exit_code}"
    # CLI may put content only in log — treat missing file as fail
    return False, result.error or "grok CLI did not write field_tests.md"


def ensure_field_plan(
    project_dir: Path,
    workspace: Path,
    *,
    plan_engine: str | None = None,
    slug: str = "",
    phase: int = 1,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[bool, str, str]:
    """
    Ensure phases/ship/field_tests.md exists.

    Returns (ok, engine_used, detail).
    """
    project_dir = Path(project_dir)
    workspace = Path(workspace)
    field_path = project_dir / FIELD_TESTS_REL
    engine = resolve_plan_engine(plan_engine)

    def _existing() -> bool:
        return field_path.is_file() and field_path.stat().st_size > 40

    if engine == "none":
        return (_existing(), "none", "existing" if _existing() else "missing field_tests.md")

    if engine == "auto" and _existing():
        return True, "existing", str(field_path)

    order: list[str]
    if engine == "auto":
        order = ["grok", "pipeline_llm", "heuristic"]
    else:
        order = [engine]

    last_detail = ""
    for backend in order:
        if backend == "grok":
            ok, detail = plan_via_grok_cli(
                project_dir, workspace, slug=slug, phase=phase
            )
            last_detail = detail
            if ok:
                return True, "grok", detail
        elif backend == "pipeline_llm":
            ok, detail = plan_via_pipeline_llm(
                project_dir,
                workspace,
                provider=provider,
                model=model,
                slug=slug,
                phase=phase,
            )
            last_detail = detail
            if ok:
                return True, "pipeline_llm", detail
        elif backend == "heuristic":
            body = plan_heuristic(project_dir, workspace)
            field_path.parent.mkdir(parents=True, exist_ok=True)
            field_path.write_text(body, encoding="utf-8")
            return True, "heuristic", "generated smoke plan"
        elif backend == "none":
            break

    if _existing():
        return True, "existing", "kept prior plan after backend failures"
    return False, engine, last_detail or "no plan backend succeeded"


def ensure_capability_claims(
    project_dir: Path,
    *,
    force_stub: bool = False,
) -> Path:
    """Ensure state/capability_claims.md exists (honesty contract for usefulness)."""
    project_dir = Path(project_dir)
    path = project_dir / CAPABILITY_CLAIMS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size > 80 and not force_stub:
        return path

    master = project_dir / "state" / "master_plan.md"
    idea = project_dir / "state" / "current_idea.json"
    title = project_dir.name
    goal_bit = ""
    if master.is_file():
        try:
            text = master.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"##\s*Goal\s*\n(.+?)(?:\n##|\Z)", text, re.DOTALL | re.I)
            if m:
                goal_bit = m.group(1).strip()[:400]
        except OSError:
            pass
    if idea.is_file():
        try:
            import json

            st = json.loads(idea.read_text(encoding="utf-8"))
            title = st.get("title") or title
        except Exception:
            pass

    # Heuristic outcome class from workspace signals
    ws = project_dir / "workspace"
    signals: list[str] = []
    outcome = "software_tool"
    if ws.is_dir():
        names = " ".join(p.name.lower() for p in ws.rglob("*") if p.is_file())
        if "prompt" in names or "sections.yaml" in names:
            outcome = "prompt_artifact"
            signals.append("prompt/yaml templates present")
        if any(p.suffix == ".py" for p in ws.rglob("*.py")):
            signals.append("python modules present")
        if (ws / "tests").is_dir():
            signals.append("tests/ present")

    body = f"""# Capability claims

- Project: {title}
- Updated: {datetime.now(timezone.utc).isoformat()}
- Source: {"stub_auto" if force_stub or not path.is_file() else "existing"}

## Delivers
- Software under `workspace/` matching the written idea / master plan.
- Goal excerpt: {goal_bit or "(see master_plan.md)"}

## Does NOT deliver (be explicit)
- Outcomes not implemented in code (e.g. calling external LLMs, full documents
  if the product only generates prompts/templates).
- Goal-level success without a separate goal-fitness pass.

## External dependencies required outside this tool
- None known from static scan (update if APIs, keys, or human steps are required).

## Primary I/O
- Inputs: see CLI `--help` / idea files in workspace
- Outputs: files produced under workspace (and any documented out dirs)

## Outcome class
- `{outcome}`  (prompt_artifact | final_document | software_tool | data_pipeline | other)
- Signals: {", ".join(signals) or "n/a"}

## Composition hints
- If outcome class is `prompt_artifact`, consider a follow-on project
  `requires: {project_dir.name}` that executes prompts and writes final artifacts.
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_usefulness_report(
    project_dir: Path,
    *,
    run_passed: bool,
    passed: int,
    failed: int,
    plan_engine: str,
) -> Path:
    """Deterministic honesty report (no LLM) — gap for goals later."""
    project_dir = Path(project_dir)
    claims_path = ensure_capability_claims(project_dir)
    claims_excerpt = ""
    try:
        claims_excerpt = claims_path.read_text(encoding="utf-8", errors="replace")[:2000]
    except OSError:
        pass

    path = project_dir / USEFULNESS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    master = project_dir / "state" / "master_plan.md"
    aim = ""
    if master.is_file():
        try:
            text = master.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"##\s*Goal\s*\n(.+?)(?:\n##|\Z)", text, re.DOTALL | re.I)
            if m:
                aim = m.group(1).strip()[:500]
        except OSError:
            pass

    outcome_m = re.search(
        r"Outcome class\s*\n-\s*`([^`]+)`",
        claims_excerpt,
        re.I,
    )
    outcome = outcome_m.group(1) if outcome_m else "unknown"

    body = f"""# Usefulness report (thin ship)

- Generated: {datetime.now(timezone.utc).isoformat()}
- Plan engine: {plan_engine}
- Field result: {"PASS" if run_passed else "FAIL"} ({passed} passed / {failed} failed)
- Outcome class (from capability claims): `{outcome}`

## Goal / plan excerpt
{aim or "(see state/master_plan.md)"}

## Capability claims (excerpt)
See `{CAPABILITY_CLAIMS_REL.as_posix()}`.

```markdown
{claims_excerpt[:1500]}
```

## What field proved
- Runnable product/integration commands against the workspace (see field_test_results.md).
- Build-track quality may already have run (grok_build review/pytest) or only classic complete.

## What field did NOT prove
- That every human *intent* beyond the written idea / claims is satisfied.
- End-to-end outcomes that require external systems (LLM APIs, paid services)
  unless those were explicitly implemented and tested.
- Goal-level success (field-proven ≠ goal-proven).

## Alone vs composition
- If outcome class is `prompt_artifact` (or similar scaffold), field-proven still
  does **not** mean "final human outcome" without another step.
- Suggested next: feature expand, new project with `requires:`, or connector.

## Status
- field_fitness: {"sufficient_for_claims" if run_passed else "insufficient"}
- goal_fitness: not_evaluated
"""
    path.write_text(body, encoding="utf-8")
    return path


def run_thin_field_ship(
    project_dir: Path,
    state: dict[str, Any] | None = None,
    *,
    slug: str = "",
    plan_engine: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    skip_if_terminal: bool = True,
) -> FieldShipResult:
    """
    Plan (if needed) + run field tests + set field_proven / ship_insufficient.

    Intended for engine=grok_build after _mark_complete (status=complete).
    """
    from pipeline.field_test_runner import format_results_markdown, run_all_field_tests
    from pipeline.project_state import _write_state_dict

    project_dir = Path(project_dir)
    state = dict(state or {})
    slug = slug or state.get("_slug") or state.get("slug") or project_dir.name
    result = FieldShipResult()

    status = (state.get("status") or "").strip()
    if skip_if_terminal and status in ("field_proven", "ship_insufficient"):
        result.reason = f"already terminal ship status={status}"
        result.status = status
        return result

    if not thin_ship_enabled(state if state.get("engine") else {"engine": ENGINE_GROK_BUILD}):
        result.reason = (
            "thin ship disabled for this engine "
            f"(engine={get_project_engine(state)}; "
            "set FIELD_SHIP_ALLOW_CLASSIC=1 or FIELD_SHIP_BULK=1 for classic)"
        )
        return result

    ensure_capability_claims(project_dir)

    workspace = project_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _ship_dir(project_dir)
    phase = int(state.get("phase") or state.get("total_phases") or 1)

    state["status"] = "field_test_planning"
    _write_state_dict(project_dir, state)

    ok_plan, eng, detail = ensure_field_plan(
        project_dir,
        workspace,
        plan_engine=plan_engine,
        slug=slug,
        phase=phase,
        provider=provider,
        model=model,
    )
    result.plan_engine = eng
    result.planned = ok_plan
    result.extra["plan_detail"] = detail
    field_path = project_dir / FIELD_TESTS_REL
    result.field_tests_path = str(field_path)

    if not ok_plan:
        state["status"] = "ship_insufficient"
        state["field_ship_reason"] = f"plan failed: {detail}"
        _write_state_dict(project_dir, state)
        result.status = "ship_insufficient"
        result.reason = detail
        return result

    state["status"] = "field_testing"
    _write_state_dict(project_dir, state)

    run = run_all_field_tests(workspace, field_path, include_baseline=True)
    results_md = format_results_markdown(run)
    header = (
        f"# Field Test Results\n\n"
        f"- Plan engine: {eng}\n"
        f"- Thin ship: field plan+run (+ optional repair bridge)\n"
        f"- Product aim: see master_plan / usefulness_report\n\n"
    )
    if results_md.startswith("# Field Test Results"):
        results_md = header + results_md.split("\n", 1)[-1].lstrip("\n")
    else:
        results_md = header + results_md
    results_path = project_dir / FIELD_RESULTS_REL
    results_path.write_text(results_md, encoding="utf-8")
    result.results_path = str(results_path)
    result.passed = run.passed
    result.failed = run.failed

    # Bridge: on FAIL, field-test skill style repair → debug → code-review → report
    # (not full grok_build implement chain)
    if not run.all_passed:
        try:
            from pipeline.engines.field_repair import repair_enabled, run_field_repair_chain

            if repair_enabled():
                state["status"] = "field_testing"  # repair in progress
                _write_state_dict(project_dir, state)
                repair = run_field_repair_chain(
                    project_dir,
                    workspace,
                    slug=slug,
                    phase=phase,
                    initial_results_md=results_md,
                )
                result.extra["repair"] = repair.to_dict()
                # Refresh counts from latest results
                if (project_dir / FIELD_RESULTS_REL).is_file():
                    results_md = (project_dir / FIELD_RESULTS_REL).read_text(
                        encoding="utf-8", errors="replace"
                    )
                if repair.steps_run:
                    result.passed = int(repair.final_passed)
                    result.failed = int(repair.final_failed)
                if repair.passed:
                    run_all_passed = True
                else:
                    run_all_passed = False
                    result.extra["repair_reason"] = repair.reason
            else:
                run_all_passed = False
        except Exception as _rep_exc:
            run_all_passed = False
            result.extra["repair_error"] = str(_rep_exc)
    else:
        run_all_passed = True

    if env_bool("FIELD_SHIP_USEFULNESS", default=True):
        up = write_usefulness_report(
            project_dir,
            run_passed=run_all_passed,
            passed=result.passed,
            failed=result.failed,
            plan_engine=eng,
        )
        result.usefulness_path = str(up)

    if run_all_passed:
        state["status"] = "field_proven"
        state["field_proven_at"] = datetime.now(timezone.utc).isoformat()
        state.pop("field_ship_reason", None)
        result.ok = True
        result.status = "field_proven"
        total = result.passed + result.failed
        result.reason = f"field PASS {result.passed}/{total or result.passed}"
        try:
            from pipeline.ship_provenance import set_maturity

            set_maturity(project_dir, "M4")
        except Exception:
            pass
        try:
            from pipeline.github_publish import maybe_publish_project

            maybe_publish_project(slug, trigger="field_proven")
        except Exception:
            pass
    else:
        state["status"] = "ship_insufficient"
        state["field_ship_reason"] = (
            f"field FAIL passed={result.passed} failed={result.failed}"
        )
        result.status = "ship_insufficient"
        result.reason = state["field_ship_reason"]

    _write_state_dict(project_dir, state)

    try:
        from pipeline.pipeline_activity import log_activity

        log_activity(
            "thin_field_ship",
            slug=slug,
            plan_engine=eng,
            passed=result.passed,
            failed=result.failed,
            status=result.status,
        )
    except Exception:
        pass

    print(
        f"  [thin-ship] {slug}: {result.status} "
        f"(plan={eng}, pass={result.passed}, fail={result.failed})"
    )
    return result
