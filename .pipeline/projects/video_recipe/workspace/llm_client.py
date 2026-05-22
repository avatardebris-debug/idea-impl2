"""LLM client for recipe generation."""

import json
import os
from typing import Any

from openai import OpenAI

from video_recipe.prompts import SYSTEM_PROMPT, build_recipe_prompt


class LLMClientError(Exception):
    """Raised when LLM client encounters an error."""
    pass


def _get_api_key() -> str | None:
    """Get API key from environment."""
    return os.environ.get("OPENAI_API_KEY")


def _parse_recipe_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM response into a recipe dict.

    Handles JSON wrapped in markdown code fences.

    Args:
        response_text: Raw text response from the LLM.

    Returns:
        Parsed recipe dict.

    Raises:
        LLMClientError: If the response is invalid or missing required fields.
    """
    # Strip markdown code fences if present
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        lines = lines[1:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMClientError(f"Failed to parse LLM response as JSON: {e}")

    # Validate required fields
    for field in ("title", "summary", "steps"):
        if field not in data:
            raise LLMClientError(f"Missing required field in recipe response: {field}")

    if not isinstance(data["steps"], list):
        raise LLMClientError("steps must be a list")

    return data


def generate_recipe(frames: list[dict], transcript: str) -> dict[str, Any]:
    """Generate a recipe from video frames and transcript.

    Args:
        frames: List of {"path": str, "timestamp": float} dicts.
        transcript: Audio transcript text.

    Returns:
        Recipe dict with title, summary, and steps.

    Raises:
        LLMClientError: If API key is missing or the LLM call fails.
    """
    api_key = _get_api_key()
    if not api_key:
        raise LLMClientError("No OpenAI API key found. Set OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=api_key)

    user_prompt = build_recipe_prompt(frames, transcript)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        raise LLMClientError(f"LLM API call failed: {e}")

    content = response.choices[0].message.content
    if not content:
        raise LLMClientError("LLM returned an empty response.")

    return _parse_recipe_response(content)
