"""
batch_runner.py — Process multiple podcast episodes in sequence.

Provides a high-level pipeline:
    batch_run(episodes, **kwargs) -> list[dict]

Each episode can be:
    - a path to an audio/video file
    - a dict with keys: "path" (str), "text" (str, optional), "title" (str, optional)

Returns a list of extraction results, one per episode.
"""
from __future__ import annotations
import json
import pathlib
import sys
from typing import Any, Dict, List, Optional, Union

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from podcast.transcriber import transcribe, get_segments
from podcast.extractor import extract_lessons
from podcast.formatter import to_markdown, to_plain, to_json


EpisodeInput = Union[str, Dict[str, Any]]


def _resolve_episode(ep: EpisodeInput) -> Dict[str, Any]:
    """Normalize an episode input to a dict with 'path' and/or 'text' and 'title'."""
    if isinstance(ep, str):
        return {"path": ep, "title": pathlib.Path(ep).stem}
    return {
        "path": ep.get("path", ""),
        "text": ep.get("text", ""),
        "title": ep.get("title", pathlib.Path(ep.get("path", "")).stem),
    }


def batch_run(
    episodes: List[EpisodeInput],
    n_lessons: int = 10,
    prompt: Optional[str] = None,
    output_format: str = "json",
    output_dir: Optional[str] = None,
    no_llm: bool = False,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Process multiple episodes and return extraction results.

    Args:
        episodes: list of file paths (str) or dicts with 'path'/'text'/'title'.
        n_lessons: number of lessons to extract per episode.
        prompt: custom extraction prompt.
        output_format: 'json', 'markdown', or 'text'.
        output_dir: directory to write output files (one per episode).
        no_llm: use rule-based fallback instead of LLM.
        model: LLM model name.
        api_key: OpenAI-compatible API key.
        api_base: OpenAI-compatible API base URL.
        **kwargs: forwarded to extract_lessons.

    Returns:
        List of extraction result dicts.
    """
    results: List[Dict[str, Any]] = []

    for ep in episodes:
        info = _resolve_episode(ep)
        title = info.get("title", "unknown")
        text = info.get("text", "")

        # Transcribe if we have a file path and no text
        if not text and info.get("path"):
            text = transcribe_file(info["path"])

        if not text:
            results.append({
                "episode": title,
                "error": "No transcript text available",
                "lessons": [],
                "summary": "",
                "metadata": {"model": model, "n_lessons": n_lessons},
            })
            continue

        # Extract lessons
        result = extract_lessons(
            text=text,
            episode=title,
            n_lessons=n_lessons,
            prompt=prompt,
            no_llm=no_llm,
            model=model,
            api_key=api_key,
            api_base=api_base,
            **kwargs,
        )

        # Write output file if output_dir specified
        if output_dir:
            out_path = pathlib.Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            safe_name = "".join(c for c in title if c.isalnum() or c in " _-")[:60]
            ext_map = {"json": ".json", "markdown": ".md", "text": ".txt"}
            ext = ext_map.get(output_format, ".json")
            file_path = out_path / f"{safe_name}{ext}"
            if output_format == "json":
                file_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            elif output_format == "markdown":
                file_path.write_text(to_markdown(result))
            elif output_format == "text":
                file_path.write_text(to_text(result))

        results.append(result)

    return results


def batch_run_cli(
    episode_paths: List[str],
    n_lessons: int = 10,
    prompt: Optional[str] = None,
    output_format: str = "json",
    output_dir: Optional[str] = None,
    no_llm: bool = False,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """CLI-friendly wrapper: accepts a list of file paths."""
    episodes = [{"path": p, "title": pathlib.Path(p).stem} for p in episode_paths]
    return batch_run(
        episodes=episodes,
        n_lessons=n_lessons,
        prompt=prompt,
        output_format=output_format,
        output_dir=output_dir,
        no_llm=no_llm,
        model=model,
        api_key=api_key,
        api_base=api_base,
    )
