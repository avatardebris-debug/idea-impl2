"""Recipe enrichment module."""

import json
import os
from typing import Any

from openai import OpenAI

from video_recipe.prompts import SYSTEM_PROMPT_ENRICHED
from video_recipe.enricher_prompts import build_enrichment_prompt


class EnrichmentError(Exception):
    """Raised when recipe enrichment fails."""
    pass


def _parse_enrichment_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM enrichment response.

    Handles JSON wrapped in markdown code fences.

    Args:
        response_text: Raw text response from the LLM.

    Returns:
        Parsed enrichment dict with ingredients, equipment, difficulty,
        estimated_time_minutes, and key_takeaways.

    Raises:
        EnrichmentError: If the response is invalid or missing required fields.
    """
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise EnrichmentError(f"Failed to parse enrichment response as JSON: {e}")

    for field in ("ingredients", "equipment", "difficulty", "estimated_time_minutes", "key_takeaways"):
        if field not in data:
            raise EnrichmentError(f"Missing required field in enrichment response: {field}")

    if data["difficulty"] not in ("easy", "medium", "hard"):
        raise EnrichmentError(f"Invalid difficulty value: {data['difficulty']}")

    if not isinstance(data["estimated_time_minutes"], int):
        raise EnrichmentError("estimated_time_minutes must be an integer")

    # Add computed fields
    data["total_steps"] = data.get("total_steps", 0)
    data["avg_step_duration"] = data.get("avg_step_duration", 0)

    return data


def enrich_recipe(recipe: dict[str, Any], frames: list[dict[str, Any]], transcript: str) -> dict[str, Any]:
    """Enrich a recipe with ingredients, equipment, difficulty, etc.

    Args:
        recipe: Recipe dict with title, summary, and steps.
        frames: List of frame dicts with 'path' and 'timestamp'.
        transcript: Audio transcript text.

    Returns:
        Enriched recipe dict with ingredients, equipment, difficulty,
        estimated_time_minutes, and key_takeaways added.

    Raises:
        EnrichmentError: If enrichment fails.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnrichmentError("No OpenAI API key found. Set OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=api_key)

    user_prompt = build_enrichment_prompt(recipe, frames, transcript)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_ENRICHED},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        raise EnrichmentError(f"LLM API call failed: {e}")

    content = response.choices[0].message.content
    if not content:
        raise EnrichmentError("LLM returned an empty response.")

    enriched = _parse_enrichment_response(content)

    # Merge enriched data into original recipe
    result = recipe.copy()
    result["ingredients"] = enriched.get("ingredients", [])
    result["equipment"] = enriched.get("equipment", [])
    result["difficulty"] = enriched.get("difficulty", "medium")
    result["estimated_time_minutes"] = enriched.get("estimated_time_minutes", 0)
    result["key_takeaways"] = enriched.get("key_takeaways", [])

    return result
