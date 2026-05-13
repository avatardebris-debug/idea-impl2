"""Summarization service for video transcripts."""

from __future__ import annotations

from typing import Optional

from .config import settings
from .llm_harness import LLMHarness
from .prompts import SUMMARIZATION_PROMPT


class SummarizationError(Exception):
    """Raised when summarization fails."""


class Summarizer:
    """Produces structured summaries from transcript text."""

    def __init__(
        self,
        harness: Optional[LLMHarness] = None,
        length: Optional[str] = None,
        tone: Optional[str] = None,
        format_type: Optional[str] = None,
    ):
        self.harness = harness or LLMHarness()
        self.length = length or "medium"
        self.tone = tone or "neutral"
        self.format_type = format_type or "paragraph"

    def summarize(
        self,
        full_text: str,
        segments: list[dict],
        length: Optional[str] = None,
        tone: Optional[str] = None,
        format_type: Optional[str] = None,
    ) -> dict:
        """Generate a structured summary of the transcript.

        Args:
            full_text: Full transcript text.
            segments: List of transcript segment dicts.
            length: Summary length - 'short', 'medium', or 'long'.
            tone: Tone of the summary - 'neutral', 'formal', 'casual'.
            format_type: Format - 'paragraph', 'bullet', 'json'.

        Returns:
            Dict with summary_text, key_points, and action_items.

        Raises:
            SummarizationError: If summarization fails.
        """
        length = length or self.length
        tone = tone or self.tone
        format_type = format_type or self.format_type

        # Build context from segments (limit to avoid token limits)
        context_segments = segments[-50:]  # Use last 50 segments as context
        context_text = "\n".join(
            f"[{seg.get('start', 0):.2f}-{seg.get('end', 0):.2f}] {seg.get('text', '')}"
            for seg in context_segments
        )

        prompt = SUMMARIZATION_PROMPT.format(
            transcript=context_text[:4000],  # Limit prompt size
            length=length,
            tone=tone,
            format=format_type,
        )

        try:
            summary = self.harness.generate_json(prompt)
            return {
                "summary_text": summary.get("summary_text") or "",
                "key_points": summary.get("key_points") or [],
                "action_items": summary.get("action_items") or [],
            }
        except Exception as e:
            raise SummarizationError(f"Summarization failed: {e}")

    def summarize_from_text(
        self,
        full_text: str,
        length: Optional[str] = None,
        tone: Optional[str] = None,
        format_type: Optional[str] = None,
    ) -> dict:
        """Generate a summary from just the full text (no segments).

        Args:
            full_text: Full transcript text.
            length: Summary length.
            tone: Tone of the summary.
            format_type: Format.

        Returns:
            Dict with summary_text, key_points, and action_items.
        """
        length = length or self.length
        tone = tone or self.tone
        format_type = format_type or self.format_type

        prompt = SUMMARIZATION_PROMPT.format(
            transcript=full_text[:4000],
            length=length,
            tone=tone,
            format=format_type,
        )

        try:
            summary = self.harness.generate_json(prompt)
            return {
                "summary_text": summary.get("summary_text") or "",
                "key_points": summary.get("key_points") or [],
                "action_items": summary.get("action_items") or [],
            }
        except Exception as e:
            raise SummarizationError(f"Summarization failed: {e}")
