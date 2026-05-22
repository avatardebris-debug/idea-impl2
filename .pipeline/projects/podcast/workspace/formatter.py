"""
formatter.py — Renders extracted lessons to Markdown or plain text.

Produces clean, shareable output suitable for notes apps, newsletters,
or piping into skillify.
"""
from __future__ import annotations
from datetime import datetime, timezone


def to_markdown(result: dict, include_quotes: bool = True) -> str:
    """Render extraction result as Markdown."""
    episode = result.get("episode", "Episode")
    summary = result.get("summary", "")
    lessons = result.get("lessons", [])
    meta    = result.get("metadata", {})
    now     = meta.get("extracted_at", datetime.now(timezone.utc).isoformat())[:10]

    lines = [
        f"# Lessons from: {episode}",
        "",
        f"> Extracted {len(lessons)} lessons — {now}",
        "",
    ]
    if summary:
        lines += ["## Episode Summary", "", summary, ""]

    lines += ["## Lessons", ""]
    for lesson in lessons:
        lines.append(f"### {lesson['number']}. {lesson['title']}")
        lines.append("")
        if lesson.get("detail"):
            lines.append(lesson["detail"])
            lines.append("")
        if include_quotes and lesson.get("quote"):
            lines.append(f"> *\"{lesson['quote']}\"*")
            lines.append("")

    return "\n".join(lines)


def to_plain(result: dict) -> str:
    """Render extraction result as plain numbered list."""
    episode = result.get("episode", "Episode")
    lessons = result.get("lessons", [])
    lines   = [f"LESSONS FROM: {episode}", "=" * 50, ""]
    summary = result.get("summary", "")
    if summary:
        lines += [f"SUMMARY: {summary}", ""]
    for lesson in lessons:
        lines.append(f"{lesson['number']}. {lesson['title']}")
        if lesson.get("detail"):
            lines.append(f"   {lesson['detail']}")
        lines.append("")
    return "\n".join(lines)
