#!/usr/bin/env python3
"""
health_check.py — Tier 2 cross-project health checker.

Unlike pipeline/health_checks.py (which runs on the active project during the
runner loop), this tool scans ALL projects at rest and catches systemic bugs:

  1. Stale status  — status says phase_1_executing but phase > 1
  2. Phantom phases — total_phases doesn't match master_plan.md
  3. Shadow leaks   — repo infra copied into workspace/ (import_zip, pipeline/, etc.)
  3b. Nested workspace — workspace/workspace/ double-nesting
  4. Orphan tests   — tests/__init__.py with broken relative imports
  5. Enum drift     — source files referencing missing enum members
  6. Validation gap — all phases PASS but status ≠ complete
  7. Duplicate slugs— two projects with identical titles

Run:
    python health_check.py              # report only
    python health_check.py --fix        # auto-fix what's safe
    python health_check.py --json       # machine-readable output
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

PIPELINE = pathlib.Path(__file__).parent / ".pipeline"
PROJECTS = PIPELINE / "projects"
REPO_ROOT = pathlib.Path(__file__).parent

# Shared with pipeline/health_checks.py and executor rescue logic
sys.path.insert(0, str(REPO_ROOT))
from pipeline.path_health import (  # noqa: E402
    find_workspace_shadows,
    prune_workspace_shadows,
    rescue_dir_filtered,
)


# ── Result container ─────────────────────────────────────────────────

class Finding:
    def __init__(self, slug: str, check: str, severity: str,
                 message: str, fixable: bool = False, fix_detail: str = ""):
        self.slug = slug
        self.check = check
        self.severity = severity
        self.message = message
        self.fixable = fixable
        self.fix_detail = fix_detail
        self.fixed = False

    def __repr__(self):
        tag = " [FIXED]" if self.fixed else (" [FIXABLE]" if self.fixable else "")
        return f"[{self.severity}] {self.slug}: {self.check} — {self.message}{tag}"

    def to_dict(self):
        return {
            "slug": self.slug, "check": self.check, "severity": self.severity,
            "message": self.message, "fixable": self.fixable,
            "fixed": self.fixed, "fix_detail": self.fix_detail,
        }


# ── Individual checks ────────────────────────────────────────────────

def check_stale_status(slug: str, state: dict, phases_dir: pathlib.Path) -> list[Finding]:
    """Status field stuck at phase_1_* while phase counter is higher."""
    findings = []
    status = state.get("status", "")
    phase = state.get("phase", 1)

    if status == "complete" or status == "budget_exceeded":
        return findings

    # Extract phase number from status string
    m = re.match(r"phase_(\d+)_", status)
    if m:
        status_phase = int(m.group(1))
        if phase > status_phase:
            findings.append(Finding(
                slug, "stale_status", "error",
                f"Status says phase_{status_phase}_* but phase counter is {phase}",
                fixable=True,
                fix_detail=f"Would update status to match phase {phase}",
            ))
    return findings


def check_phantom_phases(slug: str, state: dict, plan_path: pathlib.Path) -> list[Finding]:
    """total_phases in state doesn't match the master_plan.md count."""
    findings = []
    total = state.get("total_phases", 0)
    if not plan_path.exists() or not total:
        return findings

    text = plan_path.read_text(encoding="utf-8", errors="ignore")
    # Count "## Phase N" headings
    plan_phases = len(re.findall(r"^##\s+Phase\s+\d+", text, re.MULTILINE))
    if plan_phases and total != plan_phases and plan_phases >= 2:
        findings.append(Finding(
            slug, "phantom_phases", "warning",
            f"State says {total} phases but master_plan.md defines {plan_phases}",
            fixable=True,
            fix_detail=f"Would update total_phases to {plan_phases}",
        ))
    return findings


def check_shadow_dirs(slug: str, workspace: pathlib.Path) -> list[Finding]:
    """Repo infrastructure leaked into project workspace."""
    findings = []
    for issue in find_workspace_shadows(workspace):
        sev = "critical" if "pipeline/" in issue or "workspace/workspace" in issue else "warning"
        findings.append(Finding(
            slug, "shadow_leak", sev,
            issue,
            fixable=True,
            fix_detail="Would prune shadow files/dirs via path_health",
        ))
    return findings


def check_slug_dir_at_workspace_root(slug: str, workspace: pathlib.Path) -> list[Finding]:
    """workspace/<slug>/ when slug matches project — merge into workspace root."""
    findings = []
    nested_slug = workspace / slug
    if nested_slug.is_dir():
        py_count = sum(1 for _ in nested_slug.rglob("*.py") if _.is_file())
        findings.append(Finding(
            slug, "nested_slug_dir", "warning",
            f"Redundant workspace/{slug}/ directory ({py_count} .py files)",
            fixable=True,
            fix_detail=f"Would merge workspace/{slug}/ into workspace/ and remove nest",
        ))
    return findings


def check_stray_src_at_repo_root(slug: str) -> list[Finding]:
    """src/ or tests/ at repo root that belong in a project workspace."""
    findings = []
    for name in ("src", "tests", "test"):
        stray = REPO_ROOT / name
        if stray.is_dir():
            count = sum(1 for _ in stray.rglob("*.py") if _.is_file())
            if count:
                findings.append(Finding(
                    slug, "root_stray_dir", "warning",
                    f"Repo root {name}/ has {count} .py file(s) — may belong in workspace",
                    fixable=True,
                    fix_detail=f"Would merge root {name}/ into {slug}/workspace/{name}/",
                ))
    return findings


def check_orphan_init(slug: str, workspace: pathlib.Path) -> list[Finding]:
    """tests/__init__.py with relative imports that don't resolve."""
    findings = []
    for init in workspace.rglob("__init__.py"):
        if init.parent.name not in ("tests", "test"):
            continue
        try:
            text = init.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except SyntaxError:
            findings.append(Finding(
                slug, "broken_init", "error",
                f"Syntax error in {init.relative_to(workspace)}",
            ))
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level and node.level > 0:
                # Relative import — check if target exists
                if node.module:
                    parts = node.module.split(".")
                    target = init.parent / (parts[0] + ".py")
                    target_pkg = init.parent / parts[0] / "__init__.py"
                    if not target.exists() and not target_pkg.exists():
                        findings.append(Finding(
                            slug, "broken_init_import", "error",
                            f"{init.relative_to(workspace)}: relative import '.{node.module}' can't resolve",
                            fixable=True,
                            fix_detail="Would clear broken imports from __init__.py",
                        ))
    return findings


def check_validation_gap(slug: str, state: dict, phases_dir: pathlib.Path) -> list[Finding]:
    """All phases PASS but status is not complete."""
    findings = []
    status = state.get("status", "")
    total = state.get("total_phases", 0)
    if status == "complete" or not total or not phases_dir.exists():
        return findings

    passed_phases = 0
    for i in range(1, total + 1):
        vr = phases_dir / f"phase_{i}" / "validation_report.md"
        if vr.exists():
            text = vr.read_text(encoding="utf-8", errors="ignore")
            if "PASS" in text:
                passed_phases += 1

    if passed_phases >= total:
        findings.append(Finding(
            slug, "validation_gap", "error",
            f"All {total} phases PASS but status is '{status}' — should be complete",
            fixable=True,
            fix_detail="Would set status to 'complete'",
        ))
    return findings


def check_duplicate_titles(all_states: dict[str, dict]) -> list[Finding]:
    """Two projects with identical titles."""
    findings = []
    title_to_slugs = defaultdict(list)
    for slug, state in all_states.items():
        title = state.get("title", "").strip("[] ").lower()
        if title:
            title_to_slugs[title].append(slug)

    for title, slugs in title_to_slugs.items():
        if len(slugs) > 1:
            findings.append(Finding(
                slugs[0], "duplicate_title", "info",
                f"Title '{title}' shared by: {', '.join(slugs)}",
            ))
    return findings


def check_empty_workspace(slug: str, state: dict, workspace: pathlib.Path) -> list[Finding]:
    """Project has phases but workspace has zero Python files."""
    findings = []
    status = state.get("status", "")
    if status in ("complete", "budget_exceeded"):
        return findings
    if not workspace.exists():
        return findings

    py_files = list(workspace.rglob("*.py"))
    non_test_py = [f for f in py_files
                   if "test" not in f.name and "__pycache__" not in str(f)
                   and f.name != "__init__.py" and f.name != "conftest.py"]
    if not non_test_py and state.get("phase", 0) >= 1:
        findings.append(Finding(
            slug, "empty_workspace", "warning",
            f"No non-test Python files in workspace (phase {state.get('phase', '?')})",
        ))
    return findings


# ── Fix engine ───────────────────────────────────────────────────────

def apply_fix(finding: Finding) -> bool:
    """Apply an auto-fix for a finding. Returns True if fixed."""
    slug = finding.slug
    state_file = PROJECTS / slug / "state" / "current_idea.json"

    if finding.check == "stale_status":
        state = json.loads(state_file.read_text(encoding="utf-8"))
        phase = state.get("phase", 1)
        # Determine correct status suffix from existing status
        m = re.match(r"phase_\d+_(\w+)", state.get("status", ""))
        suffix = m.group(1) if m else "executing"
        state["status"] = f"phase_{phase}_{suffix}"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return True

    elif finding.check == "phantom_phases":
        state = json.loads(state_file.read_text(encoding="utf-8"))
        plan = (PROJECTS / slug / "state" / "master_plan.md").read_text(encoding="utf-8", errors="ignore")
        plan_phases = len(re.findall(r"^##\s+Phase\s+\d+", plan, re.MULTILINE))
        if plan_phases >= 2:
            state["total_phases"] = plan_phases
            state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            return True

    elif finding.check in ("shadow_leak", "shadow_pipeline", "shadow_script"):
        workspace = PROJECTS / slug / "workspace"
        actions = prune_workspace_shadows(workspace)
        return bool(actions)

    elif finding.check == "nested_slug_dir":
        workspace = PROJECTS / slug / "workspace"
        nested = workspace / slug
        if nested.is_dir():
            rescue_dir_filtered(nested, workspace)
            try:
                shutil.rmtree(str(nested))
            except OSError:
                pass
            return True

    elif finding.check == "root_stray_dir":
        workspace = PROJECTS / slug / "workspace"
        for name in ("src", "tests", "test"):
            stray = REPO_ROOT / name
            if stray.is_dir():
                dest = workspace / name
                rescue_dir_filtered(stray, dest)
                try:
                    shutil.rmtree(str(stray))
                except OSError:
                    pass
        return True

    elif finding.check == "broken_init_import":
        # Clear the __init__.py to just a comment
        for init in (PROJECTS / slug / "workspace").rglob("__init__.py"):
            if init.parent.name in ("tests", "test"):
                text = init.read_text(encoding="utf-8", errors="ignore")
                if "from ." in text:
                    init.write_text("# Tests package\n", encoding="utf-8")
                    return True

    elif finding.check == "validation_gap":
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["status"] = "complete"
        state["completed_at"] = datetime.now(timezone.utc).isoformat()
        slug = state.get("_slug") or slug
        state["_slug"] = slug
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        try:
            from pipeline.ideas_sync import record_completion
            title = state.get("title", slug)
            mi = pathlib.Path(__file__).parent / "master_ideas.md"
            ws = str((PROJECTS / slug / "workspace"))
            record_completion(
                slug, title,
                ideas_path=mi if mi.exists() else None,
                description=state.get("description", ""),
                workspace=ws,
            )
        except Exception:
            pass
        return True

    return False


# ── Main ─────────────────────────────────────────────────────────────

def run_health_check(fix: bool = False) -> list[Finding]:
    all_findings: list[Finding] = []
    all_states: dict[str, dict] = {}

    if not PROJECTS.exists():
        print("No .pipeline/projects/ found.")
        return all_findings

    for proj in sorted(PROJECTS.iterdir()):
        if not proj.is_dir():
            continue
        slug = proj.name
        state_file = proj / "state" / "current_idea.json"
        workspace = proj / "workspace"
        phases_dir = proj / "phases"
        plan_path = proj / "state" / "master_plan.md"

        if not state_file.exists():
            continue

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            all_findings.append(Finding(slug, "corrupt_state", "critical",
                                        "Cannot parse current_idea.json"))
            continue

        all_states[slug] = state

        # Run all checks
        all_findings.extend(check_stale_status(slug, state, phases_dir))
        all_findings.extend(check_phantom_phases(slug, state, plan_path))
        all_findings.extend(check_shadow_dirs(slug, workspace))
        all_findings.extend(check_slug_dir_at_workspace_root(slug, workspace))
        all_findings.extend(check_orphan_init(slug, workspace))
        all_findings.extend(check_validation_gap(slug, state, phases_dir))
        all_findings.extend(check_empty_workspace(slug, state, workspace))

    # Cross-project checks
    all_findings.extend(check_duplicate_titles(all_states))
    # Repo-root stray dirs (attribute to first active slug for fix targeting)
    active_slug = next(
        (s for s, st in all_states.items()
         if st.get("status") not in ("complete", "budget_exceeded")),
        next(iter(all_states), ""),
    )
    if active_slug:
        all_findings.extend(check_stray_src_at_repo_root(active_slug))

    # Apply fixes if requested
    if fix:
        for f in all_findings:
            if f.fixable and not f.fixed:
                if apply_fix(f):
                    f.fixed = True

    return all_findings


def main():
    parser = argparse.ArgumentParser(description="Tier 2 cross-project health checker")
    parser.add_argument("--fix", action="store_true", help="Auto-fix what's safe")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--severity", choices=["info", "warning", "error", "critical"],
                        help="Minimum severity to show")
    args = parser.parse_args()

    findings = run_health_check(fix=args.fix)

    # Filter by severity
    severity_order = {"info": 0, "warning": 1, "error": 2, "critical": 3}
    min_sev = severity_order.get(args.severity, 0) if args.severity else 0
    findings = [f for f in findings if severity_order.get(f.severity, 0) >= min_sev]

    if args.json:
        print(json.dumps([f.to_dict() for f in findings], indent=2))
        return

    # Summary
    total = len(findings)
    fixed = sum(1 for f in findings if f.fixed)
    fixable = sum(1 for f in findings if f.fixable and not f.fixed)

    if total == 0:
        print("[OK] All projects healthy -- no issues found.")
        return

    print(f"\n{'='*70}")
    print(f"  Health Check: {total} findings ({fixed} fixed, {fixable} fixable)")
    print(f"{'='*70}\n")

    # Group by severity
    by_sev = defaultdict(list)
    for f in findings:
        by_sev[f.severity].append(f)

    for sev in ("critical", "error", "warning", "info"):
        if sev not in by_sev:
            continue
        icon = {"critical": "[!!]", "error": "[!]", "warning": "[~]", "info": "[i]"}[sev]
        print(f"  {icon} {sev.upper()} ({len(by_sev[sev])})")
        for f in by_sev[sev]:
            tag = " [FIXED]" if f.fixed else ""
            print(f"    {f.slug}: {f.check} -- {f.message}{tag}")
        print()

    if fixable and not args.fix:
        print(f"  Run with --fix to auto-fix {fixable} issue(s).\n")

    if args.fix:
        try:
            mi = pathlib.Path(__file__).parent / "master_ideas.md"
            if mi.exists():
                from pipeline.ideas_sync import trim_completed_from_master_ideas
                n = trim_completed_from_master_ideas(mi, verbose=False)
                if n:
                    print(f"  [truth] trimmed {n} completed idea(s) from master_ideas.md\n")
        except Exception:
            pass


if __name__ == "__main__":
    main()
