"""
tools.py — Agent tool functions for the OSINT Corp2 pipeline.

All tools are self-contained (stdlib only), handle errors gracefully,
and return error strings instead of raising exceptions.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
import tempfile
import time
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Timeout configuration
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT = 120  # seconds


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Read file contents. Returns error string on failure."""
    try:
        p = pathlib.Path(path)
        if not p.exists():
            return f"ERROR: File not found: {path}"
        return p.read_text(encoding="utf-8")
    except PermissionError:
        return f"ERROR: Permission denied reading: {path}"
    except UnicodeDecodeError:
        return f"ERROR: File is binary or non-UTF-8: {path}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def write_file(path: str, content: str) -> str:
    """Create or overwrite a file. Creates parent directories automatically."""
    try:
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"OK: Wrote {p.resolve()} ({len(content)} chars)"
    except PermissionError:
        return f"ERROR: Permission denied writing: {path}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def append_file(path: str, content: str) -> str:
    """Append content to a file. Creates the file if it doesn't exist."""
    try:
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
        return f"OK: Appended to {p.resolve()}"
    except PermissionError:
        return f"ERROR: Permission denied appending: {path}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def list_tree(path: str, max_depth: int = 10) -> str:
    """Recursively list directory tree. Returns formatted string."""
    try:
        root = pathlib.Path(path)
        if not root.exists():
            return f"ERROR: Path not found: {path}"
        if not root.is_dir():
            return f"ERROR: Not a directory: {path}"

        lines = [f"{root.name}/"]
        _list_tree_recursive(root, lines, 1, max_depth)
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def _list_tree_recursive(dirpath: pathlib.Path, lines: list, depth: int, max_depth: int) -> None:
    """Helper for list_tree: recursively add entries."""
    if depth > max_depth:
        return
    try:
        entries = sorted(dirpath.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        lines.append("  " * depth + "[permission denied]")
        return

    dirs = [e for e in entries if e.is_dir()]
    files = [e for e in entries if e.is_file()]

    for f in files:
        lines.append("  " * depth + f"📄 {f.name}")
    for d in dirs:
        lines.append("  " * depth + f"📁 {d.name}/")
        _list_tree_recursive(d, lines, depth + 1, max_depth)


def delete_file(path: str) -> str:
    """Delete a file. Returns error string on failure."""
    try:
        p = pathlib.Path(path)
        if not p.exists():
            return f"ERROR: File not found: {path}"
        p.unlink()
        return f"OK: Deleted {p.resolve()}"
    except PermissionError:
        return f"ERROR: Permission denied deleting: {path}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def run_shell(cmd: str, cwd: str = None, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Execute a shell command. Captures stdout, stderr, and return code."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        if result.returncode != 0:
            output = f"ERROR (exit code {result.returncode}): {output}"
        return output
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {timeout}s"
    except FileNotFoundError:
        return f"ERROR: Command not found: {cmd.split()[0] if cmd else ''}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def search_in_files(pattern: str, path: str, glob_pattern: str = "*") -> str:
    """Search for pattern in files matching glob. Returns matches."""
    try:
        root = pathlib.Path(path)
        if not root.exists():
            return f"ERROR: Path not found: {path}"

        matches = []
        for file_path in root.rglob(glob_pattern):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    for i, line in enumerate(content.splitlines(), 1):
                        if pattern in line:
                            rel = file_path.relative_to(root)
                            matches.append(f"{rel}:{i}: {line.strip()}")
                except (PermissionError, UnicodeDecodeError):
                    continue

        if not matches:
            return f"No matches found for '{pattern}' in {path}/{glob_pattern}"
        return f"Found {len(matches)} match(es):\n" + "\n".join(matches[:100])  # cap at 100
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def patch_file(path: str, old: str, new: str) -> str:
    """Replace first occurrence of old with new in file. Returns status."""
    try:
        p = pathlib.Path(path)
        if not p.exists():
            return f"ERROR: File not found: {path}"

        content = p.read_text(encoding="utf-8")
        if old not in content:
            return f"ERROR: Pattern not found in file: '{old}'"

        new_content = content.replace(old, new, 1)
        p.write_text(new_content, encoding="utf-8")
        return f"OK: Patched {p.resolve()} (1 replacement)"
    except PermissionError:
        return f"ERROR: Permission denied patching: {path}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOLS: Dict[str, Any] = {
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "list_tree": list_tree,
    "delete_file": delete_file,
    "run_shell": run_shell,
    "search_in_files": search_in_files,
    "patch_file": patch_file,
}


# ---------------------------------------------------------------------------
# JSON schemas for LLM function calling
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Returns the file content as a string, or an error message if the file cannot be read.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to read."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new file or overwrite an existing file with the given content. Creates parent directories automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to write."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "Append text to the end of an existing file. Creates the file if it doesn't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to append to."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to append."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tree",
            "description": "Recursively list the directory tree starting at the given path. Returns a formatted string showing files and directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to list."
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to recurse (default: 10).",
                        "default": 10
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file from the filesystem. Returns a success or error message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to delete."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell command and return the combined stdout and stderr output. Useful for running tests, installing packages, git operations, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {
                        "type": "string",
                        "description": "The shell command to execute."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Working directory for the command (optional)."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 120)."
                    }
                },
                "required": ["cmd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_files",
            "description": "Search for a text pattern across files matching a glob pattern. Returns matching lines with file paths and line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The text pattern to search for."
                    },
                    "path": {
                        "type": "string",
                        "description": "The root directory to search in."
                    },
                    "glob_pattern": {
                        "type": "string",
                        "description": "Glob pattern for file names (default: '*')."
                    }
                },
                "required": ["pattern", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "patch_file",
            "description": "Replace the first occurrence of a text pattern in a file with new text. Returns a success or error message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to patch."
                    },
                    "old": {
                        "type": "string",
                        "description": "The text to find and replace."
                    },
                    "new": {
                        "type": "string",
                        "description": "The replacement text."
                    }
                },
                "required": ["path", "old", "new"]
            }
        }
    },
]


# ---------------------------------------------------------------------------
# Convenience: call a tool by name with kwargs
# ---------------------------------------------------------------------------

def call_tool(name: str, **kwargs) -> str:
    """Look up a tool by name and call it with the given kwargs."""
    if name not in TOOLS:
        return f"ERROR: Unknown tool: {name}. Available: {list(TOOLS.keys())}"
    fn = TOOLS[name]
    return fn(**kwargs)
