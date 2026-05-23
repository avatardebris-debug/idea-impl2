#!/usr/bin/env python3
"""Comprehensive pytest sweep of pipeline project workspaces."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Resolve repo root (works on Windows, Linux, Vast /workspace/idea impl, etc.)
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from pipeline.pipeline_config import PIPELINE_DIR, PROJECT_ROOT  # noqa: E402

PROJECTS_DIR = PIPELINE_DIR / "projects"
DEFAULT_RESULTS = REPO_ROOT / "sweep_results.json"


def discover_project_slugs() -> list[str]:
    """All slugs under .pipeline/projects/ that have a workspace/ dir."""
    if not PROJECTS_DIR.is_dir():
        return []
    out: list[str] = []
    for d in sorted(PROJECTS_DIR.iterdir()):
        if d.is_dir() and (d / "workspace").is_dir():
            out.append(d.name)
    return out


def sweep_all(
    pipeline_dir: str | Path | None = None,
    results_path: str | Path | None = None,
    *,
    project_slugs: list[str] | None = None,
    timeout_s: int = 60,
) -> dict[str, dict]:
    """
    Run pytest in each project's workspace/tests.

    pipeline_dir: defaults to .pipeline under PROJECT_ROOT
    results_path: write JSON summary here
    project_slugs: optional subset; default = all with workspace/
    """
    _ = pipeline_dir  # reserved; PROJECTS_DIR is canonical
    slugs = project_slugs or discover_project_slugs()
    results: dict[str, dict] = {}

    for proj in slugs:
        ws = PROJECTS_DIR / proj / "workspace"
        if not ws.is_dir():
            results[proj] = {"status": "NOT_FOUND", "detail": "workspace dir missing"}
            continue

        tests_dir = ws / "tests"
        if not tests_dir.is_dir():
            results[proj] = {"status": "NO_TESTS_DIR", "detail": "no tests/ directory"}
            continue

        print(f"Running: {proj}...", end=" ", flush=True)
        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "--no-header"],
                cwd=str(ws),
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            elapsed = time.time() - start
            lines = [ln for ln in result.stdout.strip().split("\n") if ln.strip()]
            summary_line = lines[-1] if lines else "no output"
            results[proj] = {
                "status": "COMPLETED",
                "exit_code": result.returncode,
                "summary": summary_line,
                "elapsed": round(elapsed, 1),
                "full_stdout_tail": "\n".join(lines[-5:]) if lines else "",
                "stderr_tail": "\n".join(result.stderr.strip().split("\n")[-3:])
                if result.stderr.strip()
                else "",
            }
            print(f"done ({elapsed:.1f}s) exit={result.returncode} => {summary_line}")
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            results[proj] = {
                "status": "TIMEOUT",
                "elapsed": round(elapsed, 1),
                "detail": f"timed out after {timeout_s}s",
            }
            print(f"TIMEOUT ({elapsed:.1f}s)")

    out_path = Path(results_path) if results_path else DEFAULT_RESULTS
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def print_summary_table(results: dict[str, dict]) -> None:
    print("\n" + "=" * 80)
    print(f"{'Project':<45} {'Status':<12} {'Result'}")
    print("=" * 80)
    for proj, data in results.items():
        status = data["status"]
        if status == "COMPLETED":
            label = "OK" if data["exit_code"] == 0 else "FAIL"
            print(f"{proj:<45} {label:<12} {data['summary']}")
        elif status == "TIMEOUT":
            print(f"{proj:<45} {'TIMEOUT':<12} hung after timeout")
        elif status == "NO_TESTS_DIR":
            print(f"{proj:<45} {'SKIP':<12} no tests/ directory")
        else:
            print(f"{proj:<45} {status:<12} {data.get('detail', '')}")
    print(f"\nProjects dir: {PROJECTS_DIR}")
    print(f"Repo root:    {PROJECT_ROOT}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Sweep pytest across pipeline workspaces")
    parser.add_argument(
        "--results",
        default=str(DEFAULT_RESULTS),
        help="Output JSON path (default: sweep_results.json in repo root)",
    )
    args = parser.parse_args()
    results = sweep_all(results_path=args.results)
    print_summary_table(results)


if __name__ == "__main__":
    main()
