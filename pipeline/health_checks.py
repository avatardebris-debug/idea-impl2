"""
pipeline/health_checks.py
Deterministic self-healing checks that run every health-check cycle.

These are pure Python — NO LLM calls. They catch and fix the most common
failure modes that otherwise require human intervention:

1. Stray files outside workspace (src/, tests/ at project root)
2. Import resolution (missing pip packages)
3. Workspace consistency (tasks say done but files missing)
4. Queue health (stuck messages, duplicate messages)
5. State consistency (status says X but evidence says Y)
6. Path validation (all source files inside workspace)
"""

from __future__ import annotations

import json
import logging
import pathlib
import re
import shutil
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from pipeline.path_health import (
    BUILD_ARTIFACT_SUFFIXES,
    ROOT_INFRA_DIRS,
    ROOT_INFRA_FILES,
    find_workspace_shadows,
    is_root_infra_file,
    prune_workspace_shadows,
    rescue_dir_filtered,
)

_INFRA_FILES = ROOT_INFRA_FILES
_INFRA_DIRS = ROOT_INFRA_DIRS
_BUILD_ARTIFACT_PATTERNS = BUILD_ARTIFACT_SUFFIXES


class HealthCheckResult:
    """Container for a single health check finding."""

    def __init__(self, check_name: str, severity: str, message: str,
                 auto_fixed: bool = False, fix_detail: str = ""):
        self.check_name = check_name
        self.severity = severity  # "info", "warning", "error", "critical"
        self.message = message
        self.auto_fixed = auto_fixed
        self.fix_detail = fix_detail

    def __repr__(self) -> str:
        fix = " [AUTO-FIXED]" if self.auto_fixed else ""
        return f"[{self.severity.upper()}] {self.check_name}: {self.message}{fix}"


def run_all_checks(
    project_root: pathlib.Path,
    pipeline_dir: pathlib.Path,
    active_slug: str = "",
    *,
    ship_prove: bool = False,
) -> list[HealthCheckResult]:
    """Run all deterministic health checks. Returns list of findings.

    Auto-fixes what it can, reports what it can't.
    Call this from the runner's health-check loop (every ~60s).

    When ship_prove=True, skip stray-file rescue from the factory repo root —
    that pattern copies idea impl's own test_*.py into the active workspace.
    """
    results: list[HealthCheckResult] = []

    if not ship_prove:
        results.extend(check_stray_files(project_root, pipeline_dir, active_slug))
    results.extend(prune_workspace_shadow_leaks(pipeline_dir, active_slug))
    results.extend(prune_phantom_tests(pipeline_dir, active_slug))
    results.extend(fix_datetime_utcnow(pipeline_dir, active_slug))
    results.extend(check_workspace_imports(pipeline_dir, active_slug))
    results.extend(check_state_consistency(pipeline_dir, active_slug, ship_prove=ship_prove))
    results.extend(check_workspace_file_paths(pipeline_dir, active_slug))
    results.extend(check_stale_reviews(pipeline_dir))

    # Log findings
    for r in results:
        if r.auto_fixed:
            logger.info("[health] %s", r)
        elif r.severity in ("error", "critical"):
            logger.warning("[health] %s", r)

    return results


def check_stale_reviews(pipeline_dir: pathlib.Path) -> list[HealthCheckResult]:
    """Delete boilerplate review files that cause infinite execute/review loops.

    When the reviewer LLM fails to produce output, the reviewer writes a
    conservative FAIL boilerplate containing 'review file was not generated'.
    This always has 1 blocking bug, which sends the project back to the
    executor, creating an infinite loop. Auto-deleting these lets the next
    review attempt start fresh.
    """
    results: list[HealthCheckResult] = []
    projects_dir = pipeline_dir / "projects"
    if not projects_dir.exists():
        return results

    for review_file in projects_dir.rglob("review.md"):
        try:
            content = review_file.read_text(encoding="utf-8")
            if "review file was not generated" in content:
                review_file.unlink()
                slug = review_file.relative_to(projects_dir).parts[0]
                phase = review_file.parent.name
                results.append(HealthCheckResult(
                    "stale_review", "warning",
                    f"Deleted boilerplate review: {slug}/{phase}/review.md",
                    auto_fixed=True,
                    fix_detail="Reviewer LLM didn't produce output — removed to prevent infinite loop",
                ))
        except Exception:
            pass

    return results



# ---------------------------------------------------------------------------
# Check 1: Stray files outside workspace
# ---------------------------------------------------------------------------

def check_stray_files(
    project_root: pathlib.Path,
    pipeline_dir: pathlib.Path,
    active_slug: str,
) -> list[HealthCheckResult]:
    """Find and rescue files that leaked outside .pipeline/."""
    results: list[HealthCheckResult] = []
    if not active_slug:
        return results

    workspace = pipeline_dir / "projects" / active_slug / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    rescued_total = 0

    # Pattern A: src/, tests/, test/ at project root
    for stray_name in ("src", "tests", "test"):
        stray_dir = project_root / stray_name
        if stray_dir.exists() and stray_dir.is_dir():
            count = rescue_dir_filtered(stray_dir, workspace / stray_name)
            if count:
                rescued_total += count
                results.append(HealthCheckResult(
                    "stray_files", "warning",
                    f"Rescued {count} file(s) from root {stray_name}/",
                    auto_fixed=True,
                    fix_detail=f"Moved to {workspace / stray_name}",
                ))

    # Pattern B: slug-named directory at project root
    slug_at_root = project_root / active_slug
    if slug_at_root.exists() and slug_at_root.is_dir():
        count = rescue_dir_filtered(slug_at_root, workspace)
        if count:
            rescued_total += count
            results.append(HealthCheckResult(
                "stray_files", "warning",
                f"Rescued {count} file(s) from root {active_slug}/",
                auto_fixed=True,
            ))

    # Pattern C: /workspace/workspace/<slug>/
    cloud_stray = pathlib.Path("/workspace/workspace") / active_slug
    if cloud_stray.exists() and cloud_stray.is_dir():
        count = rescue_dir_filtered(cloud_stray, workspace)
        if count:
            rescued_total += count
            results.append(HealthCheckResult(
                "stray_files", "warning",
                f"Rescued {count} file(s) from /workspace/workspace/{active_slug}/",
                auto_fixed=True,
            ))

    # Pattern D: workspace/workspace/ double-nesting (skip infra filenames)
    double_ws = workspace / "workspace"
    if double_ws.exists() and double_ws.is_dir():
        count = rescue_dir_filtered(double_ws, workspace)
        if count:
            rescued_total += count
            results.append(HealthCheckResult(
                "stray_files", "warning",
                f"Rescued {count} file(s) from workspace/workspace/ double-nesting",
                auto_fixed=True,
            ))

    # Pattern E: loose .py files at project root (not infra)
    for f in project_root.glob("*.py"):
        if is_root_infra_file(f.name):
            continue
        dst = workspace / f.name
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(f), str(dst))
            rescued_total += 1
            results.append(HealthCheckResult(
                "stray_files", "warning",
                f"Rescued loose file {f.name} from project root",
                auto_fixed=True,
            ))

    # Pattern F: stray directories at project root that match known patterns
    for d in project_root.iterdir():
        if not d.is_dir():
            continue
        if d.name in _INFRA_DIRS:
            continue
        if d.name.startswith("."):
            continue

        # Pattern F1: build artifacts (.egg-info, .dist-info) — just delete them
        if any(d.name.endswith(pat) for pat in _BUILD_ARTIFACT_PATTERNS):
            try:
                shutil.rmtree(str(d))
                results.append(HealthCheckResult(
                    "build_artifact", "info",
                    f"Removed stray build artifact {d.name}/ from project root",
                    auto_fixed=True,
                ))
            except OSError:
                pass
            continue

        # Pattern F2: check if dir name matches any project slug
        potential_proj = pipeline_dir / "projects" / d.name
        if potential_proj.exists():
            ws = potential_proj / "workspace"
            ws.mkdir(parents=True, exist_ok=True)
            count = rescue_dir_filtered(d, ws)
            if count:
                rescued_total += count
                results.append(HealthCheckResult(
                    "stray_files", "warning",
                    f"Rescued {count} file(s) from root {d.name}/ → {d.name} workspace",
                    auto_fixed=True,
                ))

    return results


def prune_workspace_shadow_leaks(
    pipeline_dir: pathlib.Path,
    active_slug: str,
) -> list[HealthCheckResult]:
    """Remove repo infrastructure files leaked into project workspace/."""
    results: list[HealthCheckResult] = []
    if not active_slug:
        return results

    workspace = pipeline_dir / "projects" / active_slug / "workspace"
    issues = find_workspace_shadows(workspace)
    if not issues:
        return results

    actions = prune_workspace_shadows(workspace)
    if actions:
        summary = "; ".join(actions[:5])
        if len(actions) > 5:
            summary += f" (+{len(actions) - 5} more)"
        results.append(HealthCheckResult(
            "workspace_shadows",
            "warning",
            f"Pruned {len(actions)} path leak(s) in {active_slug}: {summary}",
            auto_fixed=True,
        ))
    return results


def prune_phantom_tests(
    pipeline_dir: pathlib.Path,
    active_slug: str,
) -> list[HealthCheckResult]:
    """Find and delete test files that are outside the tests/ directory."""
    results: list[HealthCheckResult] = []
    if not active_slug:
        return results

    workspace = pipeline_dir / "projects" / active_slug / "workspace"
    if not workspace.exists():
        return results

    tests_dir = workspace / "tests"
    if not tests_dir.exists() or not tests_dir.is_dir():
        return results

    # Find test_*.py files that are not in the tests/ directory
    for f in workspace.rglob("test_*.py"):
        try:
            # Check if tests_dir is a parent
            f.relative_to(tests_dir)
        except ValueError:
            # Not in tests_dir -> phantom test!
            try:
                f.unlink()
                results.append(HealthCheckResult(
                    "phantom_test", "warning",
                    f"Deleted stray test file: {f.relative_to(workspace)}",
                    auto_fixed=True,
                    fix_detail="Removed to prevent cross-contamination during pytest runs",
                ))
            except OSError:
                pass

    return results


def fix_datetime_utcnow(
    pipeline_dir: pathlib.Path,
    active_slug: str,
) -> list[HealthCheckResult]:
    """Replace datetime.utcnow() with datetime.now(timezone.utc) across all python files."""
    results: list[HealthCheckResult] = []
    if not active_slug:
        return results

    workspace = pipeline_dir / "projects" / active_slug / "workspace"
    if not workspace.exists():
        return results

    fixed_count = 0
    for py in workspace.rglob("*.py"):
        try:
            content = py.read_text(encoding="utf-8")
            if "datetime.utcnow()" in content:
                new_content = content.replace("datetime.utcnow()", "datetime.now(timezone.utc)")
                if "from datetime import timezone" not in new_content and "import datetime" not in new_content:
                    # simplistic injection, better than nothing if missing
                    new_content = "from datetime import timezone\n" + new_content
                py.write_text(new_content, encoding="utf-8")
                fixed_count += 1
        except Exception:
            pass

    if fixed_count > 0:
        results.append(HealthCheckResult(
            "datetime_deprecation", "info",
            f"Auto-fixed datetime.utcnow() deprecation warnings in {fixed_count} file(s)",
            auto_fixed=True,
        ))

    return results

# ---------------------------------------------------------------------------
# Check 2: Import resolution
# ---------------------------------------------------------------------------

def check_workspace_imports(
    pipeline_dir: pathlib.Path,
    active_slug: str,
) -> list[HealthCheckResult]:
    """Check if Python files in workspace have resolvable imports."""
    results: list[HealthCheckResult] = []
    if not active_slug:
        return results

    workspace = pipeline_dir / "projects" / active_slug / "workspace"
    if not workspace.exists():
        return results

    import ast

    # Collect all module names available in workspace
    local_modules = set()
    for py in workspace.rglob("*.py"):
        # Module name = relative path without .py, using dots
        try:
            rel = py.relative_to(workspace)
            parts = list(rel.parts)
            if parts[-1] == "__init__.py":
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1].replace(".py", "")
            if parts:
                local_modules.add(parts[0])  # top-level package
        except ValueError:
            pass

    # Standard library modules (common ones — not exhaustive)
    stdlib = {
        "os", "sys", "re", "json", "pathlib", "datetime", "time", "math",
        "typing", "collections", "itertools", "functools", "abc", "enum",
        "dataclasses", "logging", "unittest", "pytest", "argparse",
        "subprocess", "shutil", "io", "csv", "hashlib", "base64",
        "urllib", "http", "email", "html", "xml", "sqlite3", "socket",
        "threading", "multiprocessing", "asyncio", "copy", "pprint",
        "textwrap", "string", "struct", "tempfile", "glob", "fnmatch",
        "configparser", "importlib", "inspect", "traceback", "warnings",
        "contextlib", "decimal", "fractions", "random", "statistics",
        "operator", "secrets", "uuid", "pickle", "shelve", "dbm",
    }

    syntax_errors: list[str] = []
    missing_imports = set()
    for py in workspace.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            rel_path = str(py.relative_to(workspace))
            detail = f"{rel_path}:{e.lineno}: {e.msg}" if e.lineno else f"{rel_path}: {e.msg}"
            syntax_errors.append(detail)
            results.append(HealthCheckResult(
                "syntax_error", "error",
                f"Syntax error in {rel_path}",
                fix_detail=detail,
            ))
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in stdlib and top not in local_modules:
                        missing_imports.add(top)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    if top not in stdlib and top not in local_modules:
                        missing_imports.add(top)

    import importlib.util

    # Try to check if missing imports are pip-installed (find_spec avoids import side effects)
    for mod in sorted(missing_imports):
        if importlib.util.find_spec(mod) is None:
            results.append(HealthCheckResult(
                "missing_import", "warning",
                f"Module '{mod}' imported but not installed or in workspace",
            ))

    # Write syntax errors to pending_fixes.md so the executor can fix them
    pending_fixes_path = workspace.parent / "state" / "pending_fixes.md"
    if syntax_errors:
        pending_fixes_path.parent.mkdir(parents=True, exist_ok=True)
        content = "# Pending Fixes (auto-detected by health check)\n\n"
        content += "These syntax errors must be fixed:\n\n"
        for err in syntax_errors:
            content += f"- `{err}`\n"
        content += "\n<!-- This file is auto-generated. It will be cleared when errors are fixed. -->\n"
        pending_fixes_path.write_text(content, encoding="utf-8")
    elif pending_fixes_path.exists():
        # All syntax errors resolved — clear the file
        pending_fixes_path.unlink(missing_ok=True)

    return results


# ---------------------------------------------------------------------------
# Check 3: State consistency
# ---------------------------------------------------------------------------

def check_state_consistency(
    pipeline_dir: pathlib.Path,
    active_slug: str,
    *,
    ship_prove: bool = False,
) -> list[HealthCheckResult]:
    """Check for inconsistencies between state files and actual state."""
    results: list[HealthCheckResult] = []
    if not active_slug:
        return results

    state_file = pipeline_dir / "projects" / active_slug / "state" / "current_idea.json"
    if not state_file.exists():
        return results

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        results.append(HealthCheckResult(
            "state_corrupt", "critical",
            f"Cannot parse current_idea.json for {active_slug}",
        ))
        return results

    status = state.get("status", "")
    phase = state.get("phase", 1)

    # Ship-prove owns its own status track — never auto-reset to phase_X_*.
    if ship_prove:
        try:
            from pipeline.ship_status import is_ship_status
            if is_ship_status(status):
                return results
        except Exception:
            pass
        # Even if status briefly looks like phase_X_executing during ship work,
        # do not rewrite it back onto the main pipeline track.
        return results

    # Check A: status says "executing" but tasks.md doesn't exist
    if "executing" in status:
        tasks_file = pipeline_dir / "projects" / active_slug / f"phases/phase_{phase}/tasks.md"
        if not tasks_file.exists():
            results.append(HealthCheckResult(
                "missing_tasks", "error",
                f"Status is {status} but tasks.md missing for phase {phase}",
            ))
            # Auto-fix: re-route to phase_planner
            state["status"] = f"phase_{phase}_planning"
            state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            results.append(HealthCheckResult(
                "missing_tasks", "warning",
                f"Auto-reset to phase_{phase}_planning to regenerate tasks",
                auto_fixed=True,
            ))

    # Check B: status says "reviewed" but review_result is missing
    if "reviewed" in status and "review_result" not in state:
        results.append(HealthCheckResult(
            "missing_review", "error",
            f"Status is {status} but review_result missing — resetting to executing",
        ))
        state["status"] = f"phase_{phase}_executing"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        results[-1].auto_fixed = True

    # Check C: session_started_at is way in the past (orphaned)
    started = state.get("session_started_at", "")
    if started:
        try:
            start_dt = datetime.fromisoformat(started)
            elapsed_hrs = (datetime.now(timezone.utc) - start_dt).total_seconds() / 3600
            if elapsed_hrs > 24 and status not in ("complete", "budget_exceeded", "dep_waiting"):
                results.append(HealthCheckResult(
                    "stale_session", "warning",
                    f"Session started {elapsed_hrs:.0f}h ago — may be orphaned from previous run",
                ))
        except Exception:
            pass

    return results


# ---------------------------------------------------------------------------
# Check 4: Workspace file path validation
# ---------------------------------------------------------------------------

def check_workspace_file_paths(
    pipeline_dir: pathlib.Path,
    active_slug: str,
) -> list[HealthCheckResult]:
    """Verify all referenced files in tasks.md actually exist in workspace."""
    results: list[HealthCheckResult] = []
    if not active_slug:
        return results

    workspace = pipeline_dir / "projects" / active_slug / "workspace"
    if not workspace.exists():
        return results

    # Count files in workspace
    py_files = list(workspace.rglob("*.py"))
    if not py_files:
        results.append(HealthCheckResult(
            "empty_workspace", "warning",
            f"Workspace for {active_slug} has no .py files",
        ))

    # Check for __init__.py in directories that have .py files
    # (common missing file that breaks imports)
    pkg_dirs = set()
    for py in py_files:
        parent = py.parent
        if parent != workspace:
            pkg_dirs.add(parent)

    for pkg_dir in pkg_dirs:
        init_file = pkg_dir / "__init__.py"
        if not init_file.exists():
            # Check if there are actual .py files (not just subdirs)
            has_py = any(f.suffix == ".py" for f in pkg_dir.iterdir() if f.is_file())
            if has_py:
                # Auto-create empty __init__.py
                init_file.write_text("", encoding="utf-8")
                results.append(HealthCheckResult(
                    "missing_init", "info",
                    f"Created missing __init__.py in {pkg_dir.relative_to(workspace)}",
                    auto_fixed=True,
                ))

    return results


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _rescue_dir(src_dir: pathlib.Path, dest_base: pathlib.Path) -> int:
    """Backward-compatible alias — skips infra/shadow filenames."""
    return rescue_dir_filtered(src_dir, dest_base)


def write_health_report(
    results: list[HealthCheckResult],
    pipeline_dir: pathlib.Path,
) -> None:
    """Append health check findings to a persistent log file."""
    if not results:
        return

    log_path = pipeline_dir / "state" / "health_log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"\n## {ts}\n"
    for r in results:
        fix_tag = " ✅" if r.auto_fixed else ""
        entry += f"- [{r.severity.upper()}] {r.check_name}: {r.message}{fix_tag}\n"
        if r.fix_detail:
            entry += f"  - Fix: {r.fix_detail}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
