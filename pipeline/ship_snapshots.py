"""Workspace snapshot helpers for thermo-nuclear review pairs."""

from __future__ import annotations

import shutil
from pathlib import Path


def snapshot_workspace(workspace: Path, dest: Path) -> int:
    """Copy workspace tree to dest; return file count."""
    if dest.exists():
        shutil.rmtree(dest)
    if not workspace.is_dir():
        return 0
    shutil.copytree(
        workspace,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
    )
    return sum(1 for f in dest.rglob("*") if f.is_file())
