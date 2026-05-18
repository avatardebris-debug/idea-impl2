"""
summarizer.py — Core meeting transcript summarization engine.
"""
from __future__ import annotations
import json
import textwrap
import urllib.request
from datetime import datetime, timezone
from typing import Any

_OLLAMA_HOST = "http://localhost:11434"


def _call_ollama(prompt: str, model: str = "qwen3:6b", timeout: int = 180) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 16384},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{_OLLAMA_HOST}/api/generate",
            data=data, headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")).get("response", "").strip()
    except Exception:
        return ""


def _parse_json(text: str) -> dict:
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


def _fallback_summary(text: str) -> dict:
    """Static fallback when LLM fails."""
    return {
        "title": "Meeting Summary (Fallback)",
        "date": datetime.now(timezone.utc).isoformat()[:10],
        "executive_summary": "Auto-generated summary. The LLM was unavailable, so key points could not be deeply analyzed.",
        "key_topics": ["General Discussion"],
        "action_items": [
            {"task": "Review full transcript manually", "assignee": "Team", "deadline": "ASAP"}
        ],
        "decisions": ["Proceed with existing plans"],
        "metadata": {
            "model": "fallback",
            "text_length": len(text)
        }
    }


def analyze_transcript(transcript: str, model: str = "qwen3:6b") -> dict[str, Any]:
    prompt = textwrap.dedent(f"""
        You are an expert executive assistant. Analyze the following meeting transcript.
        Extract the action items (with assignees and deadlines if mentioned), key decisions made, and main topics.

        Return ONLY a valid JSON object matching this schema:
        {{
          "title": "A short descriptive title for the meeting",
          "date": "Date of meeting if mentioned, otherwise today's date",
          "executive_summary": "3-4 sentence high level summary",
          "key_topics": ["Topic 1", "Topic 2"],
          "action_items": [
            {{"task": "What needs to be done", "assignee": "Who (or 'Unassigned')", "deadline": "When (or 'None')"}}
          ],
          "decisions": ["Decision 1", "Decision 2"]
        }}

        TRANSCRIPT:
        {transcript[:16000]}
    """).strip()

    response = _call_ollama(prompt, model=model)
    result = _parse_json(response)

    if not result or "action_items" not in result:
        return _fallback_summary(transcript)

    result["metadata"] = {
        "model": model,
        "text_length": len(transcript),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


def format_markdown(data: dict) -> str:
    lines = [
        f"# 📝 {data.get('title', 'Meeting Notes')}", "",
        f"> **Date:** {data.get('date', 'Unknown')}", "",
        "## Executive Summary", "", data.get("executive_summary", ""), "",
        "## Key Topics", ""
    ]
    for t in data.get("key_topics", []):
        lines.append(f"- {t}")
    lines.append("")

    lines.extend(["## Decisions Made", ""])
    for d in data.get("decisions", []):
        lines.append(f"- ⚖️ {d}")
    lines.append("")

    lines.extend(["## Action Items", ""])
    lines.append("| Task | Assignee | Deadline |")
    lines.append("|---|---|---|")
    for a in data.get("action_items", []):
        lines.append(f"| {a.get('task', '')} | @{a.get('assignee', 'Unassigned')} | ⏰ {a.get('deadline', 'None')} |")

    return "\n".join(lines)
