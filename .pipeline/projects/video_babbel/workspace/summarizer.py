"""Summarization and Q&A module.

Provides ``Summarizer`` (extractive summary) and ``QAEngine`` (simple
keyword-based question answering) over transcript segments.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from video_babbel.core import QAError, SummarizationError, get_logger

logger = get_logger(__name__)


class Summarizer:
    """Produces a concise summary from transcript segments.

    For MVP this uses a simple extractive approach: join segment texts
    and take the first N sentences.
    """

    def __init__(self, max_sentences: int = 5) -> None:
        self.max_sentences = max_sentences

    def summarize(self, segments: List[Dict[str, Any]]) -> str:
        """Return a short summary of *segments*.

        Parameters
        ----------
        segments : list of dict
            Each dict must have a ``"text"`` key.

        Returns
        -------
        str
            A summary string (up to *max_sentences* sentences).
        """
        if not segments:
            return ""

        try:
            texts = []
            for seg in segments:
                raw = seg.get("text")
                if raw is not None:
                    texts.append(str(raw))
            full_text = " ".join(texts)
            sentences = re.split(r"(?<=[.!?])\s+", full_text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                return ""

            selected = sentences[: self.max_sentences]
            return ". ".join(selected)
        except Exception as exc:
            raise SummarizationError(f"Summarization failed: {exc}") from exc


class QAEngine:
    """Simple keyword-based question answering over transcript segments.

    For MVP this uses a basic extractive approach: find the segment
    that shares the most words with the question.
    """

    def __init__(self, segments: List[Dict[str, Any]]) -> None:
        self.segments = segments

    def answer(self, question: str) -> str:
        """Return an answer to *question* based on *segments*.

        Parameters
        ----------
        question : str
            The question to answer.

        Returns
        -------
        str
            The best matching segment text, or an empty string.
        """
        if not question or not question.strip():
            return ""

        try:
            question_lower = question.strip().lower()
            question_words = set(re.findall(r"\b\w+\b", question_lower))

            # Remove common stop words
            stop_words = {
                "the", "a", "an", "is", "are", "was", "were", "be", "been",
                "being", "have", "has", "had", "do", "does", "did", "will",
                "would", "could", "should", "may", "might", "shall", "can",
                "to", "of", "in", "for", "on", "with", "at", "by", "from",
                "as", "into", "through", "during", "before", "after", "above",
                "below", "between", "out", "off", "over", "under", "again",
                "further", "then", "once", "here", "there", "when", "where",
                "why", "how", "all", "both", "each", "few", "more", "most",
                "other", "some", "such", "no", "nor", "not", "only", "own",
                "same", "so", "than", "too", "very", "s", "t", "just",
                "don", "now",
            }
            question_words -= stop_words

            if not question_words:
                return ""

            best_score = -1
            best_segment = ""

            for seg in self.segments:
                raw_text = seg.get("text")
                if raw_text is None:
                    continue
                text = str(raw_text).strip().lower()
                if not text:
                    continue
                seg_words = set(re.findall(r"\b\w+\b", text))
                score = len(question_words & seg_words)
                if score > best_score:
                    best_score = score
                    best_segment = seg.get("text", "")

            if best_score > 0 and best_segment:
                return best_segment
            return ""
        except Exception as exc:
            raise QAError(f"Q&A failed: {exc}") from exc
