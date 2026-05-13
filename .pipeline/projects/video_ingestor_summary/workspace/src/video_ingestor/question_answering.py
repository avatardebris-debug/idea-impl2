"""Question-answering service for indexed transcripts."""

from __future__ import annotations

from typing import Optional

from .config import settings
from .llm_harness import LLMHarness
from .prompts import QA_PROMPT
from .vector_store import VectorStore


class QandAError(Exception):
    """Raised when Q&A fails."""


class QuestionAnswerer:
    """Answers questions about indexed video transcripts."""

    def __init__(
        self,
        harness: Optional[LLMHarness] = None,
        vector_store: Optional[VectorStore] = None,
        top_k: Optional[int] = None,
    ):
        self.harness = harness or LLMHarness()
        self.vector_store = vector_store or VectorStore()
        self.top_k = top_k or settings.VECTOR_TOP_K

    def answer(
        self,
        question: str,
        job_id: str,
        top_k: Optional[int] = None,
        max_context_length: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """Answer a question about a specific indexed transcript.

        Args:
            question: The user's question.
            job_id: The job ID whose transcript to search.
            top_k: Number of chunks to retrieve for context.
            max_context_length: Maximum length of context text.
            system_prompt: Optional system prompt for the LLM.

        Returns:
            Dict with answer, citations, and confidence.

        Raises:
            QandAError: If Q&A fails.
        """
        top_k = top_k or self.top_k

        # Retrieve relevant chunks
        chunks = self.vector_store.search(job_id, question, top_k=top_k)

        if not chunks:
            return {
                "answer": "I couldn't find any relevant information in the transcript to answer this question.",
                "citations": [],
                "confidence": 0.0,
            }

        # Build context from retrieved chunks
        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"[{chunk['start']:.2f}-{chunk['end']:.2f}] {chunk['text']}"
            )
        context = "\n\n".join(context_parts)

        # Apply max_context_length if specified
        if max_context_length:
            context = context[:max_context_length]

        # Generate answer using LLM
        prompt = QA_PROMPT.format(context=context, question=question)

        try:
            result = self.harness.generate_json(prompt)
            answer = result.get("answer") or "I don't have enough information to answer this question."
            citations = result.get("citations") or []
            confidence = result.get("confidence") if result.get("confidence") is not None else 0.5
            return {
                "answer": answer,
                "citations": citations,
                "confidence": confidence,
            }
        except Exception as e:
            raise QandAError(f"Question answering failed: {e}")

    def answer_from_text(
        self,
        text: str,
        question: str,
    ) -> dict:
        """Answer a question from raw text (no vector store needed).

        Args:
            text: The transcript text.
            question: The user's question.

        Returns:
            Dict with answer, citations, and confidence.
        """
        prompt = QA_PROMPT.format(context=text[:4000], question=question)

        try:
            result = self.harness.generate_json(prompt)
            return {
                "answer": result.get("answer", ""),
                "citations": result.get("citations", []),
                "confidence": result.get("confidence", 0.0),
            }
        except Exception as e:
            raise QandAError(f"Q&A failed: {e}")
