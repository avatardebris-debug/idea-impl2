"""
linter.py — AST and structure-based static analysis.
"""
import ast
import pathlib
from dataclasses import dataclass
from typing import Iterator

@dataclass
class LintError:
    file: str
    line: int
    message: str

def check_syntax(file_path: pathlib.Path) -> list[LintError]:
    """Check if the python file has valid syntax."""
    errors = []
    try:
        content = file_path.read_text(encoding="utf-8")
        ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        errors.append(LintError(
            file=str(file_path),
            line=e.lineno or 0,
            message=f"SyntaxError: {e.msg}"
        ))
    except Exception as e:
        errors.append(LintError(
            file=str(file_path),
            line=0,
            message=f"ReadError: {str(e)}"
        ))
    return errors

def check_project_structure(project_dir: pathlib.Path) -> list[LintError]:
    """Ensure standard pipeline structure (tests/, pyproject.toml)."""
    errors = []
    
    # Needs a pyproject.toml in the workspace
    if not (project_dir / "pyproject.toml").exists():
        errors.append(LintError(file=str(project_dir), line=0, message="Missing pyproject.toml"))
        
    # Needs a tests directory
    if not (project_dir / "tests").is_dir():
        errors.append(LintError(file=str(project_dir), line=0, message="Missing 'tests' directory"))
        
    return errors

def lint_workspace(workspace_dir: pathlib.Path) -> list[LintError]:
    all_errors = []
    
    all_errors.extend(check_project_structure(workspace_dir))
    
    for py_file in workspace_dir.rglob("*.py"):
        all_errors.extend(check_syntax(py_file))
        
    return all_errors

def format_report(errors: list[LintError]) -> str:
    if not errors:
        return "✅ All checks passed! No lint errors found."
        
    lines = ["❌ Linting Errors Found:", ""]
    for err in errors:
        lines.append(f"{err.file}:{err.line} - {err.message}")
    lines.append(f"\nTotal Errors: {len(errors)}")
    return "\n".join(lines)
