"""Alpaca-style prompt formatting for SFT training."""

from __future__ import annotations

from typing import Any


def alpaca_prompt(instruction: str, input_text: str = "") -> str:
    """User/prompt portion (everything before the model response)."""
    instruction = (instruction or "").strip()
    input_text = (input_text or "").strip()
    if input_text:
        return (
            f"### Instruction:\n{instruction}\n\n"
            f"### Input:\n{input_text}\n\n"
            f"### Response:\n"
        )
    return f"### Instruction:\n{instruction}\n\n### Response:\n"


def alpaca_text(instruction: str, input_text: str, output_text: str) -> str:
    """Full training example: prompt + completion."""
    return alpaca_prompt(instruction, input_text) + (output_text or "")


def record_to_text(rec: dict[str, Any]) -> str:
    return alpaca_text(
        str(rec.get("instruction", "")),
        str(rec.get("input", "")),
        str(rec.get("output", "")),
    )
