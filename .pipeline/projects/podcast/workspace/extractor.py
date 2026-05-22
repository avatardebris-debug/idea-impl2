"""
extractor.py — LLM-powered lesson extractor for podcast transcripts.

Given a transcript (text), asks the LLM to identify the N most actionable,
memorable lessons or insights. Customizable prompt for different focus areas.

Output schema:
    {
      "episode":  str,
      "lessons":  [{"number": int, "title": str, "detail": str, "quote": str}],
      "summary":  str,
      "metadata": {"model": str, "n_lessons": int, "transcript_length": int,
                   "custom_prompt": str, "extracted_at": str}
    }
"""
from __future__ import annotations
import json
import textwrap
import urllib.request
from datetime import datetime, timezone
from typing import Any

_OLLAMA_HOST = "http://localhost:11434"

_DEFAULT_PROMPT = (
    "actionable, practical lessons or insights that a listener should remember and act on"
)


def _call_ollama(prompt: str, model: str, timeout: int = 180) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_ctx": 16384},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{_OLLAMA_HOST}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")).get("response", "").strip()
    except Exception:
        return ""


def _parse_lessons_json(text: str, n: int) -> list[dict]:
    """Extract JSON array of lessons from LLM response."""
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            items = json.loads(text[start:end])
            if isinstance(items, list):
                return items[:n]
        except json.JSONDecodeError:
            pass
    return []


def _fallback_extract_lessons(transcript: str, n: int) -> list[dict]:
    """Rule-based fallback: split into chunks and return first N non-trivial sentences."""
    import re
    sentences = re.split(r"(?<=[.!?])\s+", transcript)
    lessons = []
    for i, sent in enumerate(sentences):
        if len(sent.split()) >= 8 and len(lessons) < n:
            lessons.append({
                "number": len(lessons) + 1,
                "title":  sent[:60].rstrip(".!?,"),
                "detail": sent,
                "quote":  sent,
            })
    return lessons


def extract_lessons(
    transcript: str,
    episode_name: str = "",
    n_lessons: int = 10,
    custom_prompt: str = "",
    model: str = "qwen3:6b",
) -> dict[str, Any]:
    """Extract N lessons from a podcast transcript.

    Args:
        transcript:    Full transcript text.
        episode_name:  Episode title or filename (for metadata).
        n_lessons:     Number of lessons to extract.
        custom_prompt: Override the lesson focus (e.g. "business tactics only").
        model:         Ollama model.

    Returns:
        Dict matching the output schema described in the module docstring.
    """
    focus = custom_prompt.strip() or _DEFAULT_PROMPT

    # Trim transcript to avoid context overflow (keep ~12k chars)
    transcript_excerpt = transcript[:12000]
    if len(transcript) > 12000:
        transcript_excerpt += f"\n...[transcript truncated at 12000 chars of {len(transcript)} total]"

    prompt = textwrap.dedent(f"""
        You are an expert podcast analyst. Read the following podcast transcript and extract
        exactly {n_lessons} {focus}.

        For each lesson, return a JSON object with:
        - "number":  lesson number (1 to {n_lessons})
        - "title":   concise lesson title (max 10 words)
        - "detail":  2-3 sentence explanation of the lesson and why it matters
        - "quote":   the most relevant verbatim quote from the transcript supporting this lesson
                     (max 2 sentences; empty string if none found)

        Return ONLY a valid JSON array of {n_lessons} lesson objects. No preamble, no explanation.

        EPISODE: {episode_name or "Podcast Episode"}

        TRANSCRIPT:
        {transcript_excerpt}

        JSON ARRAY:
    """).strip()

    response = _call_ollama(prompt, model=model)
    lessons  = _parse_lessons_json(response, n_lessons)

    # If LLM failed or returned too few, supplement with fallback
    if len(lessons) < n_lessons:
        fallback = _fallback_extract_lessons(transcript, n_lessons - len(lessons))
        # Renumber
        offset = len(lessons)
        for i, l in enumerate(fallback):
            l["number"] = offset + i + 1
        lessons.extend(fallback)

    # Normalise lesson schema
    normalised = []
    for i, l in enumerate(lessons[:n_lessons], 1):
        normalised.append({
            "number": i,
            "title":  str(l.get("title", f"Lesson {i}"))[:120],
            "detail": str(l.get("detail", "")),
            "quote":  str(l.get("quote",  "")),
        })

    # Generate episode summary
    summary_prompt = textwrap.dedent(f"""
        In 2-3 sentences, summarise what this podcast episode is about and its main theme.
        Be specific and concrete.

        EPISODE: {episode_name or "Podcast Episode"}
        TRANSCRIPT (first 3000 chars): {transcript[:3000]}

        SUMMARY:
    """).strip()
    summary = _call_ollama(summary_prompt, model=model, timeout=60)
    if not summary:
        # Fallback summary from first 300 chars
        summary = transcript[:300].strip() + "..."

    return {
        "episode": episode_name or "Unknown Episode",
        "lessons": normalised,
        "summary": summary,
        "metadata": {
            "model":             model,
            "n_lessons":         len(normalised),
            "transcript_length": len(transcript),
            "custom_prompt":     custom_prompt,
            "extracted_at":      datetime.now(timezone.utc).isoformat(),
        },
    }
