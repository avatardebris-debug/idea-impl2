"""
pipeline/path_health.py
Shared detection and cleanup for workspace path leaks (repo infra copied into projects).
"""

from __future__ import annotations

import pathlib
import shutil
from typing import Iterable

# Loose .py at repo root — never copy into project workspace
ROOT_INFRA_FILES: frozenset[str] = frozenset({
    "agent.py",
    "extract.py",
    "fix_indent.py",
    "fix_missing_plans.py",
    "fix_stuck_tasks.py",
    "governance.py",
    "setup.py",
    "cloud_setup.sh",
    "harvest.sh",
    "sync_cloud.sh",
    "health_check.py",
    "import_cloud_zip.py",
    "import_zip.py",
    "install_all.py",
    "llm_interface.py",
    "quality_scorer.py",
    "reset_budget_exceeded.py",
    "sweep_all.py",
    "test_all.py",
    "test_dependency_system.py",
    "test_harness_capabilities.py",
    "test_priority_eviction_unit.py",
    "tools.py",
})

ROOT_INFRA_DIRS: frozenset[str] = frozenset({
    "pipeline",
    ".pipeline",
    "_archive",
    "extras",
    ".git",
    "master ideas backup sort",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "hermes-agent-main",
    "build",
    "dist",
})

# Files that must not live under .pipeline/projects/<slug>/workspace/
WORKSPACE_SHADOW_FILES: frozenset[str] = frozenset({
    "import_zip.py",
    "import_cloud_zip.py",
    "extract.py",
    "health_check.py",
    "agent.py",
    "install_all.py",
    "llm_interface.py",
    "quality_scorer.py",
    "reset_budget_exceeded.py",
    "sweep_all.py",
    "tools.py",
    "test_all.py",
    "test_dependency_system.py",
    "test_harness_capabilities.py",
    "test_priority_eviction_unit.py",
    "governance.py",
    "fix_indent.py",
    "fix_missing_plans.py",
    "fix_stuck_tasks.py",
    "setup.py",
    "review.md",  # phase review leaked to workspace root
})

WORKSPACE_SHADOW_DIR_NAMES: frozenset[str] = frozenset({
    "pipeline",
    ".pipeline",
    ".git",
    "node_modules",
    ".venv",
    "venv",
})

# Removed silently during prune (not reported as actionable leaks)
WORKSPACE_CACHE_DIR_NAMES: frozenset[str] = frozenset({
    "__pycache__",
    ".pytest_cache",
})

BUILD_ARTIFACT_SUFFIXES: tuple[str, ...] = (".egg-info", ".dist-info")


def is_root_infra_file(name: str) -> bool:
    return name in ROOT_INFRA_FILES


def is_workspace_shadow_file(name: str) -> bool:
    return name in WORKSPACE_SHADOW_FILES


def is_workspace_shadow_dir(name: str) -> bool:
    return name in WORKSPACE_SHADOW_DIR_NAMES


def should_skip_zip_workspace_path(zip_entry: str) -> bool:
    """True if a zip path under workspace/ should not be imported."""
    parts = pathlib.PurePosixPath(zip_entry).parts
    if "workspace" not in parts:
        return False
    base = parts[-1]
    if base in WORKSPACE_SHADOW_FILES:
        return True
    if base in WORKSPACE_SHADOW_DIR_NAMES:
        return True
    return False


def rescue_dir_filtered(
    src_dir: pathlib.Path,
    dest_base: pathlib.Path,
    *,
    skip_shadow_files: bool = True,
) -> int:
    """Copy files from src_dir into dest_base, skipping infra/shadow filenames."""
    return len(
        rescue_dir_filtered_moves(
            src_dir, dest_base, skip_shadow_files=skip_shadow_files
        )
    )


def rescue_dir_filtered_moves(
    src_dir: pathlib.Path,
    dest_base: pathlib.Path,
    *,
    skip_shadow_files: bool = True,
    label: str = "",
) -> list[dict[str, str]]:
    """
    Copy files from src_dir into dest_base.

    Returns list of {src, dest, label} for each file copied (for executor hints).
    """
    if not src_dir.is_dir():
        return []

    moves: list[dict[str, str]] = []
    for f in list(src_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.name.startswith(".") or "__pycache__" in str(f):
            continue
        if skip_shadow_files and is_workspace_shadow_file(f.name):
            continue
        try:
            rel = f.relative_to(src_dir)
        except ValueError:
            continue
        dst = dest_base / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        copied = False
        if not dst.exists():
            shutil.copy2(str(f), str(dst))
            copied = True
        elif f.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(str(f), str(dst))
            copied = True
        if copied:
            moves.append(
                {
                    "src": str(f),
                    "dest": str(dst),
                    "rel": rel.as_posix(),
                    "label": label or "rescue",
                }
            )

    if moves:
        try:
            shutil.rmtree(str(src_dir))
        except OSError:
            pass

    return moves


def prune_workspace_shadows(workspace: pathlib.Path) -> list[str]:
    """
    Remove leaked infra from a project workspace.
    Returns human-readable action strings for logging.
    """
    actions: list[str] = []
    if not workspace.is_dir():
        return actions

    # Nested workspace/workspace/ — merge real files, drop shadows
    nested = workspace / "workspace"
    if nested.is_dir():
        n = rescue_dir_filtered(nested, workspace)
        if n:
            actions.append(f"merged {n} file(s) from workspace/workspace/")
        try:
            shutil.rmtree(str(nested))
            actions.append("removed workspace/workspace/")
        except OSError:
            pass

    # Shadow / cache directories at workspace root
    for child in list(workspace.iterdir()):
        if not child.is_dir():
            continue
        if child.name in WORKSPACE_CACHE_DIR_NAMES or is_workspace_shadow_dir(child.name):
            try:
                shutil.rmtree(str(child))
                actions.append(f"removed workspace/{child.name}/")
            except OSError:
                pass
        elif any(child.name.endswith(suf) for suf in BUILD_ARTIFACT_SUFFIXES):
            try:
                shutil.rmtree(str(child))
                actions.append(f"removed build artifact workspace/{child.name}/")
            except OSError:
                pass

    # Shadow files anywhere under workspace (usually at root)
    for f in list(workspace.rglob("*")):
        if not f.is_file():
            continue
        if not is_workspace_shadow_file(f.name):
            continue
        try:
            rel = f.relative_to(workspace)
            f.unlink()
            actions.append(f"deleted workspace/{rel.as_posix()}")
        except OSError:
            pass

    return actions


def find_workspace_shadows(workspace: pathlib.Path) -> list[str]:
    """Return descriptions of shadow leaks (for reporting)."""
    issues: list[str] = []
    if not workspace.is_dir():
        return issues

    if (workspace / "workspace").is_dir():
        issues.append("nested workspace/workspace/ directory")

    for name in WORKSPACE_SHADOW_DIR_NAMES:
        if (workspace / name).is_dir():
            issues.append(f"shadow directory workspace/{name}/")
    # Do not report __pycache__ / .pytest_cache — pruned silently

    for f in workspace.rglob("*"):
        if f.is_file() and is_workspace_shadow_file(f.name):
            try:
                rel = f.relative_to(workspace)
                issues.append(f"shadow file workspace/{rel.as_posix()}")
            except ValueError:
                issues.append(f"shadow file {f.name}")

    return issues
