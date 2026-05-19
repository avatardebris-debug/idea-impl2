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


def _parse_json_from_response(text: str) -> dict | list:
    """Extract the first JSON object or array from LLM output.

    Returns a dict or list on success, or {} on failure.
    """
    # Determine whether to look for an array or object first.
    # If '[' appears before '{', try array first.
    first_bracket = text.find("[")
    first_brace   = text.find("{")

    if first_bracket >= 0 and (first_brace < 0 or first_bracket < first_brace):
        # Try JSON array first
        depth = 0
        for i in range(first_bracket, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    try:
                        return json.loads(text[first_bracket:end])
                    except json.JSONDecodeError:
                        break
    else:
        # Try JSON object first
        if first_brace >= 0:
            depth = 0
            for i in range(first_brace, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        try:
                            return json.loads(text[first_brace:end])
                        except json.JSONDecodeError:
                            break

    return {}


def _fallback_extract(text: str, topic: str, fmt: str) -> dict:
    """Simple rule-based extraction when LLM unavailable."""
    import re
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    # Find numbered or bulleted lines as steps
    step_lines = [l for l in lines if re.match(r"^(\d+[\.\):]|[-•*])\s+", l)]
    if not step_lines:
        # Treat each sentence as a step
        step_lines = [s.strip() for s in re.split(r"[.!?]\s+", text) if len(s.strip()) > 0][:20]

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

    fallback_used = False
    if not result:
        result = _fallback_extract(text, topic, fmt)
        fallback_used = True
    elif isinstance(result, dict) and "steps" not in result:
        # Valid JSON but missing required 'steps' key — treat as invalid
        result = _fallback_extract(text, topic, fmt)
        fallback_used = True

    # Ensure required keys exist
    result.setdefault("title", topic or "Extracted Procedure")
    # Topic: user-provided topic overrides LLM's topic; if no user topic, use empty string
    if topic:
        result["topic"] = topic
    else:
        result["topic"] = ""
    result.setdefault("format", fmt)
    result.setdefault("description", "")
    result.setdefault("components", [])
    result.setdefault("tips", [])
    result.setdefault("steps", [])
    result["metadata"] = {
        "source_length": len(text),
        "model": "fallback" if fallback_used else model,
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
