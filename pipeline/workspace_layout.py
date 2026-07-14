"""Detect and repair workspace layout before ship field tests."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Root-level scripts kept outside the package directory during auto-repair.
_ROOT_SCRIPT_NAMES = frozenset({
    "conftest.py",
    "quick_test.py",
    "sweep_test.py",
    "setup.py",
})

_RELATIVE_IMPORT = re.compile(r"^\s*from\s+\.", re.MULTILINE)
_MODULE_MAIN = re.compile(r"python\s+-m\s+([\w.]+)\.main\b", re.IGNORECASE)


def infer_package_name(workspace: Path, slug: str = "") -> str:
    """Guess Python package name from main.py docstring or slug."""
    main = workspace / "main.py"
    if main.is_file():
        try:
            text = main.read_text(encoding="utf-8", errors="replace")
            m = _MODULE_MAIN.search(text)
            if m:
                return m.group(1).split(".")[0]
        except OSError:
            pass
    if slug:
        candidate = workspace / slug
        if candidate.is_dir() and (candidate / "__init__.py").is_file():
            return slug
        if slug.replace("-", "_").isidentifier():
            return slug.replace("-", "_")
    return slug or "app"


def _uses_relative_imports(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(_RELATIVE_IMPORT.search(text))


def analyze_layout(workspace: Path, package_name: str) -> dict[str, Any]:
    """
    Classify workspace layout.

    Modes:
      package        — workspace/<pkg>/main.py exists
      flat_relative  — main.py at root with relative imports (broken as script)
      flat_script    — main.py at root, no relative imports
      unknown        — no recognizable entry
    """
    workspace = workspace.resolve()
    pkg_dir = workspace / package_name
    flat_main = workspace / "main.py"
    pkg_main = pkg_dir / "main.py"

    if pkg_main.is_file():
        return {
            "mode": "package",
            "package_name": package_name,
            "entry_command": f"{sys.executable} -m {package_name}.main --help",
            "needs_repair": False,
        }

    if flat_main.is_file() and _uses_relative_imports(flat_main):
        return {
            "mode": "flat_relative",
            "package_name": package_name,
            "entry_command": f"{sys.executable} -m {package_name}.main --help",
            "needs_repair": True,
        }

    if flat_main.is_file():
        return {
            "mode": "flat_script",
            "package_name": "",
            "entry_command": f"{sys.executable} main.py --help",
            "needs_repair": False,
        }

    entry = _find_any_entry(workspace)
    if entry:
        rel = entry.relative_to(workspace).as_posix()
        return {
            "mode": "flat_script",
            "package_name": "",
            "entry_command": f"{sys.executable} {rel} --help",
            "needs_repair": False,
        }

    return {
        "mode": "unknown",
        "package_name": package_name,
        "entry_command": "",
        "needs_repair": False,
    }


def _find_any_entry(workspace: Path) -> Path | None:
    for name in ("main.py", "app.py", "cli.py"):
        p = workspace / name
        if p.is_file():
            return p
    return None


def _root_module_files(workspace: Path) -> list[Path]:
    """Python modules at workspace root that belong in the package (not harness scripts)."""
    files: list[Path] = []
    for p in sorted(workspace.glob("*.py")):
        if not p.is_file():
            continue
        if p.name in _ROOT_SCRIPT_NAMES:
            continue
        if p.name.startswith("test_"):
            continue
        files.append(p)
    return files


def ensure_package_layout(workspace: Path, package_name: str) -> tuple[bool, str]:
    """
    If modules use relative imports but live at workspace root, move them into
    workspace/<package_name>/ (config.py parent-of-sops pattern).

    Returns (changed, message).
    """
    workspace = workspace.resolve()
    analysis = analyze_layout(workspace, package_name)
    messages: list[str] = []
    changed = False

    if analysis["mode"] == "flat_relative":
        moved = _move_root_modules_into_package(workspace, package_name)
        if moved:
            changed = True
            messages.append(
                f"moved {len(moved)} module(s) into {package_name}/: {', '.join(moved)}"
            )
        elif not messages:
            return False, "flat_relative but no module files to move"

    # Finish partial repairs: package dir exists but harness left modules at root.
    pkg_dir = workspace / package_name
    if pkg_dir.is_dir() and (pkg_dir / "main.py").is_file():
        stray = _root_module_files(workspace)
        if stray:
            moved = _move_root_modules_into_package(workspace, package_name)
            if moved:
                changed = True
                messages.append(
                    f"completed layout: moved {len(moved)} stray module(s): {', '.join(moved)}"
                )

    if not changed:
        if analysis["mode"] == "package":
            return False, "already package layout"
        return False, f"layout={analysis['mode']} (no repair needed)"

    return True, "; ".join(messages)


def _move_root_modules_into_package(workspace: Path, package_name: str) -> list[str]:
    pkg_dir = workspace / package_name
    if pkg_dir.exists() and not pkg_dir.is_dir():
        return []
    pkg_dir.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for src in _root_module_files(workspace):
        dest = pkg_dir / src.name
        if dest.exists():
            continue
        shutil.move(str(src), str(dest))
        moved.append(src.name)
    return moved


def sanity_check_module(workspace: Path, package_name: str) -> tuple[bool, str]:
    """Run a quick `python -m pkg.main --help` from workspace."""
    layout = analyze_layout(workspace, package_name)
    cmd = layout.get("entry_command", "")
    if not cmd:
        return False, "no entry command detected"
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout: {cmd}"
    combined = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if proc.returncode == 0:
        return True, combined[:200] or "exit 0"
    return False, combined[:400] or f"exit {proc.returncode}"


def format_layout_block(workspace: Path, package_name: str) -> str:
    """Summary for field_test_planner prompts."""
    layout = analyze_layout(workspace, package_name)
    lines = [
        f"- mode: {layout['mode']}",
        f"- package: {layout.get('package_name') or '(none)'}",
    ]
    if layout.get("entry_command"):
        lines.append(f"- entry smoke: `{layout['entry_command']}`")
    if layout.get("needs_repair"):
        lines.append(
            f"- repair: run ensure_package_layout → create `{package_name}/` package dir"
        )
    ok, detail = sanity_check_module(workspace, package_name)
    lines.append(f"- entry check: {'PASS' if ok else 'FAIL'} ({detail[:120]})")
    return "\n".join(lines)
