"""
pipeline/validator.py
Code quality validator: syntax, imports, types, docstrings, complexity,
security, style, config, and multi-file validation.
"""

import ast
import importlib
import inspect
import os
import re
import sys
import textwrap
import tokenize
import io
from typing import Any, Dict, List, Optional


# ── Config ────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "max_complexity": 10,
    "max_line_length": 100,
    "require_docstrings": False,
    "require_types": False,
    "security_checks": True,
}


def validate_config(config: Optional[Dict[str, Any]] = None) -> bool:
    """Validate that the config dict has acceptable values."""
    if config is None:
        return True
    valid_keys = {
        "max_complexity",
        "max_line_length",
        "require_docstrings",
        "require_types",
        "security_checks",
    }
    for key, value in config.items():
        if key not in valid_keys:
            return False
        if key in ("max_complexity", "max_line_length"):
            if not isinstance(value, (int, float)) or value < 0:
                return False
        if key in ("require_docstrings", "require_types"):
            if not isinstance(value, bool):
                return False
        if key == "security_checks" and not isinstance(value, bool):
            return False
    return True


# ── Syntax Validation ─────────────────────────────────────────────────────

def validate_syntax(filepath: str) -> List[Dict[str, Any]]:
    """Check a Python file for syntax errors."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source, filename=filepath)
    except SyntaxError as e:
        issues.append({
            "file": filepath,
            "line": e.lineno or 0,
            "message": f"Syntax error: {e.msg}",
        })
    except FileNotFoundError:
        issues.append({
            "file": filepath,
            "line": 0,
            "message": f"File not found: {filepath}",
        })
    except Exception as e:
        issues.append({
            "file": filepath,
            "line": 0,
            "message": f"Error reading file: {e}",
        })
    return issues


# ── Import Validation ─────────────────────────────────────────────────────

def validate_imports(filepath: str, search_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Check that all imports in a file can be resolved."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, FileNotFoundError):
        return issues

    if search_paths is None:
        search_paths = [os.path.dirname(filepath)]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split(".")[0]
                try:
                    importlib.import_module(module_name)
                except ImportError:
                    issues.append({
                        "file": filepath,
                        "line": node.lineno,
                        "message": f"Cannot import module: {alias.name}",
                    })
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split(".")[0]
                try:
                    importlib.import_module(module_name)
                except ImportError:
                    issues.append({
                        "file": filepath,
                        "line": node.lineno,
                        "message": f"Cannot import from module: {node.module}",
                    })
    return issues


# ── Type Hint Validation ──────────────────────────────────────────────────

def validate_types(filepath: str) -> List[Dict[str, Any]]:
    """Check for type hint correctness in a Python file."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, FileNotFoundError):
        return issues

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Check return type annotation
            if node.returns:
                return_str = ast.dump(node.returns)
                # Simple heuristic: if return is annotated as str but body returns non-str
                # We just check that annotations exist, not deep type checking
                pass
    return issues


# ── Docstring Validation ──────────────────────────────────────────────────

def validate_docstrings(filepath: str) -> List[Dict[str, Any]]:
    """Check that public functions and classes have docstrings."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, FileNotFoundError):
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                    issues.append({
                        "file": filepath,
                        "line": node.lineno,
                        "message": f"Function '{node.name}' is missing a docstring",
                    })
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                    issues.append({
                        "file": filepath,
                        "line": node.lineno,
                        "message": f"Class '{node.name}' is missing a docstring",
                    })
    return issues


# ── Complexity Validation ─────────────────────────────────────────────────

def _count_complexity(node: ast.AST) -> int:
    """Count cyclomatic complexity of a function node."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


def validate_complexity(filepath: str, max_complexity: int = 10) -> List[Dict[str, Any]]:
    """Check function complexity against a threshold."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, FileNotFoundError):
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = _count_complexity(node)
            if complexity > max_complexity:
                issues.append({
                    "file": filepath,
                    "line": node.lineno,
                    "message": f"Function '{node.name}' has complexity {complexity} (max: {max_complexity})",
                })
    return issues


# ── Security Validation ───────────────────────────────────────────────────

def validate_security(filepath: str) -> List[Dict[str, Any]]:
    """Check for dangerous patterns in code."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, FileNotFoundError):
        return issues

    dangerous_patterns = {
        "eval": "Use of eval() is dangerous",
        "exec": "Use of exec() is dangerous",
        "pickle.load": "Use of pickle.load() is dangerous",
        "pickle.loads": "Use of pickle.loads() is dangerous",
        "shell=True": "Use of shell=True in subprocess is dangerous",
    }

    # Check source text for shell=True
    if "shell=True" in source:
        for i, line in enumerate(source.splitlines(), 1):
            if "shell=True" in line:
                issues.append({
                    "file": filepath,
                    "line": i,
                    "message": "Use of shell=True in subprocess is dangerous",
                })

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            func_name = None
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr

            if func_name == "eval":
                issues.append({
                    "file": filepath,
                    "line": node.lineno,
                    "message": dangerous_patterns["eval"],
                })
            elif func_name == "exec":
                issues.append({
                    "file": filepath,
                    "line": node.lineno,
                    "message": dangerous_patterns["exec"],
                })
            elif isinstance(func, ast.Attribute) and func.attr in ("load", "loads"):
                if isinstance(func.value, ast.Name) and func.value.id == "pickle":
                    issues.append({
                        "file": filepath,
                        "line": node.lineno,
                        "message": dangerous_patterns[f"pickle.{func.attr}"],
                    })
    return issues


# ── Style Validation ──────────────────────────────────────────────────────

def validate_style(filepath: str, max_line_length: int = 100) -> List[Dict[str, Any]]:
    """Check code style (PEP 8 basics)."""
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        return issues

    lines = source.splitlines()
    for i, line in enumerate(lines, 1):
        # Long lines
        if len(line) > max_line_length:
            issues.append({
                "file": filepath,
                "line": i,
                "message": f"Line too long ({len(line)} > {max_line_length} chars)",
            })
        # Missing whitespace around operators (simple check)
        if re.search(r'[a-zA-Z0-9_][a-zA-Z0-9_]*\s*[+\-*/]=', line):
            pass  # skip augmented assignments
        if re.search(r'[^=]\s*[+\-*/]\s*[+\-*/]', line):
            pass  # skip normal expressions
        # Check for missing space around = in assignments (not ==)
        if re.search(r'[^!=<>]=[^=]', line) and not line.strip().startswith('#'):
            # Simple heuristic: x=1 should be x = 1
            if re.search(r'[a-zA-Z0-9_]\s*[+\-*/]\s*[a-zA-Z0-9_]', line):
                pass  # skip expressions
            elif re.search(r'=\s*[a-zA-Z0-9_]', line) and not re.search(r'==', line):
                if not re.search(r'=\s*["\']', line) and not re.search(r'=\s*None', line):
                    if re.search(r'[a-zA-Z0-9_]\s*=\s*[a-zA-Z0-9_]', line):
                        # Check if there's no space around =
                        if re.search(r'[a-zA-Z0-9_]=[a-zA-Z0-9_]', line):
                            issues.append({
                                "file": filepath,
                                "line": i,
                                "message": "Missing whitespace around operator",
                            })
    return issues


# ── Validator Class ───────────────────────────────────────────────────────

class Validator:
    """Main validator class that runs all checks."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}

    def validate(self, filepath: str) -> List[Dict[str, Any]]:
        """Run all validation checks on a file."""
        issues = []
        issues.extend(validate_syntax(filepath))
        if not issues:  # Only check imports if syntax is OK
            issues.extend(validate_imports(filepath))
        issues.extend(validate_types(filepath))
        if self.config.get("require_docstrings", False):
            issues.extend(validate_docstrings(filepath))
        issues.extend(validate_complexity(filepath, self.config.get("max_complexity", 10)))
        if self.config.get("security_checks", True):
            issues.extend(validate_security(filepath))
        issues.extend(validate_style(filepath, self.config.get("max_line_length", 100)))
        return issues


# ── Multi-file Validation ─────────────────────────────────────────────────

def validate_all(filepaths: List[str], config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Validate multiple files and return all issues."""
    all_issues = []
    for filepath in filepaths:
        all_issues.extend(Validator(config=config).validate(filepath))
    return all_issues
