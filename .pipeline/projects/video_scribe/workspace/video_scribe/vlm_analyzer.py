"""VLM integration for frame analysis.

Encodes key frames as base64, sends them to a VLM (default GPT-4o via OpenAI API)
with a structured cinematography prompt, and parses the text response.

Supports single-frame analysis, multi-frame analysis per scene, and
parallel processing of multiple scenes.
"""

from __future__ import annotations

import base64
import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from video_scribe.config import PROVIDER_CLAUDE, PROVIDER_GPT4O, DEFAULT_MAX_WORKERS


_CINEMATOGRAPHY_PROMPT = """\
You are an expert cinematographer and film analyst. Analyze the provided video frame \
in detail and return a structured JSON response with the following keys:

- "content_summary": A concise 2-3 sentence summary of what is happening in the scene.
- "visual_elements": A list of 5-10 key visual elements (objects, people, colors, composition details).
- "camera_notes": Notes on camera techniques (pan, tilt, zoom, dolly, tracking, angle, etc.).
- "lighting_color_notes": Notes on lighting conditions, color palette, and mood.

Return ONLY valid JSON. Do not include any markdown formatting, code fences, or extra text.
"""


def _image_to_base64(image) -> str:
    """Encode a PIL Image as base64 JPEG."""
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def analyze_frame(
    image,
    provider: str = PROVIDER_GPT4O,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Analyze a single frame using a Vision-Language Model.

    Args:
        image: A PIL Image of the frame to analyze.
        provider: VLM provider ('gpt-4o' or 'claude').
        api_key: API key. If None, will be loaded from config.

    Returns:
        A dict with keys: content_summary, visual_elements, camera_notes, lighting_color_notes.

    Raises:
        ValueError: If the VLM call fails or returns invalid JSON.
    """
    if provider == PROVIDER_GPT4O:
        return _analyze_with_openai(image, api_key)
    elif provider == PROVIDER_CLAUDE:
        return _analyze_with_anthropic(image, api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def analyze_frames(
    images: List,
    provider: str = PROVIDER_GPT4O,
    api_key: str | None = None,
) -> Dict[str, Any]:
    """Analyze multiple frames from a single scene using a Vision-Language Model.

    Sends all frames in a single multimodal API call. The VLM is prompted to
    synthesize a unified analysis across all frames.

    Args:
        images: A list of PIL Images (2-3 frames from the same scene).
        provider: VLM provider ('gpt-4o' or 'claude').
        api_key: API key. If None, will be loaded from config.

    Returns:
        A dict with keys: content_summary, visual_elements, camera_notes,
        lighting_color_notes, per_frame_analysis (list of dicts).

    Raises:
        ValueError: If the VLM call fails or returns invalid JSON.
    """
    if provider == PROVIDER_GPT4O:
        return _analyze_frames_openai(images, api_key)
    elif provider == PROVIDER_CLAUDE:
        return _analyze_frames_anthropic(images, api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _analyze_frames_openai(
    images: List,
    api_key: str | None,
) -> Dict[str, Any]:
    """Analyze multiple frames using OpenAI GPT-4o in a single multimodal call."""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package is required. Install with: pip install openai")

    client = OpenAI(api_key=api_key) if api_key else OpenAI()

    content_parts: List[Dict[str, Any]] = [
        {"type": "text", "text": _CINEMATOGRAPHY_PROMPT}
    ]

    for i, img in enumerate(images):
        b64 = _image_to_base64(img)
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}",
                "detail": "high",
            },
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert cinematographer and film analyst. Analyze the provided frames from a single scene and synthesize a unified analysis.",
            },
            {
                "role": "user",
                "content": content_parts,
            },
        ],
        max_tokens=1024,
        temperature=0.3,
    )

    raw_text = response.choices[0].message.content
    return _parse_vlm_response(raw_text)


def _analyze_frames_anthropic(
    images: List,
    api_key: str | None,
) -> Dict[str, Any]:
    """Analyze multiple frames using Anthropic Claude in a single multimodal call."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("anthropic package is required. Install with: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    content_parts: List[Dict[str, Any]] = [
        {"type": "text", "text": _CINEMATOGRAPHY_PROMPT}
    ]

    for img in images:
        b64 = _image_to_base64(img)
        content_parts.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": b64,
            },
        })

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        temperature=0.3,
        system="You are an expert cinematographer and film analyst. Analyze the provided frames from a single scene and synthesize a unified analysis.",
        messages=[
            {
                "role": "user",
                "content": content_parts,
            },
        ],
    )

    raw_text = response.content[0].text
    return _parse_vlm_response(raw_text)


def analyze_scenes_parallel(
    scenes_frames: List[List],
    provider: str = PROVIDER_GPT4O,
    api_key: str | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> List[Dict[str, Any]]:
    """Analyze multiple scenes in parallel using a thread pool.

    Each scene's frames are analyzed via a single multimodal API call.
    Scenes are processed concurrently to reduce total runtime.

    Args:
        scenes_frames: A list of lists of PIL Images — one inner list per scene.
        provider: VLM provider ('gpt-4o' or 'claude').
        api_key: API key. If None, will be loaded from config.
        max_workers: Maximum number of concurrent threads (default 4).

    Returns:
        A list of analysis dicts, one per scene, in the same order as input.
        Errors for individual scenes are caught and returned as error dicts
        with an 'error' key.
    """
    results: List[Dict[str, Any]] = [{}] * len(scenes_frames)

    def _analyze_scene(index: int, frames: List) -> tuple:
        """Analyze a single scene and return (index, result)."""
        try:
            result = analyze_frames(frames, provider=provider, api_key=api_key)
            return (index, result)
        except Exception as e:
            return (index, {"error": str(e), "content_summary": "Error during analysis", "visual_elements": [], "camera_notes": "N/A", "lighting_color_notes": "N/A"})

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_analyze_scene, i, frames): i
            for i, frames in enumerate(scenes_frames)
        }
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result

    return results


def _parse_vlm_response(raw_text: str) -> Dict[str, Any]:
    """Parse the VLM response text into a structured dict.

    Handles JSON with or without markdown code fences.
    """
    text = raw_text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (code fence markers)
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else lines[1] if len(lines) > 1 else ""

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"VLM returned invalid JSON: {e}\nResponse was:\n{text}"
        )

    # Validate required keys
    required_keys = ["content_summary", "visual_elements", "camera_notes", "lighting_color_notes"]
    for key in required_keys:
        if key not in data:
            data[key] = "N/A"

    return data
