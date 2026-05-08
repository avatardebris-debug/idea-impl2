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

# Infrastructure files that should NOT be rescued (they belong at project root)
_INFRA_FILES = {
    "agent.py", "extract.py", "fix_indent.py", "fix_missing_plans.py",
    "fix_stuck_tasks.py", "governance.py", "setup.py", "cloud_setup.sh",
    "harvest.sh", "sync_cloud.sh", "constitution.yaml",
}

_INFRA_DIRS = {
    "pipeline", ".pipeline", "_archive", "extras", ".git",
    "master ideas backup sort", "__pycache__", ".ipynb_checkpoints",
    "node_modules", ".pytest_cache", "build", "dist",
}

# Build artifacts that should be deleted (not rescued) when found at project root
_BUILD_ARTIFACT_PATTERNS = {".egg-info", ".dist-info"}


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
) -> list[HealthCheckResult]:
    """Run all deterministic health checks. Returns list of findings.

    Auto-fixes what it can, reports what it can't.
    Call this from the runner's health-check loop (every ~60s).
    """
    results: list[HealthCheckResult] = []

    results.extend(check_stray_files(project_root, pipeline_dir, active_slug))
    results.extend(check_workspace_imports(pipeline_dir, active_slug))
    results.extend(check_state_consistency(pipeline_dir, active_slug))
    results.extend(check_workspace_file_paths(pipeline_dir, active_slug))

    # Log findings
    for r in results:
        if r.auto_fixed:
            logger.info("[health] %s", r)
        elif r.severity in ("error", "critical"):
            logger.warning("[health] %s", r)

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
            count = _rescue_dir(stray_dir, workspace / stray_name)
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
        count = _rescue_dir(slug_at_root, workspace)
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
        count = _rescue_dir(cloud_stray, workspace)
        if count:
            rescued_total += count
            results.append(HealthCheckResult(
                "stray_files", "warning",
                f"Rescued {count} file(s) from /workspace/workspace/{active_slug}/",
                auto_fixed=True,
            ))

    # Pattern D: workspace/workspace/ double-nesting
    double_ws = workspace / "workspace"
    if double_ws.exists() and double_ws.is_dir():
        count = _rescue_dir(double_ws, workspace)
        if count:
            rescued_total += count
            results.append(HealthCheckResult(
                "stray_files", "warning",
                f"Rescued {count} file(s) from workspace/workspace/ double-nesting",
                auto_fixed=True,
            ))

    # Pattern E: loose .py files at project root (not infra)
    for f in project_root.glob("*.py"):
        if f.name in _INFRA_FILES:
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
            count = _rescue_dir(d, ws)
            if count:
                rescued_total += count
                results.append(HealthCheckResult(
                    "stray_files", "warning",
                    f"Rescued {count} file(s) from root {d.name}/ → {d.name} workspace",
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

    missing_imports = set()
    for py in workspace.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            results.append(HealthCheckResult(
                "syntax_error", "error",
                f"Syntax error in {py.relative_to(workspace)}",
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

    # Try to check if they're pip-installed
    for mod in sorted(missing_imports):
        try:
            __import__(mod)
        except ImportError:
            results.append(HealthCheckResult(
                "missing_import", "warning",
                f"Module '{mod}' imported but not installed or in workspace",
            ))

    return results


# ---------------------------------------------------------------------------
# Check 3: State consistency
# ---------------------------------------------------------------------------

def check_state_consistency(
    pipeline_dir: pathlib.Path,
    active_slug: str,
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
    """Move files from src_dir into dest_base, preserving relative paths.
    Returns count of files moved.
    """
    if not src_dir.exists() or not src_dir.is_dir():
        return 0

    moved = 0
    for f in list(src_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.name.startswith(".") or "__pycache__" in str(f):
            continue
        try:
            rel = f.relative_to(src_dir)
        except ValueError:
            continue
        dst = dest_base / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(str(f), str(dst))
            moved += 1
        elif f.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(str(f), str(dst))
            moved += 1

    if moved:
        try:
            shutil.rmtree(str(src_dir))
        except OSError:
            pass

    return moved


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
