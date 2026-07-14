"""Detect stale imports and broken path references in a workspace."""

from __future__ import annotations

import ast
import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_HARNESS_ROOT_FILES = frozenset({"conftest.py", "quick_test.py", "sweep_test.py"})

_STDLIB_ROOTS = set(getattr(sys, "stdlib_module_names", ())) | {
    "os", "sys", "json", "re", "pathlib", "typing", "datetime", "subprocess", "__future__",
    "time", "csv", "io", "logging", "argparse", "collections", "functools", "itertools",
    "uuid", "hashlib", "tempfile", "shutil", "copy", "math", "random", "enum", "dataclasses",
    "abc", "contextlib", "traceback", "unittest", "asyncio", "http", "urllib", "email",
    "html", "xml", "sqlite3", "threading", "multiprocessing", "socket", "ssl", "struct",
    "pickle", "base64", "binascii", "codecs", "inspect", "importlib", "pkgutil", "warnings",
    "textwrap", "string", "fractions", "decimal", "statistics", "heapq", "bisect", "array",
    "queue", "weakref", "types", "operator", "pprint", "configparser", "getpass", "platform",
    "signal", "selectors", "secrets", "hmac", "zlib", "gzip", "tarfile", "zipfile", "fnmatch",
    "glob", "linecache", "tokenize", "ast", "dis", "pydoc", "doctest", "pdb", "profile",
    "cProfile", "timeit", "sched", "locale", "gettext", "calendar", "zoneinfo",
}


def _is_stdlib_module(module: str) -> bool:
    root = module.split(".")[0]
    return root in _STDLIB_ROOTS


def _is_installed_module(module: str) -> bool:
    """True if importable as stdlib or third-party (pip-installed)."""
    root = module.split(".")[0]
    if _is_stdlib_module(module):
        return True
    try:
        return importlib.util.find_spec(root) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


@dataclass
class StaleRefIssue:
    file: str
    line: int
    kind: str
    detail: str


# Issue kinds that fail the structural validator gate (local graph only)
_BLOCKING_KINDS = frozenset({"syntax", "path_string", "local_import"})


@dataclass
class ImportGraphReport:
    issues: list[StaleRefIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    py_files: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def has_blocking_issues(self) -> bool:
        """True when validator structural gate should FAIL."""
        return any(i.kind in _BLOCKING_KINDS for i in self.issues)

    def format_block(self, max_issues: int = 20) -> str:
        if not self.issues and not self.warnings:
            return "No stale import or missing-path issues detected."
        lines = ["## Stale reference scan", ""]
        blocking = [i for i in self.issues if i.kind in _BLOCKING_KINDS]
        other = [i for i in self.issues if i.kind not in _BLOCKING_KINDS]
        for issue in blocking[:max_issues]:
            lines.append(
                f"- `{issue.file}:{issue.line}` [{issue.kind}] {issue.detail}"
            )
        for issue in other[: max(0, max_issues - len(blocking))]:
            lines.append(
                f"- `{issue.file}:{issue.line}` [{issue.kind}] {issue.detail} (non-blocking)"
            )
        for w in self.warnings[:10]:
            lines.append(f"- warning: {w}")
        if len(self.issues) > max_issues:
            lines.append(f"- ... and {len(self.issues) - max_issues} more")
        return "\n".join(lines)


def _module_to_path(workspace: Path, module: str) -> Path | None:
    parts = module.split(".")
    candidate = workspace.joinpath(*parts)
    if candidate.with_suffix(".py").is_file():
        return candidate.with_suffix(".py")
    if (candidate / "__init__.py").is_file():
        return candidate / "__init__.py"
    return None


def _workspace_local_roots(workspace: Path) -> set[str]:
    """Top-level package/module names that live inside *workspace*."""
    roots: set[str] = set()
    if not workspace.is_dir():
        return roots
    try:
        for p in workspace.iterdir():
            if p.name.startswith(".") or p.name == "__pycache__":
                continue
            if p.is_dir() and (
                (p / "__init__.py").is_file() or any(p.rglob("*.py"))
            ):
                roots.add(p.name)
            elif p.is_file() and p.suffix == ".py" and p.name != "__init__.py":
                roots.add(p.stem)
    except OSError:
        pass
    return roots


def _resolve_import(
    workspace: Path,
    node: ast.AST,
    py_file: Path,
    local_roots: set[str],
) -> tuple[list[str], list[str]]:
    """Return (local_missing, external_unresolved).

    Local missing = root package appears under workspace but path not found.
    External unresolved = not installed and not a workspace package (non-blocking).
    """
    local_missing: list[str] = []
    external: list[str] = []

    def _check(module: str) -> None:
        if not module or module.startswith("."):
            return
        if _is_stdlib_module(module):
            return
        if _is_installed_module(module):
            return
        if _module_to_path(workspace, module) is not None:
            return
        root = module.split(".")[0]
        if root in local_roots:
            local_missing.append(module)
        else:
            external.append(module)

    if isinstance(node, ast.Import):
        for alias in node.names:
            _check(alias.name)
    elif isinstance(node, ast.ImportFrom):
        if node.level and node.level > 0:
            return local_missing, external
        if node.module:
            _check(node.module)
    return local_missing, external


def scan_workspace(workspace: Path) -> ImportGraphReport:
    report = ImportGraphReport()
    if not workspace.is_dir():
        return report

    py_files = sorted(
        p for p in workspace.rglob("*.py")
        if p.is_file()
        and "__pycache__" not in p.parts
        and not (
            p.parent == workspace.resolve() and p.name in _HARNESS_ROOT_FILES
        )
    )
    report.py_files = [str(p.relative_to(workspace)) for p in py_files]
    known = {p.resolve() for p in py_files}
    local_roots = _workspace_local_roots(workspace)

    for py_file in py_files:
        rel = str(py_file.relative_to(workspace))
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError as exc:
            report.issues.append(
                StaleRefIssue(rel, exc.lineno or 0, "syntax", str(exc.msg))
            )
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                local_miss, external = _resolve_import(
                    workspace, node, py_file, local_roots,
                )
                for mod in local_miss:
                    report.issues.append(
                        StaleRefIssue(
                            rel,
                            getattr(node, "lineno", 0),
                            "local_import",
                            f"local module not found: {mod}",
                        )
                    )
                for mod in external:
                    report.warnings.append(
                        f"{rel}:{getattr(node, 'lineno', 0)} unresolved import "
                        f"(not installed, not local): {mod}"
                    )

        # String paths that look like .py files under workspace
        text = py_file.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"""['"]([./\w][\w./\\-]*\.py)['"]""", text):
            raw = m.group(1).replace("\\", "/")
            if raw.startswith("./"):
                raw = raw[2:]
            candidate = (workspace / raw).resolve()
            if ".py" in raw and candidate not in known and not candidate.is_file():
                line_no = text[: m.start()].count("\n") + 1
                report.issues.append(
                    StaleRefIssue(
                        rel,
                        line_no,
                        "path_string",
                        f"references missing file: {raw}",
                    )
                )

    return report
