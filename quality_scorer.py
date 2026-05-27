#!/usr/bin/env python3
"""
quality_scorer.py — Tier 1 deterministic code quality scorer.

Scores every project on 6 dimensions (100 points max):

  1. Test pass rate      (25 pts) — pytest results
  2. File completeness   (20 pts) — tasks spec vs actual files
  3. Import health       (15 pts) — all modules importable?
  4. Code complexity     (15 pts) — avg function length, nesting depth
  5. Docstring coverage  (10 pts) — % of public functions documented
  6. Project structure   (15 pts) — README, config, CLI entry point

Run:
    python quality_scorer.py                   # score all projects
    python quality_scorer.py --top 10          # show top 10
    python quality_scorer.py --bottom 10       # show bottom 10 (recycle candidates)
    python quality_scorer.py --project foo     # score a single project
    python quality_scorer.py --csv             # output as CSV
    python quality_scorer.py --threshold 70    # only show projects above threshold
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))
from pipeline.paths import projects_dir  # noqa: E402


@dataclass
class ScoreBreakdown:
    test_pass_rate: float = 0.0      # 0-25
    file_completeness: float = 0.0   # 0-20
    import_health: float = 0.0       # 0-15
    code_complexity: float = 0.0     # 0-15
    docstring_coverage: float = 0.0  # 0-10
    project_structure: float = 0.0   # 0-15

    @property
    def total(self) -> float:
        return (self.test_pass_rate + self.file_completeness +
                self.import_health + self.code_complexity +
                self.docstring_coverage + self.project_structure)


@dataclass
class ProjectScore:
    slug: str
    title: str
    status: str
    phase: int
    total_phases: int
    score: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    details: dict = field(default_factory=dict)

    @property
    def total(self) -> float:
        return self.score.total

    def grade(self) -> str:
        t = self.total
        if t >= 90: return "A"
        if t >= 80: return "B"
        if t >= 70: return "C"
        if t >= 60: return "D"
        return "F"

    def tier(self) -> str:
        t = self.total
        if t >= 80: return "TOP"       # Ready for human review
        if t >= 50: return "MIDDLE"    # Auto-fix and re-validate
        return "BOTTOM"                 # Recycle back to runner


# ── Scoring functions ────────────────────────────────────────────────

def score_test_pass_rate(workspace: pathlib.Path) -> tuple[float, dict]:
    """Run pytest and score based on pass rate. Max 25 points."""
    test_files = list(workspace.rglob("test_*.py"))
    if not test_files:
        return 0.0, {"reason": "no test files found"}

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(workspace), "-q",
             "--tb=no", "--no-header", "-x", "--timeout=10"],
            capture_output=True, text=True, timeout=30,
            cwd=str(workspace),
        )
        output = result.stdout + result.stderr

        # Parse "X passed, Y failed" or "X passed"
        passed = failed = errors = 0
        m = re.search(r"(\d+) passed", output)
        if m: passed = int(m.group(1))
        m = re.search(r"(\d+) failed", output)
        if m: failed = int(m.group(1))
        m = re.search(r"(\d+) error", output)
        if m: errors = int(m.group(1))

        total = passed + failed + errors
        if total == 0:
            return 5.0, {"reason": "tests exist but none collected", "test_files": len(test_files)}

        rate = passed / total
        points = rate * 25.0
        return round(points, 1), {
            "passed": passed, "failed": failed, "errors": errors,
            "total": total, "rate": round(rate, 3),
        }
    except subprocess.TimeoutExpired:
        return 5.0, {"reason": "pytest timed out (30s)"}
    except Exception as e:
        return 0.0, {"reason": f"pytest error: {str(e)[:100]}"}


def score_file_completeness(slug: str, workspace: pathlib.Path,
                             phases_dir: pathlib.Path) -> tuple[float, dict]:
    """Check if files mentioned in tasks.md actually exist. Max 20 points."""
    if not phases_dir.exists():
        return 10.0, {"reason": "no phases directory"}

    total_files = 0
    present_files = 0

    for phase_dir in sorted(phases_dir.iterdir()):
        tasks_file = phase_dir / "tasks.md"
        if not tasks_file.exists():
            continue

        text = tasks_file.read_text(encoding="utf-8", errors="ignore")
        # Extract file paths from "Files: foo.py, bar.py" or "- Files: ..." patterns
        file_refs = re.findall(r'[\w/]+\.py', text)
        for ref in file_refs:
            total_files += 1
            # Check various possible locations
            candidates = [
                workspace / ref,
                workspace / slug / ref,
                workspace / "src" / ref,
                workspace / "src" / slug / ref,
            ]
            if any(c.exists() for c in candidates):
                present_files += 1

    if total_files == 0:
        # Fallback: just check if workspace has py files
        py_count = sum(1 for _ in workspace.rglob("*.py")
                       if "__pycache__" not in str(_))
        if py_count > 5:
            return 15.0, {"reason": "no file refs in tasks but workspace has code", "py_files": py_count}
        return 5.0, {"reason": "no file refs in tasks.md", "py_files": py_count}

    rate = present_files / total_files
    points = rate * 20.0
    return round(points, 1), {
        "referenced": total_files, "present": present_files,
        "rate": round(rate, 3),
    }


def score_import_health(workspace: pathlib.Path) -> tuple[float, dict]:
    """Check if all .py files parse without syntax errors. Max 15 points."""
    py_files = [f for f in workspace.rglob("*.py")
                if "__pycache__" not in str(f)]
    if not py_files:
        return 0.0, {"reason": "no Python files"}

    parseable = 0
    errors = []
    for f in py_files:
        try:
            ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
            parseable += 1
        except SyntaxError as e:
            errors.append(f"{f.name}:{e.lineno}")

    rate = parseable / len(py_files) if py_files else 0
    points = rate * 15.0
    return round(points, 1), {
        "total_files": len(py_files), "parseable": parseable,
        "syntax_errors": errors[:5], "rate": round(rate, 3),
    }


def score_code_complexity(workspace: pathlib.Path) -> tuple[float, dict]:
    """Score based on average function length and nesting depth. Max 15 points."""
    py_files = [f for f in workspace.rglob("*.py")
                if "__pycache__" not in str(f)
                and "test" not in f.name.lower()
                and f.name != "conftest.py"]
    if not py_files:
        return 7.5, {"reason": "no non-test Python files"}

    total_functions = 0
    total_lines = 0
    max_nesting = 0

    for f in py_files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                # Estimate function length
                if hasattr(node, "end_lineno") and node.end_lineno:
                    func_len = node.end_lineno - node.lineno + 1
                    total_lines += func_len
                # Estimate nesting depth
                depth = _max_nesting_depth(node)
                max_nesting = max(max_nesting, depth)

    if total_functions == 0:
        return 7.5, {"reason": "no functions found"}

    avg_len = total_lines / total_functions
    # Ideal: avg < 20 lines, max nesting < 5
    len_score = max(0, min(1, 1 - (avg_len - 20) / 40))  # 0 if avg > 60
    nest_score = max(0, min(1, 1 - (max_nesting - 4) / 6))  # 0 if nesting > 10
    points = ((len_score + nest_score) / 2) * 15.0

    return round(points, 1), {
        "total_functions": total_functions,
        "avg_function_length": round(avg_len, 1),
        "max_nesting_depth": max_nesting,
    }


def _max_nesting_depth(node: ast.AST, depth: int = 0) -> int:
    """Calculate max nesting depth of control flow in a function."""
    max_d = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            max_d = max(max_d, _max_nesting_depth(child, depth + 1))
        else:
            max_d = max(max_d, _max_nesting_depth(child, depth))
    return max_d


def score_docstring_coverage(workspace: pathlib.Path) -> tuple[float, dict]:
    """Check what % of public functions/classes have docstrings. Max 10 points."""
    py_files = [f for f in workspace.rglob("*.py")
                if "__pycache__" not in str(f)
                and "test" not in f.name.lower()
                and f.name != "conftest.py"]

    total_public = 0
    documented = 0

    for f in py_files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
                if name.startswith("_") and not name.startswith("__"):
                    continue  # Skip private
                total_public += 1
                if (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                    documented += 1

    if total_public == 0:
        return 5.0, {"reason": "no public functions/classes"}

    rate = documented / total_public
    points = rate * 10.0
    return round(points, 1), {
        "public_symbols": total_public, "documented": documented,
        "rate": round(rate, 3),
    }


def score_project_structure(slug: str, workspace: pathlib.Path) -> tuple[float, dict]:
    """Check for README, config, CLI entry, __init__.py. Max 15 points."""
    checks = {}
    points = 0.0

    # README
    has_readme = any(workspace.glob("README*")) or any(workspace.glob("*/README*"))
    checks["readme"] = has_readme
    if has_readme: points += 3.0

    # Requirements or pyproject.toml
    has_deps = ((workspace / "requirements.txt").exists() or
                (workspace / "pyproject.toml").exists() or
                (workspace / "setup.py").exists())
    checks["dependencies_file"] = has_deps
    if has_deps: points += 2.0

    # __init__.py in main package
    slug_pkg = workspace / slug
    has_init = (slug_pkg / "__init__.py").exists() if slug_pkg.exists() else False
    # Also check if there's a top-level __init__.py
    if not has_init:
        has_init = (workspace / "__init__.py").exists()
    checks["package_init"] = has_init
    if has_init: points += 2.0

    # CLI entry point (cli.py, __main__.py, or click/argparse usage)
    has_cli = False
    for name in ("cli.py", "__main__.py", "main.py", "app.py"):
        if (workspace / name).exists() or (workspace / slug / name).exists():
            has_cli = True
            break
    # Also check src/ layout
    if not has_cli:
        for name in ("cli.py", "__main__.py"):
            if list(workspace.rglob(name)):
                has_cli = True
                break
    checks["cli_entry"] = has_cli
    if has_cli: points += 3.0

    # Config file
    has_config = any(workspace.rglob("config*")) or any(workspace.rglob("*.yaml"))
    checks["config_file"] = has_config
    if has_config: points += 2.0

    # Test directory
    test_files = list(workspace.rglob("test_*.py"))
    checks["has_tests"] = len(test_files) > 0
    checks["test_count"] = len(test_files)
    if test_files: points += 3.0

    return round(points, 1), checks


# ── Main scorer ──────────────────────────────────────────────────────

def score_project(slug: str, run_tests: bool = True) -> Optional[ProjectScore]:
    """Score a single project across all dimensions."""
    proj_dir = projects_dir() / slug
    state_file = proj_dir / "state" / "current_idea.json"
    workspace = proj_dir / "workspace"
    phases_dir = proj_dir / "phases"

    if not state_file.exists():
        return None

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return None

    ps = ProjectScore(
        slug=slug,
        title=state.get("title", slug),
        status=state.get("status", "unknown"),
        phase=state.get("phase", 0),
        total_phases=state.get("total_phases", 0),
    )

    if not workspace.exists():
        return ps

    # Score each dimension
    if run_tests:
        pts, det = score_test_pass_rate(workspace)
    else:
        pts, det = 0.0, {"reason": "skipped"}
    ps.score.test_pass_rate = pts
    ps.details["test_pass_rate"] = det

    pts, det = score_file_completeness(slug, workspace, phases_dir)
    ps.score.file_completeness = pts
    ps.details["file_completeness"] = det

    pts, det = score_import_health(workspace)
    ps.score.import_health = pts
    ps.details["import_health"] = det

    pts, det = score_code_complexity(workspace)
    ps.score.code_complexity = pts
    ps.details["code_complexity"] = det

    pts, det = score_docstring_coverage(workspace)
    ps.score.docstring_coverage = pts
    ps.details["docstring_coverage"] = det

    pts, det = score_project_structure(slug, workspace)
    ps.score.project_structure = pts
    ps.details["project_structure"] = det

    return ps


def score_all_projects(run_tests: bool = True,
                        only_complete: bool = False) -> list[ProjectScore]:
    """Score all projects."""
    scores = []
    for proj in sorted(projects_dir().iterdir()):
        if not proj.is_dir():
            continue
        state_file = proj / "state" / "current_idea.json"
        if not state_file.exists():
            continue

        if only_complete:
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                if state.get("status") != "complete":
                    continue
            except Exception:
                continue

        ps = score_project(proj.name, run_tests=run_tests)
        if ps:
            scores.append(ps)

    return sorted(scores, key=lambda s: s.total, reverse=True)


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Tier 1 code quality scorer")
    parser.add_argument("--project", help="Score a single project")
    parser.add_argument("--top", type=int, help="Show top N projects")
    parser.add_argument("--bottom", type=int, help="Show bottom N projects")
    parser.add_argument("--threshold", type=float, help="Only show projects above threshold")
    parser.add_argument("--complete-only", action="store_true", help="Only score complete projects")
    parser.add_argument("--no-tests", action="store_true", help="Skip running pytest (faster)")
    parser.add_argument("--csv", action="store_true", help="Output as CSV")
    parser.add_argument("--json", action="store_true", help="Output as JSON with details")
    args = parser.parse_args()

    run_tests = not args.no_tests

    if args.project:
        ps = score_project(args.project, run_tests=run_tests)
        if not ps:
            print(f"Project '{args.project}' not found.")
            return
        _print_detail(ps)
        return

    print("Scoring projects...", end="", flush=True)
    scores = score_all_projects(run_tests=run_tests, only_complete=args.complete_only)
    print(f" done ({len(scores)} projects)\n")

    if args.threshold:
        scores = [s for s in scores if s.total >= args.threshold]

    if args.bottom:
        scores = list(reversed(scores[-args.bottom:]))

    if args.top:
        scores = scores[:args.top]

    if args.json:
        data = [{"slug": s.slug, "title": s.title, "status": s.status,
                 "total": round(s.total, 1), "grade": s.grade(), "tier": s.tier(),
                 "breakdown": {
                     "test_pass_rate": s.score.test_pass_rate,
                     "file_completeness": s.score.file_completeness,
                     "import_health": s.score.import_health,
                     "code_complexity": s.score.code_complexity,
                     "docstring_coverage": s.score.docstring_coverage,
                     "project_structure": s.score.project_structure,
                 },
                 "details": s.details}
                for s in scores]
        print(json.dumps(data, indent=2))
        return

    if args.csv:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["slug", "title", "status", "score", "grade", "tier",
                     "tests", "files", "imports", "complexity", "docs", "structure"])
        for s in scores:
            w.writerow([s.slug, s.title, s.status, round(s.total, 1), s.grade(), s.tier(),
                         s.score.test_pass_rate, s.score.file_completeness,
                         s.score.import_health, s.score.code_complexity,
                         s.score.docstring_coverage, s.score.project_structure])
        print(buf.getvalue())
        return

    # Table output
    _print_table(scores)

    # Summary
    tiers = {"TOP": 0, "MIDDLE": 0, "BOTTOM": 0}
    for s in scores:
        tiers[s.tier()] += 1
    print(f"\n  Tier Summary: {tiers['TOP']} TOP | {tiers['MIDDLE']} MIDDLE | {tiers['BOTTOM']} BOTTOM")
    if scores:
        avg = sum(s.total for s in scores) / len(scores)
        print(f"  Average Score: {avg:.1f}/100")


def _print_table(scores: list[ProjectScore]):
    header = f"  {'SLUG':<45} {'STATUS':<18} {'SCORE':>5} {'GRD':>3} {'TIER':>6}  {'TEST':>4} {'FILE':>4} {'IMP':>3} {'CMP':>3} {'DOC':>3} {'STR':>3}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for s in scores:
        tier_icon = {"TOP": "[+]", "MIDDLE": "[~]", "BOTTOM": "[-]"}[s.tier()]
        print(f"  {s.slug:<45} {s.status:<18} {s.total:>5.1f} {s.grade():>3} {tier_icon:>4}  "
              f"{s.score.test_pass_rate:>4.0f} {s.score.file_completeness:>4.0f} "
              f"{s.score.import_health:>3.0f} {s.score.code_complexity:>3.0f} "
              f"{s.score.docstring_coverage:>3.0f} {s.score.project_structure:>3.0f}")


def _print_detail(ps: ProjectScore):
    print(f"\n  Project: {ps.slug}")
    print(f"  Title:   {ps.title}")
    print(f"  Status:  {ps.status} (phase {ps.phase}/{ps.total_phases})")
    print(f"  Score:   {ps.total:.1f}/100 (Grade: {ps.grade()}, Tier: {ps.tier()})")
    print()
    print(f"  Tests:       {ps.score.test_pass_rate:>5.1f}/25  {ps.details.get('test_pass_rate', {})}")
    print(f"  Files:       {ps.score.file_completeness:>5.1f}/20  {ps.details.get('file_completeness', {})}")
    print(f"  Imports:     {ps.score.import_health:>5.1f}/15  {ps.details.get('import_health', {})}")
    print(f"  Complexity:  {ps.score.code_complexity:>5.1f}/15  {ps.details.get('code_complexity', {})}")
    print(f"  Docstrings:  {ps.score.docstring_coverage:>5.1f}/10  {ps.details.get('docstring_coverage', {})}")
    print(f"  Structure:   {ps.score.project_structure:>5.1f}/15  {ps.details.get('project_structure', {})}")


if __name__ == "__main__":
    main()
