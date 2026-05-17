"""Structured prompts for recipe enrichment."""


ENRICH_SYSTEM_PROMPT = """You are a video analysis expert that enriches video-derived recipes with additional metadata.

You will receive:
1. A base recipe with steps, timestamps, inferred tools, and inferred materials.
2. The original video frames (as file paths).
3. The audio transcript of the video.

Your task is to infer and add the following enriched fields:

- **ingredients**: A list of all ingredients/food items visible or mentioned in the video.
- **equipment**: A list of all tools, appliances, or equipment visible or mentioned.
- **difficulty**: One of "easy", "medium", or "hard" — based on the complexity of steps, number of tools, and skill level required.
- **estimated_time_minutes**: An integer estimate of the total time a viewer would need to complete this recipe, based on the video duration and step count.
- **key_takeaways**: A list of 2-5 key insights or tips a viewer should remember from watching this video.

OUTPUT FORMAT:
You MUST output valid JSON only — no markdown, no explanation, no code fences.
The JSON must match this exact schema:
{
  "ingredients": ["string"],
  "equipment": ["string"],
  "difficulty": "easy" | "medium" | "hard",
  "estimated_time_minutes": number,
  "key_takeaways": ["string"]
}

RULES:
1. Infer ingredients from both visual evidence (frames) and audio transcript.
2. Infer equipment from visual evidence — include both tools and appliances.
3. Difficulty should reflect the overall complexity: easy (few steps, basic tools), medium (moderate steps, some specialized tools), hard (many steps, advanced techniques).
4. Estimated time should account for prep, cooking, and cleanup — typically 1.5-2x the video duration.
5. Key takeaways should be practical, actionable insights a viewer would want to remember.
6. Do NOT include any text outside the JSON object."""


def build_enrichment_prompt(recipe: dict, frames: list[dict], transcript: str) -> str:
    """Build the user prompt for recipe enrichment.

    Args:
        recipe: Base recipe dict with title, summary, steps.
        frames: List of {"path": str, "timestamp": float} dicts.
        transcript: Audio transcript text.

    Returns:
        The user-facing prompt string.
    """
    steps_info = ""
    for i, step in enumerate(recipe.get("steps", []), 1):
        ts = step.get("timestamp", 0)
        desc = step.get("description", "")
        tools = step.get("inferred_tools", [])
        materials = step.get("inferred_materials", [])
        steps_info += f"Step {i} (t={ts}s): {desc}"
        if tools:
            steps_info += f" | Tools: {', '.join(tools)}"
        if materials:
            steps_info += f" | Materials: {', '.join(materials)}"
        steps_info += "\n"

    frame_info = ""
    for frame in frames:
        frame_info += f"- Frame at t={frame['timestamp']}s: {frame['path']}\n"

    prompt = f"""You are enriching a recipe derived from a video. Use the base recipe, frames, and transcript to infer additional metadata.

BASE RECIPE:
Title: {recipe.get('title', 'Untitled')}
Summary: {recipe.get('summary', 'No summary')}
Steps:
{steps_info}

VIDEO FRAMES (key frames):
{frame_info}

AUDIO TRANSCRIPT:
{transcript if transcript else "(No audio transcript available)"}

Based on all the above, produce the enriched recipe metadata in the required JSON format.
Infer ingredients from visual and audio evidence.
Infer equipment from visual evidence.
Estimate difficulty based on step complexity.
Estimate time based on video duration and step count.
Provide practical key takeaways.
"""
    return prompt
