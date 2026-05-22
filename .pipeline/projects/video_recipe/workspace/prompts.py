"""Prompt templates for LLM interactions."""


SYSTEM_PROMPT = """You are a cooking recipe expert. Given video frames and an audio transcript of a cooking video, generate a structured recipe.

Return a JSON object with:
- "title": string — a concise recipe title
- "summary": string — a brief description of the recipe
- "steps": array of objects, each with:
  - "timestamp": number — the timestamp (in seconds) of the frame
  - "description": string — what happens in this step
  - "inferred_tools": array of strings — tools needed for this step
  - "inferred_materials": array of strings — ingredients/materials used in this step

Be precise and practical. Infer tools and materials from the visual and audio context."""


SYSTEM_PROMPT_ENRICHED = """You are a cooking recipe expert. Given video frames and an audio transcript of a cooking video, enrich the recipe with additional metadata.

Return a JSON object with:
- "ingredients": array of strings — all ingredients used
- "equipment": array of strings — all tools/equipment needed
- "difficulty": string — "easy", "medium", or "hard"
- "estimated_time_minutes": integer — estimated total cooking time
- "key_takeaways": array of strings — key tips or insights

Be precise and practical."""


def build_recipe_prompt(frames: list[dict], transcript: str) -> str:
    """Build the user prompt for recipe generation.

    Args:
        frames: List of {"path": str, "timestamp": float} dicts.
        transcript: Audio transcript text.

    Returns:
        Formatted user prompt string.
    """
    frame_info = "\n".join(
        f"- Frame at {f['timestamp']:.1f}s: {f['path']}" for f in frames
    )
    return f"""VIDEO FRAMES:
{frame_info}

AUDIO TRANSCRIPT:
{transcript}

Generate a structured recipe in JSON format."""


def build_enriched_recipe_prompt(frames: list[dict], transcript: str) -> str:
    """Build the user prompt for recipe enrichment.

    Args:
        frames: List of {"path": str, "timestamp": float} dicts.
        transcript: Audio transcript text.

    Returns:
        Formatted user prompt string.
    """
    frame_info = "\n".join(
        f"- Frame at {f['timestamp']:.1f}s: {f['path']}" for f in frames
    )
    return f"""VIDEO FRAMES:
{frame_info}

AUDIO TRANSCRIPT:
{transcript}

Enrich the recipe with additional metadata in JSON format."""


def build_enrichment_prompt(recipe: dict, frames: list[dict], transcript: str) -> str:
    """Build the user prompt for recipe enrichment with recipe context.

    Args:
        recipe: Existing recipe dict with title, summary, steps.
        frames: List of {"path": str, "timestamp": float} dicts.
        transcript: Audio transcript text.

    Returns:
        Formatted user prompt string.
    """
    frame_info = "\n".join(
        f"- Frame at {f['timestamp']:.1f}s: {f['path']}" for f in frames
    )
    return f"""EXISTING RECIPE:
Title: {recipe.get('title', 'Unknown')}
Summary: {recipe.get('summary', 'No summary')}
Steps:
{frame_info}

AUDIO TRANSCRIPT:
{transcript}

Enrich the recipe with additional metadata in JSON format.
Return only the enrichment fields: ingredients, equipment, difficulty, estimated_time_minutes, key_takeaways."""
