"""
pipeline/corpus_continuation.py
Split workspace code into chained Alpaca continuation records (no hard truncation).

Record 1: instruction + input → output chunk 1
Record 2+: input = prior output tail + "continue" → output chunk N
"""

from __future__ import annotations

import pathlib
import re
import uuid
from typing import Any

# Marker reserved in continuation inputs (do not split across this token)
CONTINUE_MARKER = "continue"
CONTINUE_INSTRUCTION = (
    "Continue producing the remaining project files from where the prior segment ended. "
    "Output only the next segment; do not repeat files already fully emitted."
)

DEFAULT_MAX_CHARS_PER_OUTPUT = 12_000
DEFAULT_MAX_CHARS_PER_INPUT_CONTINUE = 2_000
# Reserve space for marker + framing in continuation input
_CONTINUE_INPUT_OVERHEAD = 80


def format_workspace_block(files: dict[str, str]) -> str:
    """Format workspace files as structured markdown code blocks (no truncation)."""
    parts: list[str] = []
    for rel, code in files.items():
        parts.append(f"### {rel}\n```python\n{code}\n```\n")
    return "\n".join(parts)


def collect_workspace_files(
    workspace: pathlib.Path,
    *,
    extensions: tuple[str, ...] = (".py",),
) -> dict[str, str]:
    """Return {relative_path: content} for all matching files under workspace."""
    files: dict[str, str] = {}
    if not workspace.exists():
        return files
    for fp in sorted(workspace.rglob("*")):
        if not fp.is_file() or fp.suffix not in extensions:
            continue
        if "__pycache__" in fp.parts:
            continue
        rel = fp.relative_to(workspace).as_posix()
        try:
            files[rel] = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return files


def _split_text_into_chunks(text: str, max_chars: int) -> list[str]:
    """
    Split text into chunks <= max_chars, preferring file boundaries (### headers).
    Falls back to line splits, then hard character splits for oversized segments.
    """
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Split on file headers when present
    if "### " in text:
        segments = re.split(r"(?=^### )", text, flags=re.MULTILINE)
        segments = [s for s in segments if s.strip()]
    else:
        segments = [text]

    chunks: list[str] = []
    buf = ""

    def _flush() -> None:
        nonlocal buf
        if buf.strip():
            chunks.append(buf)
        buf = ""

    for seg in segments:
        if len(seg) > max_chars:
            _flush()
            chunks.extend(_split_by_lines(seg, max_chars))
            continue
        candidate = buf + seg if buf else seg
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            _flush()
            buf = seg
    _flush()
    return chunks if chunks else [text[:max_chars]]


def _split_by_lines(text: str, max_chars: int) -> list[str]:
    """Split a long segment on newlines, then by characters if needed."""
    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    buf = ""
    for line in lines:
        if len(line) > max_chars:
            if buf:
                chunks.append(buf)
                buf = ""
            for i in range(0, len(line), max_chars):
                chunks.append(line[i : i + max_chars])
            continue
        if len(buf) + len(line) > max_chars:
            chunks.append(buf)
            buf = line
        else:
            buf += line
    if buf:
        chunks.append(buf)
    return chunks


def _continuation_input(tail: str, part_index: int, total_parts: int) -> str:
    """Build continuation input: prior tail + continue marker + lightweight metadata."""
    meta = f"[part {part_index} of {total_parts}]"
    return f"{tail.rstrip()}\n\n{CONTINUE_MARKER}\n{meta}\n"


def _make_record_id(base_id: str, part_index: int, total_parts: int) -> str:
    return f"{base_id}__p{part_index}of{total_parts}"


def chunk_workspace_to_records(
    workspace: pathlib.Path | dict[str, str],
    instruction: str,
    input: str = "",
    max_chars_per_output: int = DEFAULT_MAX_CHARS_PER_OUTPUT,
    max_chars_per_input_continue: int = DEFAULT_MAX_CHARS_PER_INPUT_CONTINUE,
    *,
    sequence_id: str | None = None,
    source_slug: str = "",
    granularity: str = "task",
    base_id: str = "",
    enricher_tags: list[str] | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Split workspace code into chained Alpaca records without dropping content.

    Args:
        workspace: Project workspace path or pre-collected {rel_path: content}.
        instruction: Full task/phase instruction (record 1 only uses this verbatim).
        input: Optional context for record 1 (master plan snippet, etc.).
        max_chars_per_output: Target max characters per output chunk.
        max_chars_per_input_continue: Max prior-output tail in continuation inputs.
        sequence_id: Shared ID across all parts (generated if omitted).
        source_slug: Project slug for metadata.
        granularity: task | phase | project
        base_id: Prefix for per-record ids (defaults to sequence_id).
        enricher_tags: Tags applied by enricher pipeline stage.
        extra_fields: Merged into every record (quality_label, model, etc.).

    Returns:
        List of Alpaca dicts with continuation metadata.
    """
    if isinstance(workspace, pathlib.Path):
        files = collect_workspace_files(workspace)
    else:
        files = dict(workspace)

    full_block = format_workspace_block(files)
    if not full_block.strip():
        return []

    output_chunks = _split_text_into_chunks(full_block, max_chars_per_output)
    total_parts = len(output_chunks)
    seq_id = sequence_id or str(uuid.uuid4())
    id_base = base_id or seq_id
    tags = list(enricher_tags or [])
    shared = dict(extra_fields or {})

    tail_budget = max(
        200,
        max_chars_per_input_continue - _CONTINUE_INPUT_OVERHEAD - len(CONTINUE_MARKER),
    )

    records: list[dict[str, Any]] = []
    prev_output = ""

    for idx, chunk in enumerate(output_chunks):
        part_index = idx + 1  # 1-based for trainers/humans
        rec_id = _make_record_id(id_base, part_index, total_parts)

        if idx == 0:
            rec_instruction = instruction
            rec_input = input
        else:
            rec_instruction = CONTINUE_INSTRUCTION
            tail = prev_output[-tail_budget:] if prev_output else ""
            rec_input = _continuation_input(tail, part_index, total_parts)

        record: dict[str, Any] = {
            "id": rec_id,
            "instruction": rec_instruction,
            "input": rec_input,
            "output": chunk,
            "sequence_id": seq_id,
            "part_index": part_index,
            "total_parts": total_parts,
            "source_slug": source_slug,
            "granularity": granularity,
            "enricher_tags": tags,
            "is_continuation": idx > 0,
        }
        record.update(shared)
        records.append(record)
        prev_output = chunk

    return records


def records_from_code_block(
    code_block: str,
    instruction: str,
    input: str = "",
    *,
    max_chars_per_output: int = DEFAULT_MAX_CHARS_PER_OUTPUT,
    max_chars_per_input_continue: int = DEFAULT_MAX_CHARS_PER_INPUT_CONTINUE,
    sequence_id: str | None = None,
    source_slug: str = "",
    granularity: str = "task",
    base_id: str = "",
    enricher_tags: list[str] | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Like chunk_workspace_to_records but accepts a pre-formatted code block string."""
    if not code_block.strip():
        return []

    output_chunks = _split_text_into_chunks(code_block, max_chars_per_output)
    total_parts = len(output_chunks)
    seq_id = sequence_id or str(uuid.uuid4())
    id_base = base_id or seq_id
    tags = list(enricher_tags or [])
    shared = dict(extra_fields or {})
    tail_budget = max(
        200,
        max_chars_per_input_continue - _CONTINUE_INPUT_OVERHEAD - len(CONTINUE_MARKER),
    )

    records: list[dict[str, Any]] = []
    prev_output = ""

    for idx, chunk in enumerate(output_chunks):
        part_index = idx + 1
        rec_id = _make_record_id(id_base, part_index, total_parts)

        if idx == 0:
            rec_instruction = instruction
            rec_input = input
        else:
            rec_instruction = CONTINUE_INSTRUCTION
            tail = prev_output[-tail_budget:] if prev_output else ""
            rec_input = _continuation_input(tail, part_index, total_parts)

        record: dict[str, Any] = {
            "id": rec_id,
            "instruction": rec_instruction,
            "input": rec_input,
            "output": chunk,
            "sequence_id": seq_id,
            "part_index": part_index,
            "total_parts": total_parts,
            "source_slug": source_slug,
            "granularity": granularity,
            "enricher_tags": tags,
            "is_continuation": idx > 0,
        }
        record.update(shared)
        records.append(record)
        prev_output = chunk

    return records
