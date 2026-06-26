"""Detect stale imports and broken path references in a workspace."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StaleRefIssue:
    file: str
    line: int
    kind: str
    detail: str


@dataclass
class ImportGraphReport:
    issues: list[StaleRefIssue] = field(default_factory=list)
    py_files: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def format_block(self, max_issues: int = 20) -> str:
        if not self.issues:
            return "No stale import or missing-path issues detected."
        lines = ["## Stale reference scan", ""]
        for issue in self.issues[:max_issues]:
            lines.append(
                f"- `{issue.file}:{issue.line}` [{issue.kind}] {issue.detail}"
            )
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


def _resolve_import(workspace: Path, node: ast.AST, py_file: Path) -> list[str]:
    missing: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.startswith("."):
                continue
            if _module_to_path(workspace, alias.name) is None:
                missing.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        if node.level and node.level > 0:
            return missing
        if node.module and _module_to_path(workspace, node.module) is None:
            # stdlib / third-party — skip common names
            root = node.module.split(".")[0]
            if root in {"os", "sys", "json", "re", "pathlib", "typing", "datetime", "subprocess"}:
                return missing
            missing.append(node.module)
    return missing


def scan_workspace(workspace: Path) -> ImportGraphReport:
    report = ImportGraphReport()
    if not workspace.is_dir():
        return report

    py_files = sorted(
        p for p in workspace.rglob("*.py")
        if p.is_file() and "__pycache__" not in p.parts
    )
    report.py_files = [str(p.relative_to(workspace)) for p in py_files]
    known = {p.resolve() for p in py_files}

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
                for mod in _resolve_import(workspace, node, py_file):
                    report.issues.append(
                        StaleRefIssue(
                            rel,
                            getattr(node, "lineno", 0),
                            "import",
                            f"local module not found: {mod}",
                        )
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
