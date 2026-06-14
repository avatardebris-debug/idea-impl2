#!/usr/bin/env python3
"""
Repo-wide regression audit for idea impl (post thermo-nuclear refactors).

  python scripts/idea_impl_audit.py
  python scripts/idea_impl_audit.py --smoke-imports
"""

from __future__ import annotations

import argparse
import compileall
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_HARDCODED = re.compile(
    r'(?:pathlib\.Path\(|["\'])(?:\.pipeline/|\.pipeline["\'])',
)


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def audit_compile() -> bool:
    _section("Compile pipeline/ + core modules")
    ok = compileall.compile_dir(ROOT / "pipeline", quiet=1)
    for rel in ("agent.py", "llm_interface.py", "tools.py", "governance.py"):
        ok = compileall.compile_file(ROOT / rel, quiet=1) and ok
    print("compileall:", "OK" if ok else "FAIL")
    return bool(ok)


def audit_hardcoded_paths() -> list[str]:
    _section("Hardcoded .pipeline paths (should use pipeline.paths)")
    hits: list[str] = []
    for path in ROOT.rglob("*.py"):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(ROOT)
        if str(rel).startswith("_archive"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if _HARDCODED.search(line) and "get_pipeline_dir" not in line:
                hits.append(f"{rel}:{i}: {line.strip()[:90]}")
    if hits:
        for h in hits[:30]:
            print(f"  {h}")
        if len(hits) > 30:
            print(f"  ... and {len(hits) - 30} more")
    else:
        print("  (none found)")
    return hits


def audit_path_resolution() -> None:
    _section("Path resolution")
    from pipeline.pipeline_config import get_pipeline_dir, PROJECT_ROOT

    print(f"  PROJECT_ROOT={PROJECT_ROOT}")
    print(f"  get_pipeline_dir()={get_pipeline_dir()}")


def smoke_imports() -> bool:
    _section("Smoke imports")
    modules = [
        "pipeline.runner",
        "pipeline.message_bus",
        "pipeline.seeding",
        "pipeline.project_rebuild",
        "pipeline.startup",
        "pipeline.agents.reviewer",
        "pipeline.agents.phase_planner",
        "pipeline.agents.manager",
        "llm_interface",
        "agent",
    ]
    ok = True
    for mod in modules:
        try:
            __import__(mod)
            print(f"  OK {mod}")
        except Exception as e:
            print(f"  FAIL {mod}: {e}")
            ok = False
    return ok


def audit_seeding_behavior() -> None:
    _section("master_ideas.md seeding (first unchecked wins serially)")
    mi = ROOT / "master_ideas.md"
    if not mi.exists():
        print("  master_ideas.md missing")
        return
    for line in mi.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("[ ]") or s.startswith("- [ ]"):
            print(f"  FIRST unchecked line (blocks all below until complete):")
            print(f"    {s[:120]}")
            break


def main() -> int:
    parser = argparse.ArgumentParser(description="idea impl regression audit")
    parser.add_argument("--smoke-imports", action="store_true")
    args = parser.parse_args()

    ok = audit_compile()
    hits = audit_hardcoded_paths()
    audit_path_resolution()
    audit_seeding_behavior()
    if args.smoke_imports:
        ok = smoke_imports() and ok

    _section("Summary")
    if hits:
        print(f"  WARN {len(hits)} hardcoded .pipeline reference(s)")
    if not ok:
        print("  FAIL compile or imports")
        return 1
    print("  Audit complete — run pipeline smoke test separately")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
