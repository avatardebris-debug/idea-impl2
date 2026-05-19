"""Prompt Template System.

Loads .md templates from the *prompts/* directory and fills placeholders
with context from SOP execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .config import get_prompts_dir
from .sop_schema import SOP


# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------

def load_prompt_template(template_name: str, prompts_dir: Path | None = None) -> str:
    """Load a prompt template file (extension .md is appended automatically)."""
    prompts_dir = prompts_dir or get_prompts_dir()
    path = prompts_dir / f"{template_name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Template filling
# ---------------------------------------------------------------------------

def fill_prompt(template: str, context: Dict[str, Any]) -> str:
    """Replace ``{{key}}`` placeholders in *template* with *context* values."""
    result = template
    for key, value in context.items():
        placeholder = "{{" + key + "}}"
        if isinstance(value, (dict, list)):
            value = json.dumps(value, indent=2, ensure_ascii=False)
        result = result.replace(placeholder, str(value))
    return result


# ---------------------------------------------------------------------------
# Step prompt builder
# ---------------------------------------------------------------------------

def build_step_prompt(
    sop: SOP,
    step_index: int,
    input_data: Dict[str, Any],
    step_outputs: List[Dict[str, Any]],
    prompts_dir: Path | None = None,
) -> str:
    """Build the full prompt string for a given SOP step.

    Args:
        sop:          Validated SOP model.
        step_index:   0-based index into ``sop.steps``.
        input_data:   User-provided input data (validated).
        step_outputs:  Outputs from previous steps (``step_index`` entries
                       when called for step ``step_index``).
        prompts_dir:  Override the default prompts directory.

    Returns:
        A fully filled prompt string ready for LLM consumption.
    """
    step = sop.steps[step_index]
    template_name = step.prompt_template or "default_step"

    template = load_prompt_template(template_name, prompts_dir)

    # Build context dict
    previous_output = step_outputs[step_index - 1].get("raw", "N/A") if step_index > 0 else "N/A"

    context = {
        "step_name": step.name,
        "step_description": step.description,
        "input_context": json.dumps(input_data, indent=2, ensure_ascii=False),
        "previous_output": previous_output,
        "output_format": sop.output_format or "N/A",
    }

    return fill_prompt(template, context)
