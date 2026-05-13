"""
tools.py
Tool registry and function implementations.

Tools are registered as a dict of {name: function} and their schemas
are generated for the LLM interface.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import logging
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Read a file and return its contents."""
    try:
        return pathlib.Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return f"ERROR reading file: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating directories as needed."""
    try:
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"OK: Written {len(content)} chars to {path}"
    except Exception as e:
        return f"ERROR writing file: {e}"


def append_file(path: str, content: str) -> str:
    """Append content to a file."""
    try:
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        current = p.read_text(encoding="utf-8") if p.exists() else ""
        p.write_text(current + content, encoding="utf-8")
        return f"OK: Appended {len(content)} chars to {path}"
    except Exception as e:
        return f"ERROR appending to file: {e}"


def list_dir(path: str = ".") -> str:
    """List files in a directory."""
    try:
        entries = list(pathlib.Path(path).iterdir())
        lines = []
        for e in sorted(entries):
            tag = "/" if e.is_dir() else ""
            lines.append(f"- {e.name}{tag}")
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR listing directory: {e}"


def search_files(pattern: str, path: str = ".") -> str:
    """Search for files matching a glob pattern."""
    try:
        matches = list(pathlib.Path(path).glob(pattern))
        if not matches:
            return "No matches found."
        return "\n".join(str(m) for m in sorted(matches))
    except Exception as e:
        return f"ERROR searching files: {e}"


def run_command(command: str, cwd: str | None = None) -> str:
    """Run a shell command and return stdout/stderr."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        if result.returncode != 0:
            output = f"EXIT CODE {result.returncode}:\n{output}"
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 120s"
    except Exception as e:
        return f"ERROR running command: {e}"


def read_env(key: str) -> str:
    """Read an environment variable."""
    value = os.environ.get(key, "(not set)")
    return f"{key}={value}"


def set_env(key: str, value: str) -> str:
    """Set an environment variable (current process only)."""
    os.environ[key] = value
    return f"OK: Set {key}={value}"


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

TOOLS: dict[str, Any] = {
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "list_dir": list_dir,
    "search_files": search_files,
    "run_command": run_command,
    "read_env": read_env,
    "set_env": set_env,
}

# Tool schemas for LLM interface
TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file, creating it if it doesn't exist.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "append_file",
        "description": "Append content to an existing file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to append to"},
                "content": {"type": "string", "description": "Content to append"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_dir",
        "description": "List files and directories in a path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory to list", "default": "."},
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_files",
        "description": "Search for files matching a glob pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern to search for"},
                "path": {"type": "string", "description": "Directory to search in", "default": "."},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "run_command",
        "description": "Execute a shell command and return its output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "cwd": {"type": "string", "description": "Working directory for the command"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_env",
        "description": "Read the value of an environment variable.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Environment variable name"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "set_env",
        "description": "Set an environment variable for the current process.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Environment variable name"},
                "value": {"type": "string", "description": "Value to set"},
            },
            "required": ["key", "value"],
        },
    },
]
