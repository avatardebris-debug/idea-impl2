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
from typing import Any, Dict, List, Optional

from video_scribe.config import PROVIDER_CLAUDE, PROVIDER_GPT4O, DEFAULT_MAX_WORKERS
from video_scribe.cache import VLMCache

_CINEMATOGRAPHY_PROMPT = """\
You are an expert cinematographer and film analyst. Analyze the provided video frame \
in detail and return a structured JSON response with the following keys:

- "content_summary": A concise 2-3 sentence summary of what is happening in the scene.
- "visual_elements": A list of 5-10 key visual elements (objects, people, colors, composition details).
- "camera_notes": Notes on camera techniques (pan, tilt, zoom, dolly, tracking, angle, etc.).
- "lighting_color_notes": Notes on lighting conditions, color palette, and mood.

Return ONLY valid JSON. Do not include any markdown formatting, code fences, or extra text.
"""

# Global Cache instance
_cache = VLMCache()

def _image_to_base64(image) -> str:
    """Encode a PIL Image as base64 JPEG."""
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def _image_to_bytes(image) -> bytes:
    """Get raw bytes for cache hashing."""
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

class VLMProvider:
    def analyze(self, images: List, api_key: str | None) -> Dict[str, Any]:
        raise NotImplementedError

class OpenAIProvider(VLMProvider):
    def analyze(self, images: List, api_key: str | None) -> Dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")

        client = OpenAI(api_key=api_key) if api_key else OpenAI()
        content_parts: List[Dict[str, Any]] = [{"type": "text", "text": _CINEMATOGRAPHY_PROMPT}]

        for i, img in enumerate(images):
            b64 = _image_to_base64(img)
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"},
            })

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert cinematographer and film analyst. Analyze the provided frames from a single scene and synthesize a unified analysis."},
                {"role": "user", "content": content_parts},
            ],
            max_tokens=1024,
            temperature=0.3,
        )

        return _parse_vlm_response(response.choices[0].message.content)

class AnthropicProvider(VLMProvider):
    def analyze(self, images: List, api_key: str | None) -> Dict[str, Any]:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")

        client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        content_parts: List[Dict[str, Any]] = [{"type": "text", "text": _CINEMATOGRAPHY_PROMPT}]

        for img in images:
            b64 = _image_to_base64(img)
            content_parts.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": b64},
            })

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.3,
            system="You are an expert cinematographer and film analyst. Analyze the provided frames from a single scene and synthesize a unified analysis.",
            messages=[{"role": "user", "content": content_parts}],
        )

        return _parse_vlm_response(response.content[0].text)

class OllamaProvider(VLMProvider):
    def analyze(self, images: List, api_key: str | None) -> Dict[str, Any]:
        try:
            import requests
        except ImportError:
            raise ImportError("requests required for Ollama")
            
        # Simplified integration for Ollama LLAVA or similar local models
        b64_images = [_image_to_base64(img) for img in images]
        payload = {
            "model": "llava",
            "prompt": _CINEMATOGRAPHY_PROMPT,
            "images": b64_images,
            "stream": False
        }
        resp = requests.post("http://localhost:11434/api/generate", json=payload)
        resp.raise_for_status()
        return _parse_vlm_response(resp.json()["response"])


def _get_provider_instance(provider_name: str) -> VLMProvider:
    if provider_name == PROVIDER_GPT4O:
        return OpenAIProvider()
    elif provider_name == PROVIDER_CLAUDE:
        return AnthropicProvider()
    elif provider_name == "ollama":
        return OllamaProvider()
    raise ValueError(f"Unknown provider: {provider_name}")


def analyze_frames(
    images: List,
    provider: str = PROVIDER_GPT4O,
    api_key: str | None = None,
) -> Dict[str, Any]:
    # Cache key based on all frames combined
    combined_bytes = b"".join([_image_to_bytes(img) for img in images])
    
    cached = _cache.get(combined_bytes)
    if cached:
        return cached

    provider_impl = _get_provider_instance(provider)
    result = provider_impl.analyze(images, api_key)
    
    _cache.set(combined_bytes, result)
    return result

def analyze_frame(image, provider: str = PROVIDER_GPT4O, api_key: str | None = None) -> Dict[str, Any]:
    return analyze_frames([image], provider, api_key)

def analyze_scenes_parallel(
    scenes_frames: List[List],
    provider: str = PROVIDER_GPT4O,
    api_key: str | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = [{}] * len(scenes_frames)

    def _analyze_scene(index: int, frames: List) -> tuple:
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
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else lines[1] if len(lines) > 1 else ""
    elif "{" in text and "}" in text:
        text = text[text.find("{"):text.rfind("}")+1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"VLM returned invalid JSON: {e}\nResponse was:\n{text}")

    required_keys = ["content_summary", "visual_elements", "camera_notes", "lighting_color_notes"]
    for key in required_keys:
        if key not in data:
            data[key] = "N/A"

    return data
