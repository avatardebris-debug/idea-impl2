"""
pipeline/output_bootstrap.py
Bootstrap pipeline output directory on cloud (clone/pull avatardebris-debug/pipeline).

Local dev: use ../thepipeline or PIPELINE_DIR env — no clone.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PIPELINE_REPO_URL = os.environ.get(
    "PIPELINE_REPO_URL",
    "https://github.com/avatardebris-debug/pipeline.git",
)
PIPELINE_REPO_BRANCH = os.environ.get("PIPELINE_REPO_BRANCH", "main")
PIPELINE_MINIMAL = os.environ.get("PIPELINE_MINIMAL", "").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)


def is_cloud_environment() -> bool:
    if os.environ.get("PIPELINE_CLOUD", "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    if Path("/workspace").is_dir():
        return True
    sibling = PROJECT_ROOT.parent / "thepipeline"
    if sibling.is_dir() and (sibling / "projects").is_dir():
        return False
    nested = PROJECT_ROOT / ".pipeline"
    if nested.is_dir() and (nested / "projects").is_dir():
        return False
    return not sibling.is_dir()


def cloud_output_dir() -> Path:
    return (PROJECT_ROOT / ".pipeline").resolve()


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _sparse_checkout_minimal(target: Path) -> None:
    """Shallow clone with sparse checkout for projects/state/finetune only."""
    if target.exists() and (target / ".git").is_dir():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    _git("clone", "--depth", "1", "--filter=blob:none", "--sparse", PIPELINE_REPO_URL, str(target))
    _git("sparse-checkout", "set", "projects", "state", "finetune_corpus", "master_ideas.md", "workflows", cwd=target)
    _git("checkout", PIPELINE_REPO_BRANCH, cwd=target)


def bootstrap_output_repo(*, force: bool = False) -> Path:
    """
    Ensure PROJECT_ROOT/.pipeline exists and is populated on cloud.
    Returns the output directory path.
    """
    if not is_cloud_environment() and not force:
        return cloud_output_dir()

    target = cloud_output_dir()
    os.environ["PIPELINE_DIR"] = str(target)

    if PIPELINE_MINIMAL and not (target / ".git").is_dir():
        print(f"  [bootstrap] Minimal sparse clone → {target}")
        _sparse_checkout_minimal(target)
        (target / "projects").mkdir(parents=True, exist_ok=True)
        (target / "state").mkdir(parents=True, exist_ok=True)
        (target / "finetune_corpus" / "raw" / "task").mkdir(parents=True, exist_ok=True)
        return target

    if (target / ".git").is_dir():
        print(f"  [bootstrap] git pull → {target}")
        pull = _git("pull", "--ff-only", "origin", PIPELINE_REPO_BRANCH, cwd=target)
        if pull.returncode != 0:
            print(f"  [bootstrap] pull warning: {(pull.stderr or pull.stdout)[:300]}")
        return target

    if target.exists() and any(target.iterdir()) and not (target / ".git").is_dir():
        print(f"  [bootstrap] Using existing {target} (not a git repo)")
        return target

    print(f"  [bootstrap] git clone {PIPELINE_REPO_URL} → {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    clone = _git(
        "clone",
        "--depth",
        "1",
        "-b",
        PIPELINE_REPO_BRANCH,
        PIPELINE_REPO_URL,
        str(target),
    )
    if clone.returncode != 0:
        print(f"  [bootstrap] clone failed: {clone.stderr or clone.stdout}")
        target.mkdir(parents=True, exist_ok=True)
        (target / "projects").mkdir(exist_ok=True)
    return target


def bootstrap_hermes() -> bool:
    """Clone hermes-agent if missing (delegates to hermes_runner)."""
    try:
        from pipeline.hermes_runner import ensure_hermes_available

        ensure_hermes_available()
        return True
    except Exception as exc:
        print(f"  [bootstrap] Hermes skipped: {exc}")
        return False
