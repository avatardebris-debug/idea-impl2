"""LLM-driven recipe extraction from parsed scene descriptions."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from video_recipe_mu.recipe_parser import ParsedSceneDescription
from video_recipe_mu.schema import RobotRecipeStep


def _load_prompt_template(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
    # Ensure the prompt_name doesn't already have .md extension
    if prompt_name.endswith(".md"):
        prompt_path = os.path.join(prompt_dir, prompt_name)
    else:
        prompt_path = os.path.join(prompt_dir, f"{prompt_name}.md")
    with open(prompt_path, "r") as f:
        return f.read()


def _build_extraction_prompt(parsed: ParsedSceneDescription) -> str:
    """Build the LLM prompt for recipe extraction."""
    template = _load_prompt_template("recipe_extraction.md")

    # Format scenes for the prompt
    scenes_text = ""
    for scene in parsed.scenes:
        scenes_text += f"\n---\nScene {scene.index} (t={scene.time_range[0]:.1f}-{scene.time_range[1]:.1f}s):\n"
        scenes_text += f"Description: {scene.description}\n"
        if scene.visual_elements:
            scenes_text += f"Visual Elements: {', '.join(scene.visual_elements)}\n"
        if scene.camera_notes:
            scenes_text += f"Camera: {scene.camera_notes}\n"
        if scene.lighting_color_notes:
            scenes_text += f"Lighting: {scene.lighting_color_notes}\n"

    prompt = template.replace("{SCENES}", scenes_text)
    if parsed.global_summary:
        prompt = prompt.replace("{GLOBAL_SUMMARY}", parsed.global_summary)
    else:
        prompt = prompt.replace("{GLOBAL_SUMMARY}", "N/A")

    return prompt


def _call_llm(prompt: str, provider: str = "openai") -> str:
    """Call the LLM API to get extraction results.

    In production, this would call OpenAI, Anthropic, etc.
    For testing, this can be mocked.
    """
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content
    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def extract_recipe_from_parsed(
    parsed: ParsedSceneDescription,
    provider: str = "openai",
) -> List[RobotRecipeStep]:
    """Extract robot recipe steps from a parsed scene description.

    Args:
        parsed: Parsed scene description from video_scribe.
        provider: LLM provider to use ("openai" or "anthropic").

    Returns:
        List of RobotRecipeStep dicts.
    """
    prompt = _build_extraction_prompt(parsed)
    raw_response = _call_llm(prompt, provider)

    # Parse JSON from LLM response
    steps = _parse_llm_response(raw_response)
    return steps


def extract_recipe(
    input_path: str,
    provider: str = "openai",
) -> List[RobotRecipeStep]:
    """Extract robot recipe from a video_scribe output file.

    Args:
        input_path: Path to video_scribe JSON or Markdown file.
        provider: LLM provider to use.

    Returns:
        List of RobotRecipeStep dicts.
    """
    from video_recipe_mu.recipe_parser import parse_scene_description

    parsed = parse_scene_description(input_path)
    return extract_recipe_from_parsed(parsed, provider)


def _parse_llm_response(raw_response: str) -> List[RobotRecipeStep]:
    """Parse LLM JSON response into RobotRecipeStep objects.

    Handles cases where the LLM wraps JSON in markdown code blocks.
    """
    # Strip markdown code blocks if present
    json_str = raw_response.strip()
    if json_str.startswith("```"):
        lines = json_str.split("\n")
        # Find the JSON content between ```json and ```
        in_json = False
        json_lines: List[str] = []
        for line in lines:
            if line.strip().startswith("```"):
                if in_json:
                    break
                in_json = True
                continue
            if in_json:
                json_lines.append(line)
        json_str = "\n".join(json_lines)

    # Parse JSON
    data = json.loads(json_str)

    # Handle both list and dict with 'steps' key
    if isinstance(data, dict):
        data = data.get("steps", data.get("recipe", []))

    if not isinstance(data, list):
        raise ValueError(f"Expected list of steps, got {type(data)}")

    # Validate and convert to RobotRecipeStep
    steps: List[RobotRecipeStep] = []
    for i, step_data in enumerate(data):
        step = _validate_step(step_data, i + 1)
        steps.append(step)

    return steps


def _validate_step(step_data: Dict[str, Any], step_num: int) -> RobotRecipeStep:
    """Validate and normalize a single step from LLM response."""
    # Ensure required fields
    if "action" not in step_data:
        raise ValueError(f"Step {step_num} missing 'action' field")
    if "object" not in step_data:
        raise ValueError(f"Step {step_num} missing 'object' field")

    # Normalize xyz_delta
    xyz_delta = step_data.get("xyz_delta", {"x": 0.0, "y": 0.0, "z": 0.0})
    if not isinstance(xyz_delta, dict):
        xyz_delta = {"x": 0.0, "y": 0.0, "z": 0.0}
    xyz_delta = {
        "x": float(xyz_delta.get("x", 0.0)),
        "y": float(xyz_delta.get("y", 0.0)),
        "z": float(xyz_delta.get("z", 0.0)),
    }

    # Normalize preconditions
    preconditions = step_data.get("preconditions", [])
    if isinstance(preconditions, str):
        preconditions = [preconditions]
    preconditions = list(preconditions)

    return RobotRecipeStep(
        step=step_num,
        action=str(step_data["action"]),
        object=str(step_data["object"]),
        xyz_delta=xyz_delta,
        duration_s=float(step_data.get("duration_s", 1.0)),
        preconditions=preconditions,
        success_state=str(step_data.get("success_state", "")),
    )
