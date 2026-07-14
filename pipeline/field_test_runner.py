"""Run baseline + LLM-authored field tests against a project workspace."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.import_graph import scan_workspace
from pipeline.workspace_layout import analyze_layout, ensure_package_layout, infer_package_name


@dataclass
class FieldTestTask:
    task_id: str
    title: str
    kind: str  # baseline | product | integration
    command: str = ""
    expect_substr: str = ""
    expect_exit: int | None = 0
    notes: str = ""


@dataclass
class FieldTestRunResult:
    passed: int = 0
    failed: int = 0
    results: list[dict[str, Any]] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and self.passed > 0


def find_entrypoint(workspace: Path) -> Path | None:
    for name in ("main.py", "app.py", "cli.py", "__main__.py"):
        p = workspace / name
        if p.is_file():
            return p
    for p in sorted(workspace.glob("*.py")):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            if 'if __name__ == "__main__"' in text or "if __name__ == '__main__'" in text:
                return p
        except OSError:
            continue
    return None


def baseline_tasks(workspace: Path, *, package_name: str = "") -> list[FieldTestTask]:
    tasks: list[FieldTestTask] = []
    pkg = package_name or infer_package_name(workspace)
    ensure_package_layout(workspace, pkg)
    layout = analyze_layout(workspace, pkg)

    if layout["mode"] == "package":
        mod = layout["package_name"]
        tasks.append(
            FieldTestTask(
                task_id="B1",
                title=f"Run package entrypoint {mod}.main --help",
                kind="baseline",
                command=f"{sys.executable} -m {mod}.main --help",
                expect_exit=0,
            )
        )
        tasks.append(
            FieldTestTask(
                task_id="B2",
                title=f"Syntax-check {mod}/main.py",
                kind="baseline",
                command=f"{sys.executable} -m py_compile {mod}/main.py",
                expect_exit=0,
            )
        )
    else:
        entry = find_entrypoint(workspace)
        if entry:
            rel = entry.relative_to(workspace).as_posix()
            tasks.append(
                FieldTestTask(
                    task_id="B1",
                    title=f"Run entrypoint {rel}",
                    kind="baseline",
                    command=f"{sys.executable} {rel} --help",
                    expect_exit=0,
                )
            )
            tasks.append(
                FieldTestTask(
                    task_id="B2",
                    title=f"Syntax-check {rel}",
                    kind="baseline",
                    command=f"{sys.executable} -m py_compile {rel}",
                    expect_exit=0,
                )
            )
        else:
            tasks.append(
                FieldTestTask(
                    task_id="B1",
                    title="Workspace has at least one .py file",
                    kind="baseline",
                    notes="manual_check:py_exists",
                )
            )

    graph = scan_workspace(workspace)
    tasks.append(
        FieldTestTask(
            task_id="B3",
            title="No stale local imports",
            kind="baseline",
            notes="stale_ref_check",
            expect_substr=(
                "PASS" if not getattr(graph, "has_blocking_issues", graph.has_issues)
                else "FAIL"
            ),
        )
    )
    return tasks


_TASK_LINE = re.compile(
    r"^\s*-\s+\[([ xX])\]\s+(?:Task\s+)?(\w+[\w-]*)\s*:\s*(.+)$",
    re.MULTILINE,
)
_CMD_LINE = re.compile(r"^\s*-\s*Command:\s*`([^`]+)`", re.MULTILINE | re.IGNORECASE)
_EXPECT_LINE = re.compile(
    r"^\s*-\s*Expect:\s*(.+)$", re.MULTILINE | re.IGNORECASE
)
_KIND_LINE = re.compile(r"^\s*-\s*Kind:\s*(\w+)", re.MULTILINE | re.IGNORECASE)
_EXIT_EXPECT = re.compile(r"^exit\s+(\d+)\s*$", re.IGNORECASE)

# Workspace harness scripts — not part of the shipped package.
_HARNESS_ROOT_FILES = frozenset({"conftest.py", "quick_test.py", "sweep_test.py"})


def _parse_expect_line(raw: str) -> tuple[int | None, str]:
    """Parse Expect: line — supports exit N or output substring (quotes stripped)."""
    text = raw.strip().strip("'\"")
    exit_m = _EXIT_EXPECT.match(text)
    if exit_m:
        return int(exit_m.group(1)), ""
    return None, text


def parse_field_tests_md(content: str) -> list[FieldTestTask]:
    """Parse LLM/product section from field_tests.md."""
    tasks: list[FieldTestTask] = []
    blocks = re.split(r"(?=^\s*-\s+\[[ xX]\]\s+)", content, flags=re.MULTILINE)
    for block in blocks:
        m = _TASK_LINE.search(block)
        if not m:
            continue
        task_id, title = m.group(2), m.group(3).strip()
        kind_m = _KIND_LINE.search(block)
        kind = kind_m.group(1).lower() if kind_m else "product"
        cmd_m = _CMD_LINE.search(block)
        exp_m = _EXPECT_LINE.search(block)
        command = cmd_m.group(1).strip() if cmd_m else ""
        expect_exit: int | None = 0
        expect_substr = ""
        if exp_m:
            parsed_exit, expect_substr = _parse_expect_line(exp_m.group(1))
            if parsed_exit is not None:
                expect_exit = parsed_exit
            elif expect_substr:
                # Output substring checks still require a successful command.
                expect_exit = 0
        tasks.append(
            FieldTestTask(
                task_id=task_id,
                title=title,
                kind=kind,
                command=command,
                expect_substr=expect_substr,
                expect_exit=expect_exit,
            )
        )
    return tasks


def _run_shell(workspace: Path, command: str, timeout: int = 120) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        shell=True,
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, combined


def run_task(workspace: Path, task: FieldTestTask) -> dict[str, Any]:
    if task.notes == "stale_ref_check":
        graph = scan_workspace(workspace)
        # Only local graph / syntax / path issues block ship B3
        ok = not getattr(graph, "has_blocking_issues", graph.has_issues)
        return {
            "task_id": task.task_id,
            "title": task.title,
            "kind": task.kind,
            "passed": ok,
            "detail": graph.format_block(10) if not ok else "No stale refs",
        }
    if task.notes == "manual_check:py_exists":
        ok = any(workspace.rglob("*.py"))
        return {
            "task_id": task.task_id,
            "title": task.title,
            "kind": task.kind,
            "passed": ok,
            "detail": "found .py" if ok else "no .py files",
        }
    if not task.command:
        return {
            "task_id": task.task_id,
            "title": task.title,
            "kind": task.kind,
            "passed": False,
            "detail": "no Command: line in field test task",
        }

    try:
        rc, output = _run_shell(workspace, task.command)
    except subprocess.TimeoutExpired:
        return {
            "task_id": task.task_id,
            "title": task.title,
            "kind": task.kind,
            "passed": False,
            "detail": f"timeout running: {task.command}",
        }

    passed = True
    if task.expect_exit is not None and rc != task.expect_exit:
        passed = False
    if task.expect_substr:
        # Normalize JSON-ish output: match substring after collapsing whitespace.
        needle = task.expect_substr
        haystack = output
        if needle not in haystack and needle.upper() not in haystack.upper():
            collapsed_needle = " ".join(needle.split())
            collapsed_hay = " ".join(haystack.split())
            if collapsed_needle.upper() not in collapsed_hay.upper():
                passed = False

    return {
        "task_id": task.task_id,
        "title": task.title,
        "kind": task.kind,
        "passed": passed,
        "returncode": rc,
        "output_tail": output[-2000:] if output else "",
        "command": task.command,
    }


def run_all_field_tests(
    workspace: Path,
    field_tests_md: Path,
    *,
    include_baseline: bool = True,
    package_name: str = "",
) -> FieldTestRunResult:
    run = FieldTestRunResult()
    pkg = package_name or infer_package_name(workspace)
    changed, repair_msg = ensure_package_layout(workspace, pkg)
    if changed:
        print(f"  [field-test] Layout repair: {repair_msg}")
    tasks: list[FieldTestTask] = []
    if include_baseline:
        tasks.extend(baseline_tasks(workspace, package_name=pkg))
    if field_tests_md.is_file():
        content = field_tests_md.read_text(encoding="utf-8", errors="replace")
        tasks.extend(parse_field_tests_md(content))

    for task in tasks:
        row = run_task(workspace, task)
        run.results.append(row)
        if row.get("passed"):
            run.passed += 1
        else:
            run.failed += 1
    return run


def format_results_markdown(run: FieldTestRunResult) -> str:
    lines = [
        "# Field Test Results",
        "",
        f"- Passed: {run.passed}",
        f"- Failed: {run.failed}",
        "",
    ]
    for row in run.results:
        status = "PASS" if row.get("passed") else "FAIL"
        lines.append(f"## {row.get('task_id', '?')}: {row.get('title', '')} — {status}")
        lines.append(f"- Kind: {row.get('kind', '?')}")
        if row.get("command"):
            lines.append(f"- Command: `{row['command']}`")
        if row.get("detail"):
            lines.append(f"- Detail: {row['detail'][:500]}")
        if row.get("output_tail"):
            lines.append("```")
            lines.append(row["output_tail"][-1500:])
            lines.append("```")
        lines.append("")
    verdict = "Verdict: PASS" if run.all_passed else "Verdict: FAIL"
    lines.append(f"## {verdict}")
    return "\n".join(lines)
