"""
pipeline/finetune_collector.py
Fine-tuning dataset collector for the idea pipeline.

Captures clean (instruction, output) pairs every time a phase passes review
without fix cycles. These become SFT training examples for a future executor
model that makes fewer filepath/syntax errors.

Dataset format (Alpaca-style JSONL, compatible with most fine-tuning frameworks):
    {
        "instruction": "<phase spec + full task list>",
        "input":       "<project context: master plan summary, phase goal>",
        "output":      "<final code files as unified diff or concatenated blocks>",
        "metadata": {
            "project": "<slug>",
            "phase":   <int>,
            "fix_cycles": <int>,      # 0 = clean pass, higher = less desirable
            "model":   "<model used>",
            "tokens":  <int>,
            "collected_at": "<iso timestamp>"
        }
    }

High-quality pairs (fix_cycles=0) are the most valuable training signal.
The collector tags every pair with fix_cycles so you can filter later.

Usage:
    from pipeline.finetune_collector import collect_phase_pair
    collect_phase_pair(
        project_dir=self._project_dir,
        phase_num=phase_num,
        fix_cycles=review_result.get("retry_count", 0),
        model=self.model,
        tokens=result.tokens_used,
    )

Called from reviewer.py when a phase reaches phase_N_reviewed status.
"""
from __future__ import annotations

import json
import pathlib
import re
import time
from datetime import datetime, timezone
from typing import Any

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
from pipeline.pipeline_config import PIPELINE_DIR as _PIPELINE_DIR_CFG
_DATASET_DIR  = _PIPELINE_DIR_CFG / "finetune"
_DATASET_FILE = _DATASET_DIR / "dataset.jsonl"
_STATS_FILE   = _DATASET_DIR / "stats.json"

# Max chars per code block to keep dataset manageable
_MAX_CODE_CHARS   = 16_000
_MAX_CONTEXT_CHARS = 4_000


def collect_phase_pair(
    project_dir: pathlib.Path,
    phase_num: int,
    fix_cycles: int = 0,
    model: str = "",
    tokens: int = 0,
    files_written: list[str] | None = None,
) -> bool:
    """
    Capture a (instruction, output) training pair for this completed phase.

    Args:
        project_dir:  Absolute path to .pipeline/projects/<slug>/
        phase_num:    Phase number just completed (1-indexed)
        fix_cycles:   Number of reviewer→executor retry loops before PASS
                      (0 = clean first-pass, most valuable)
        model:        Model that produced this output
        tokens:       Tokens used in final execution
        files_written: List of files written during this phase

    Returns:
        True if a pair was successfully written, False otherwise.
    """
    try:
        slug = project_dir.name

        # --- Read instruction: phase spec + task list ---
        spec_path  = project_dir / f"phases/phase_{phase_num}/spec.md"
        tasks_path = project_dir / f"phases/phase_{phase_num}/tasks.md"
        spec  = spec_path.read_text(encoding="utf-8")  if spec_path.exists()  else ""
        tasks = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else ""

        if not tasks.strip():
            return False  # No task list = nothing meaningful to train on

        instruction = _build_instruction(spec, tasks)

        # --- Read input: project context (master plan summary) ---
        master_plan_path = project_dir / "master_plan.md"
        master_plan = ""
        if master_plan_path.exists():
            master_plan = master_plan_path.read_text(encoding="utf-8")[:_MAX_CONTEXT_CHARS]

        idea_state_path = project_dir / "state" / "current_idea.json"
        idea_title = ""
        if idea_state_path.exists():
            try:
                state = json.loads(idea_state_path.read_text(encoding="utf-8"))
                idea_title = state.get("title", "")
            except Exception:
                pass

        context = _build_context(idea_title, master_plan, phase_num)

        # --- Read output: all workspace files written this phase ---
        workspace_path = project_dir / "workspace"
        output = _collect_workspace_output(workspace_path, phase_num, tasks_path, files_written)

        if not output.strip():
            return False  # No code = nothing to learn from

        # --- Assemble and write record ---
        record: dict[str, Any] = {
            "instruction": instruction,
            "input": context,
            "output": output,
            "metadata": {
                "project": slug,
                "phase": phase_num,
                "fix_cycles": fix_cycles,
                "model": model,
                "tokens": tokens,
                "quality": "high" if fix_cycles == 0 else ("medium" if fix_cycles <= 2 else "low"),
                "collected_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        _DATASET_DIR.mkdir(parents=True, exist_ok=True)
        with open(_DATASET_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        _update_stats(fix_cycles)
        return True

    except Exception:
        return False  # Never crash the pipeline over data collection


def get_dataset_stats() -> dict:
    """Return current dataset statistics."""
    try:
        if _STATS_FILE.exists():
            return json.loads(_STATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"total": 0, "high_quality": 0, "medium_quality": 0, "low_quality": 0}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_instruction(spec: str, tasks: str) -> str:
    """Build the instruction string from spec and task list."""
    parts = []
    if spec.strip():
        parts.append(f"## Phase Specification\n{spec.strip()[:2000]}")
    if tasks.strip():
        parts.append(f"## Implementation Tasks\n{tasks.strip()[:3000]}")
    parts.append(
        "## Your Task\n"
        "Implement all tasks listed above completely and correctly. "
        "Write production-quality code with proper error handling. "
        "Use the exact file paths specified. "
        "Return all files in the format:\n"
        "```\n# FILE: path/to/file.py\n<code>\n```"
    )
    return "\n\n".join(parts)


def _build_context(title: str, master_plan: str, phase_num: int) -> str:
    """Build the input context string."""
    parts = []
    if title:
        parts.append(f"Project: {title}")
    parts.append(f"Current phase: {phase_num}")
    if master_plan:
        # Take just the first section of the master plan (goal + architecture)
        summary = master_plan[:_MAX_CONTEXT_CHARS].split("##")[0].strip()
        if summary:
            parts.append(f"Project overview:\n{summary}")
    return "\n".join(parts)


def _collect_workspace_output(
    workspace_path: pathlib.Path,
    phase_num: int,
    tasks_path: pathlib.Path,
    files_written: list[str] | None = None,
) -> str:
    """
    Collect all code files written for this phase as a structured output.

    Strategy: read the task list to find which files were supposed to be written,
    then collect those files from the workspace. Falls back to all .py files
    if we can't parse the task list.
    """
    if not workspace_path.exists():
        return ""

    # Target files to collect: prioritize actual files_written, then fallback to expected_files
    targets: list[str] = []
    if files_written:
        targets.extend(files_written)

    # Try to parse expected files from task list
    expected_files: list[str] = []
    if tasks_path.exists():
        tasks_content = tasks_path.read_text(encoding="utf-8")
        # Match file paths in tasks: backtick paths, quoted paths, or bare .py/.ts/.js paths
        file_patterns = re.findall(
            r'`([^`]+\.[a-z]{1,5})`|"([^"]+\.[a-z]{1,5})"'
            r"|(?:^|\s)([\w/.-]+\.(?:py|ts|js|tsx|jsx|json|yaml|yml|toml|sh|md))\b",
            tasks_content,
            re.MULTILINE,
        )
        for groups in file_patterns:
            for g in groups:
                if g and "/" in g or g.endswith((".py", ".ts", ".js", ".tsx", ".jsx")):
                    expected_files.append(g.strip())

    for f in expected_files:
        if f not in targets:
            targets.append(f)

    # Collect files — prefer expected, fall back to all code files
    code_extensions = {".py", ".ts", ".js", ".tsx", ".jsx", ".json", ".yaml",
                       ".yml", ".toml", ".sh", ".sql", ".css", ".html", ".md"}
    collected: list[tuple[str, str]] = []
    total_chars = 0

    def _add_file(fp: pathlib.Path) -> bool:
        nonlocal total_chars
        if total_chars >= _MAX_CODE_CHARS:
            return False
        if fp.suffix not in code_extensions:
            return False
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
            rel = str(fp.relative_to(workspace_path))
            snippet = content[:(_MAX_CODE_CHARS - total_chars)]
            collected.append((rel, snippet))
            total_chars += len(snippet)
            return True
        except Exception:
            return False

    # First pass: prioritized targets (actual files_written + expected_files)
    for rel_path in targets:
        fp = workspace_path / rel_path
        if fp.exists():
            _add_file(fp)

    # Second pass: fall back to scanning all code files ONLY if we collected nothing so far
    if not collected and total_chars < _MAX_CODE_CHARS:
        for fp in sorted(workspace_path.rglob("*")):
            if fp.is_file() and fp.suffix in code_extensions:
                rel = str(fp.relative_to(workspace_path))
                if not any(r == rel for r, _ in collected):
                    if not _add_file(fp):
                        break

    if not collected:
        return ""

    # Format as structured file blocks (easy to parse during fine-tuning)
    blocks = []
    for rel, content in collected:
        blocks.append(f"# FILE: {rel}\n{content}")
    return "\n\n".join(blocks)


def _update_stats(fix_cycles: int) -> None:
    """Update rolling stats file."""
    try:
        stats = get_dataset_stats()
        stats["total"] = stats.get("total", 0) + 1
        quality = "high" if fix_cycles == 0 else ("medium" if fix_cycles <= 2 else "low")
        stats[f"{quality}_quality"] = stats.get(f"{quality}_quality", 0) + 1
        stats["last_updated"] = datetime.now(timezone.utc).isoformat()
        _STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    except Exception:
        pass
