"""Summarization and Q&A modules — summarize transcripts and answer questions."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from video_babbel.core import QAError, SummarizationError, get_logger

logger = get_logger(__name__)


class Summarizer:
    """Creates a summary from a list of transcript segments.

    Parameters
    ----------
    max_sentences : int
        Maximum number of sentences in the summary.  Default is 5.
    """

    def __init__(self, max_sentences: int = 5) -> None:
        if max_sentences < 1:
            raise SummarizationError("max_sentences must be >= 1")
        self.max_sentences = max_sentences
        logger.info("Initializing Summarizer with max_sentences=%d", max_sentences)

    def summarize(self, segments: List[Dict[str, Any]]) -> str:
        """Create a summary from transcript segments.

        Parameters
        ----------
        segments : list[dict]
            List of transcription segments, each containing ``text``,
            ``start``, and ``end`` keys.

        Returns
        ----- --
        str
            A summary string.

        Raises
        ------
        SummarizationError
            If summarization fails.
        """
        logger.info("Summarizing %d segments", len(segments) if segments else 0)
        try:
            if not segments:
                return ""

            # Filter out segments with None or empty text
            texts = []
            for seg in segments:
                text = seg.get("text")
                if text and text.strip():
                    texts.append(text.strip())

            if not texts:
                return ""

            # Join all texts
            full_text = " ".join(texts)

            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', full_text)
            sentences = [s for s in sentences if s.strip()]

            if not sentences:
                return ""

            # Take up to max_sentences
            summary_sentences = sentences[: self.max_sentences]
            summary = ". ".join(summary_sentences)

            # Ensure proper ending
            if summary and not summary[-1] in ".!?":
                summary += "."

            logger.info("Summary: %s", summary[:100])
            return summary
        except SummarizationError:
            raise
        except Exception as exc:
            raise SummarizationError(f"Summarization failed: {exc}") from exc


class QAEngine:
    """Answers questions based on transcript segments.

    Parameters
    ----------
    segments : list[dict]
        List of transcription segments.
    """

    def __init__(self, segments: Optional[List[Dict[str, Any]]] = None) -> None:
        self.segments = segments or []
        logger.info("Initializing QAEngine with %d segments", len(self.segments))

    def answer(self, question: str) -> str:
        """Answer a question based on the transcript segments.

        Parameters
        ----------
        question : str
            The question to answer.

        Returns
        ----- --
        str
            The answer text, or empty string if no answer found.

        Raises
        ------
        QAError
            If Q&A fails.
        """
        logger.info("Answering question: %s", question)
        try:
            if not question or not question.strip():
                return ""

            if not self.segments:
                return ""

            # Filter out segments with None or empty text
            valid_segments = []
            for seg in self.segments:
                text = seg.get("text")
                if text and text.strip():
                    valid_segments.append(seg)

            if not valid_segments:
                return ""

            # Simple keyword matching
            question_words = set(re.findall(r'\w+', question.lower()))
            if not question_words:
                return ""

            best_score = 0
            best_segment = None

            for seg in valid_segments:
                text = seg["text"]
                text_words = set(re.findall(r'\w+', text.lower()))
                score = len(question_words & text_words)
                if score > best_score:
                    best_score = score
                    best_segment = seg

            if best_segment and best_score > 0:
                return best_segment["text"]

            # If no keyword match, return the first segment as fallback
            if valid_segments:
                return valid_segments[0]["text"]

            return ""
        except QAError:
            raise
        except Exception as exc:
            raise QAError(f"Q&A failed: {exc}") from exc
