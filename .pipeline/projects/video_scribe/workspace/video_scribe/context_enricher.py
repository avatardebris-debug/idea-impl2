"""Cross-scene context enrichment for Video Scribe.

After all scenes are analyzed, runs a second LLM pass (text-only) to generate
transition descriptions between consecutive scenes and a global video summary.
"""

from __future__ import annotations

from typing import Any, Dict, List

from video_scribe.config import PROVIDER_GPT4O, PROVIDER_CLAUDE


_TRANSITION_PROMPT = """\
You are an expert film editor and cinematographer. Given the analysis of consecutive \
scenes from a video, describe the transition between them. Focus on:
- Visual continuity or contrast (color, lighting, composition)
- Camera movement or angle changes
- Narrative or thematic shifts
- Audio or pacing changes (if inferable)

Return ONLY a single paragraph (2-3 sentences) describing the transition. \
Do not include any JSON, markdown, or extra text.
"""

_GLOBAL_SUMMARY_PROMPT = """\
You are an expert film critic and cinematographer. Given the analysis of all scenes \
from a video, write a 2-3 sentence global summary of the entire video. Focus on:
- The overall narrative or visual arc
- Key themes or motifs
- The progression of visual style across scenes

Return ONLY the summary text. Do not include any JSON, markdown, or extra text.
"""


def _get_provider_text(provider: str) -> str:
    """Get the text-only analysis prompt for the given provider."""
    if provider == PROVIDER_GPT4O:
        return _TRANSITION_PROMPT
    elif provider == PROVIDER_CLAUDE:
        return _TRANSITION_PROMPT
    else:
        return _TRANSITION_PROMPT


def enrich_scenes(
    scene_analyses: List[Dict[str, Any]],
    provider: str = PROVIDER_GPT4O,
    api_key: str | None = None,
) -> List[Dict[str, Any]]:
    """Enrich scene analyses with transition descriptions and global summary.

    For each scene (except the last), generates a transition description to the
    next scene. Also generates a global summary of the entire video.

    Args:
        scene_analyses: List of scene analysis dicts from the VLM analyzer.
        provider: VLM provider for the text-only LLM pass.
        api_key: API key. If None, will be loaded from config.

    Returns:
        The same list of scene analysis dicts, now with additional keys:
        - 'transition_to_next': str or None (for the last scene)
        - 'global_summary': str (added to all scenes, same value)
    """
    if not scene_analyses:
        return []

    # Generate transition descriptions
    transitions = []
    for i in range(len(scene_analyses) - 1):
        current = scene_analyses[i]
        next_scene = scene_analyses[i + 1]
        transition = _generate_transition(
            current, next_scene, provider, api_key
        )
        transitions.append(transition)
    # Last scene has no transition
    transitions.append(None)

    # Generate global summary
    global_summary = _generate_global_summary(scene_analyses, provider, api_key)

    # Enrich each scene
    enriched = []
    for i, analysis in enumerate(scene_analyses):
        enriched_scene = dict(analysis)
        enriched_scene["transition_to_next"] = transitions[i]
        enriched_scene["global_summary"] = global_summary
        enriched.append(enriched_scene)

    return enriched


def _generate_transition(
    current: Dict[str, Any],
    next_scene: Dict[str, Any],
    provider: str,
    api_key: str | None,
) -> str:
    """Generate a transition description between two consecutive scenes."""
    current_summary = current.get("content_summary", "Unknown content")
    current_visual = ", ".join(current.get("visual_elements", [])) if isinstance(current.get("visual_elements"), list) else str(current.get("visual_elements", "N/A"))
    current_lighting = current.get("lighting_color_notes", "N/A")

    next_summary = next_scene.get("content_summary", "Unknown content")
    next_visual = ", ".join(next_scene.get("visual_elements", [])) if isinstance(next_scene.get("visual_elements"), list) else str(next_scene.get("visual_elements", "N/A"))
    next_lighting = next_scene.get("lighting_color_notes", "N/A")

    prompt = f"""Scene {current_summary}. Visual elements: {current_visual}. Lighting: {current_lighting}.

Transition to: Scene {next_summary}. Visual elements: {next_visual}. Lighting: {next_lighting}.

Describe the transition between these two scenes."""

    return _call_llm_text(prompt, _TRANSITION_PROMPT, provider, api_key)


def _generate_global_summary(
    scene_analyses: List[Dict[str, Any]],
    provider: str,
    api_key: str | None,
) -> str:
    """Generate a global summary of the entire video from all scene analyses."""
    scene_summaries = []
    for i, analysis in enumerate(scene_analyses):
        summary = analysis.get("content_summary", "Unknown content")
        visual = ", ".join(analysis.get("visual_elements", [])) if isinstance(analysis.get("visual_elements"), list) else str(analysis.get("visual_elements", "N/A"))
        scene_summaries.append(f"Scene {i+1}: {summary}. Visual elements: {visual}.")

    prompt = f"""Analyze the following scene summaries and provide a 2-3 sentence global summary of the entire video:

{chr(10).join(scene_summaries)}"""

    return _call_llm_text(prompt, _GLOBAL_SUMMARY_PROMPT, provider, api_key)


def _call_llm_text(
    user_prompt: str,
    system_prompt: str,
    provider: str,
    api_key: str | None,
) -> str:
    """Call the LLM with a text-only prompt and return the response."""
    if provider == PROVIDER_GPT4O:
        return _call_openai_text(user_prompt, system_prompt, api_key)
    elif provider == PROVIDER_CLAUDE:
        return _call_anthropic_text(user_prompt, system_prompt, api_key)
    else:
        return f"[Unknown provider: {provider}]"


def _call_openai_text(
    user_prompt: str,
    system_prompt: str,
    api_key: str | None,
) -> str:
    """Call OpenAI GPT-4o with a text-only prompt."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package is required. Install with: pip install openai")

    client = OpenAI(api_key=api_key) if api_key else OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=256,
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


def _call_anthropic_text(
    user_prompt: str,
    system_prompt: str,
    api_key: str | None,
) -> str:
    """Call Anthropic Claude with a text-only prompt."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package is required. Install with: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        temperature=0.3,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.content[0].text.strip()
