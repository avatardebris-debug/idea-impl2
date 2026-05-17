"""JSON response parser — handles LLM JSON responses with markdown code fences."""

import json


def parse_json_response(content: str) -> dict | None:
    """Parse JSON from LLM response, handling markdown code fences.

    Args:
        content: Raw text content from an LLM response.

    Returns:
        Parsed dict if valid JSON is found, None otherwise.
    """
    content = content.strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first and last fence lines
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON block in the text
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                pass
    return None
