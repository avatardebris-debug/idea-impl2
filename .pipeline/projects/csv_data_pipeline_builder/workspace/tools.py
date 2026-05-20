"""
tools.py
File-tree tools available to the agent.

Each tool is a plain Python function.
The TOOL_SCHEMAS list describes them in JSON-Schema format for the LLM.
The TOOLS dict maps name → callable for the executor.
"""

from __future__ import annotations
import os
import pathlib
import subprocess
import textwrap

# Root of the agent's writable workspace
AGENT_DIR = pathlib.Path(".agent")


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Read and return the full text content of a file."""
    p = pathlib.Path(path)
    if not p.exists():
        return f"ERROR: File not found: {path}"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories as needed."""
    p = pathlib.Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"OK: Written {len(content)} chars to {path}"
    except Exception as e:
        return f"ERROR writing {path}: {e}"


def append_file(path: str, content: str) -> str:
    """Append content to a file (creates the file if it doesn't exist)."""
    p = pathlib.Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
        return f"OK: Appended to {path}"
    except Exception as e:
        return f"ERROR appending to {path}: {e}"


def list_tree(path: str = ".") -> str:
    """
    Return an indented tree of all files/directories under `path`.
    Hidden directories (starting with .) and __pycache__ are skipped.
    """
    lines = []
    root_path = pathlib.Path(path).resolve()

    for dirpath, dirs, files in os.walk(root_path):
        # Prune hidden + cache dirs
        dirs[:] = sorted(
            d for d in dirs
            if not d.startswith(".") and d != "__pycache__"
        )
        rel = pathlib.Path(dirpath).relative_to(root_path)
        depth = len(rel.parts)
        indent = "  " * depth
        folder_name = pathlib.Path(dirpath).name if depth > 0 else str(root_path)
        lines.append(f"{indent}{folder_name}/")
        for fname in sorted(files):
            lines.append(f"{indent}  {fname}")

    return "\n".join(lines) if lines else "(empty)"


def delete_file(path: str) -> str:
    """Delete a file."""
    p = pathlib.Path(path)
    if not p.exists():
        return f"ERROR: {path} does not exist"
    try:
        p.unlink()
        return f"OK: Deleted {path}"
    except Exception as e:
        return f"ERROR deleting {path}: {e}"


def run_shell(command: str, cwd: str = ".") -> str:
    """
    Run a shell command and return stdout + stderr (truncated to 4000 chars).
    Use with care — the agent should only run safe, read-only commands unless
    explicitly instructed otherwise.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=120,
        )
        out = result.stdout + result.stderr
        if len(out) > 4000:
            out = out[:4000] + "\n...(truncated)"
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out after 120s"
    except Exception as e:
        return f"ERROR: {e}"


def append_memory(fact: str) -> str:
    """Persist an important fact to .agent/memory/facts.md"""
    return append_file(".agent/memory/facts.md", f"\n- {fact}")


def update_tasks(content: str) -> str:
    """Overwrite .agent/tasks.md with the updated task list."""
    return write_file(".agent/tasks.md", content)


def log_decision(decision: str) -> str:
    """Append a decision/rationale entry to .agent/memory/decisions.md"""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n\n## {ts}\n{decision}"
    return append_file(".agent/memory/decisions.md", entry)


def search_in_files(pattern: str, path: str = ".", file_glob: str = "*.py") -> str:
    """Search for a text pattern across files using grep.

    Returns matching lines with file:line context (max 4000 chars).
    Much faster than reading every file sequentially.
    """
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include", file_glob, pattern, path],
            capture_output=True, text=True, timeout=30,
        )
        out = result.stdout
        if len(out) > 4000:
            out = out[:4000] + "\n...(truncated)"
        return out or "(no matches)"
    except FileNotFoundError:
        # grep not available (Windows without Git Bash) — fall back to Python
        matches = []
        import fnmatch
        root = pathlib.Path(path)
        for fp in root.rglob(file_glob):
            if fp.is_file():
                try:
                    for i, line in enumerate(fp.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                        if pattern in line:
                            matches.append(f"{fp}:{i}: {line.strip()}")
                except Exception:
                    continue
        out = "\n".join(matches[:100])
        if len(out) > 4000:
            out = out[:4000] + "\n...(truncated)"
        return out or "(no matches)"
    except subprocess.TimeoutExpired:
        return "ERROR: search timed out after 30s"
    except Exception as e:
        return f"ERROR: {e}"


def patch_file(path: str, old: str, new: str) -> str:
    """Replace the first occurrence of `old` with `new` in a file.

    This is safer than write_file for small edits — it won't truncate
    the rest of the file. Returns an error if `old` is not found.
    """
    p = pathlib.Path(path)
    if not p.exists():
        return f"ERROR: File not found: {path}"
    try:
        content = p.read_text(encoding="utf-8")
        if old not in content:
            return f"ERROR: pattern not found in {path}"
        updated = content.replace(old, new, 1)
        p.write_text(updated, encoding="utf-8")
        return f"OK: Patched {path} ({len(old)} chars → {len(new)} chars)"
    except Exception as e:
        return f"ERROR patching {path}: {e}"


# ---------------------------------------------------------------------------
# Tool schemas (JSON Schema format — works with OpenAI & Claude)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read the full content of a file from disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read."},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write (or overwrite) a file with the given content. Creates parent directories automatically.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Destination file path."},
                "content": {"type": "string", "description": "Full content to write."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "append_file",
        "description": "Append content to an existing file (creates it if missing).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path."},
                "content": {"type": "string", "description": "Text to append."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_tree",
        "description": "List all files and directories in a tree view. Defaults to the current directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Root path to list. Defaults to '.'.", "default": "."},
            },
        },
    },
    {
        "name": "delete_file",
        "description": "Delete a file from disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path of the file to delete."},
            },
            "required": ["path"],
        },
    },
    {
        "name": "run_shell",
        "description": "Run a shell command and return the output. Timeout: 120s.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute."},
                "cwd": {"type": "string", "description": "Working directory. Defaults to '.'.", "default": "."},
            },
            "required": ["command"],
        },
    },
    {
        "name": "append_memory",
        "description": "Save an important fact to persistent memory (.agent/memory/facts.md).",
        "parameters": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "The fact to remember."},
            },
            "required": ["fact"],
        },
    },
    {
        "name": "update_tasks",
        "description": "Overwrite the agent task list (.agent/tasks.md) with updated content. Use [ ] for pending, [x] for done.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Full markdown task list content."},
            },
            "required": ["content"],
        },
    },
    {
        "name": "log_decision",
        "description": "Append a timestamped decision or rationale to .agent/memory/decisions.md.",
        "parameters": {
            "type": "object",
            "properties": {
                "decision": {"type": "string", "description": "The decision and its reasoning."},
            },
            "required": ["decision"],
        },
    },
    {
        "name": "search_in_files",
        "description": "Search for a text pattern across files (like grep). Returns matching lines with file:line context.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Text to search for."},
                "path": {"type": "string", "description": "Directory to search in. Defaults to '.'.", "default": "."},
                "file_glob": {"type": "string", "description": "File pattern to include (e.g. '*.py', '*.md'). Defaults to '*.py'.", "default": "*.py"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "patch_file",
        "description": "Replace the first occurrence of 'old' text with 'new' text in a file. Safer than write_file for small edits — won't truncate the rest of the file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to patch."},
                "old": {"type": "string", "description": "Exact text to find and replace (first occurrence only)."},
                "new": {"type": "string", "description": "Replacement text."},
            },
            "required": ["path", "old", "new"],
        },
    },
]

# Callable registry — used by the agent executor
TOOLS: dict[str, callable] = {
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "list_tree": list_tree,
    "delete_file": delete_file,
    "run_shell": run_shell,
    "append_memory": append_memory,
    "update_tasks": update_tasks,
    "log_decision": log_decision,
    "search_in_files": search_in_files,
    "patch_file": patch_file,
}
