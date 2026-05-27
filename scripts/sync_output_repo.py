#!/usr/bin/env python3
"""
Commit and optionally push the pipeline *output* repo (PIPELINE_DIR).

Use after runs so GitHub avatardebris-debug/pipeline stays in sync with local work:
  projects/, finetune_corpus/, state/, shared_libs/, master_ideas.md, etc.

Usage:
  python scripts/sync_output_repo.py
  python scripts/sync_output_repo.py --message "corpus: advantage_player p1-p3"
  python scripts/sync_output_repo.py --push
  python scripts/sync_output_repo.py --dry-run

Requires PIPELINE_DIR (or auto-detect via pipeline.pipeline_config).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.output_bootstrap import ensure_pipeline_ready
from pipeline.pipeline_config import get_pipeline_dir  # noqa: E402


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync pipeline output repo to git")
    parser.add_argument("--message", "-m", default="pipeline: sync output")
    parser.add_argument("--push", action="store_true", help="git push after commit")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_pipeline_ready(hermes=False)
    out_dir = get_pipeline_dir()
    if not out_dir.is_dir():
        print(f"ERROR: PIPELINE_DIR not found: {out_dir}")
        return 1

    git_dir = out_dir / ".git"
    if not git_dir.is_dir():
        print(f"ERROR: {out_dir} is not a git repo (no .git). Clone pipeline output repo there.")
        print("  git clone https://github.com/avatardebris-debug/pipeline.git thepipeline")
        return 1

    status = _git("status", "--porcelain", cwd=out_dir)
    if status.returncode != 0:
        print(status.stderr or status.stdout)
        return 1

    if not status.stdout.strip():
        print(f"No changes in {out_dir}")
        return 0

    print(f"Changes in {out_dir}:\n{status.stdout}")

    if args.dry_run:
        return 0

    add = _git("add", "-A", cwd=out_dir)
    if add.returncode != 0:
        print(add.stderr or add.stdout)
        return 1

    commit = _git("commit", "-m", args.message, cwd=out_dir)
    if commit.returncode != 0:
        if "nothing to commit" in (commit.stdout or "") + (commit.stderr or ""):
            print("Nothing to commit.")
            return 0
        print(commit.stderr or commit.stdout)
        return 1

    print(commit.stdout or "Committed.")

    rev = _git("rev-parse", "--short", "HEAD", cwd=out_dir)
    if rev.returncode == 0:
        print(f"HEAD {rev.stdout.strip()}")

    if args.push:
        push = _git("push", cwd=out_dir)
        if push.returncode != 0:
            print(push.stderr or push.stdout)
            return 1
        print("Pushed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
