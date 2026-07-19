#!/usr/bin/env python3
"""
Publish a pipeline project folder as a git repo (whole projects/<slug>/).

By default: local git commit only.
With --push or PIPELINE_GITHUB_PUBLISH=1: create/push GitHub repo (needs org + auth).

Usage:
  python scripts/publish_project_github.py --slug ship_canary
  python scripts/publish_project_github.py --slug ship_canary --push
  python scripts/publish_project_github.py --all-eligible
  python scripts/publish_project_github.py --all-eligible --push

Env:
  PIPELINE_GITHUB_PUBLISH=1
  PIPELINE_GITHUB_ORG=your-org
  PIPELINE_GITHUB_REPO_PREFIX=pipe-
  PIPELINE_GITHUB_VISIBILITY=private
  PIPELINE_GITHUB_ON=complete,field_proven
  GITHUB_TOKEN or gh auth login
  GIT_COMMIT_AUTHOR="Name <email>"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE from factory .env into os.environ (no overwrite of set vars)."""
    if not path.is_file():
        return
    import os

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_dotenv(ROOT / ".env")

from pipeline.github_publish import (  # noqa: E402
    list_eligible_slugs,
    publish_enabled,
    publish_project,
    publish_triggers,
)
from pipeline.output_bootstrap import ensure_pipeline_ready  # noqa: E402
from pipeline.paths import project_dir  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish pipeline project to git/GitHub")
    parser.add_argument("--slug", default="", help="Project slug under projects/")
    parser.add_argument(
        "--all-eligible",
        action="store_true",
        help="Publish all projects with status in PIPELINE_GITHUB_ON",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push to GitHub (overrides off env for this run)",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Never push (local commit only)",
    )
    parser.add_argument(
        "--trigger",
        default="manual",
        help="Label stored in commit message / status (default: manual)",
    )
    args = parser.parse_args()

    ensure_pipeline_ready(hermes=False)

    if args.local_only and args.push:
        print("ERROR: use only one of --push / --local-only")
        return 1

    force_push: bool | None
    if args.local_only:
        force_push = False
    elif args.push:
        force_push = True
    else:
        force_push = None  # follow env

    slugs: list[str] = []
    if args.all_eligible:
        slugs = list_eligible_slugs()
        if not slugs:
            print(f"No eligible projects (triggers={sorted(publish_triggers())})")
            return 0
    elif args.slug:
        slugs = [args.slug.strip()]
    else:
        print("Provide --slug SLUG or --all-eligible")
        return 1

    print(
        f"Publish mode: push={'on' if (force_push if force_push is not None else publish_enabled()) else 'off (local only)'}"
    )
    rc = 0
    for slug in slugs:
        p = project_dir(slug)
        if not p.is_dir():
            print(f"  ✗ missing project dir: {p}")
            rc = 1
            continue
        result = publish_project(
            slug, trigger=args.trigger, force_push=force_push
        )
        if result.ok:
            extra = result.url or ("local " + (result.sha[:8] if result.sha else ""))
            print(f"  ✓ {slug}: {result.message or 'ok'} ({extra})")
        else:
            print(f"  ✗ {slug}: {result.error or result.message}")
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
