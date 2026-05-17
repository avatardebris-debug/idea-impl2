"""
extractor.py — Core extraction engine.

Given raw source text, uses an LLM to extract a structured sequence of steps.
Works for: recipes, how-to guides, SOPs, tutorials, processes, instructions.

Output schema:
{
  "title": str,
  "topic": str,
  "format": "recipe" | "steps" | "sop",
  "description": str,
  "components": [{"name": str, "quantity": str, "unit": str, "notes": str}],
  "steps": [{"step_number": int, "action": str, "detail": str,
             "duration": str, "tools": [str], "warnings": [str]}],
  "tips": [str],
  "metadata": {"source_length": int, "model": str, "extracted_at": str}
}
"""
from __future__ import annotations
import json
import textwrap
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any

_OLLAMA_HOST = "http://localhost:11434"


def _call_ollama(prompt: str, model: str = "qwen3:6b", timeout: int = 120) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 8192},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{_OLLAMA_HOST}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")).get("response", "").strip()
    except Exception:
        return ""


def _parse_json_from_response(text: str) -> dict:
    """Extract the first JSON object or array from LLM output."""
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


def _fallback_extract(text: str, topic: str, fmt: str) -> dict:
    """Simple rule-based extraction when LLM unavailable."""
    import re
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Find numbered or bulleted lines as steps
    step_lines = [l for l in lines if re.match(r"^(\d+[\.\):]|[-•*])\s+", l)]
    if not step_lines:
        # Treat each sentence as a step
        step_lines = [s.strip() for s in re.split(r"[.!?]\s+", text) if len(s.strip()) > 10][:20]

    steps = []
    for i, line in enumerate(step_lines, 1):
        clean = re.sub(r"^(\d+[\.\):]|[-•*])\s+", "", line)
        steps.append({
            "step_number": i,
            "action": clean[:100],
            "detail": clean,
            "duration": "",
            "tools": [],
            "warnings": [],
        })

    return {
        "title": topic or "Extracted Procedure",
        "topic": topic,
        "format": fmt,
        "description": lines[0] if lines else "",
        "components": [],
        "steps": steps,
        "tips": [],
        "metadata": {
            "source_length": len(text),
            "model": "fallback",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def extract(
    text: str,
    topic: str = "",
    fmt: str = "steps",
    model: str = "qwen3:6b",
) -> dict[str, Any]:
    """Extract a structured step-by-step sequence from raw text.

    Args:
        text:  Source material (article, transcript, how-to text, etc.)
        topic: Optional description of what is being extracted (helps the LLM).
        fmt:   Output format hint: "recipe" | "steps" | "sop"
        model: Ollama model to use.

    Returns:
        Extraction dict matching the schema described in the module docstring.
    """
    if not text or not text.strip():
        return _fallback_extract("", topic, fmt)

    fmt_desc = {
        "recipe": "a cooking recipe with ingredients list and ordered steps",
        "steps":  "an ordered sequence of steps or instructions",
        "sop":    "a Standard Operating Procedure with numbered steps and notes",
    }.get(fmt, "an ordered sequence of steps")

    prompt = textwrap.dedent(f"""
        Extract {fmt_desc} from the following source text.
        Topic: {topic or 'infer from the text'}

        Return ONLY a valid JSON object with this exact schema:
        {{
          "title": "concise title",
          "topic": "topic description",
          "format": "{fmt}",
          "description": "one sentence overview",
          "components": [
            {{"name": "ingredient/component", "quantity": "amount", "unit": "unit", "notes": "optional note"}}
          ],
          "steps": [
            {{"step_number": 1, "action": "short verb phrase", "detail": "full description",
              "duration": "time if applicable", "tools": ["tool1"], "warnings": ["warning if any"]}}
          ],
          "tips": ["tip1", "tip2"]
        }}

        SOURCE TEXT:
        {text[:4000]}

        JSON:
    """).strip()

    response = _call_ollama(prompt, model=model, timeout=180)
    result = _parse_json_from_response(response)

    if not result or "steps" not in result:
        result = _fallback_extract(text, topic, fmt)

    # Ensure required keys exist
    result.setdefault("title", topic or "Extracted Procedure")
    result.setdefault("topic", topic)
    result.setdefault("format", fmt)
    result.setdefault("description", "")
    result.setdefault("components", [])
    result.setdefault("tips", [])
    result.setdefault("steps", [])
    result["metadata"] = {
        "source_length": len(text),
        "model": model,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    # Normalise step numbers
    for i, step in enumerate(result["steps"], 1):
        step["step_number"] = i
        step.setdefault("action", "")
        step.setdefault("detail", step.get("action", ""))
        step.setdefault("duration", "")
        step.setdefault("tools", [])
        step.setdefault("warnings", [])

    return result
