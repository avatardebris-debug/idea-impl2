"""Prompt templates for LLM-based summarization and Q&A."""

from __future__ import annotations

SUMMARIZATION_PROMPT = """\
You are a helpful assistant that summarizes video transcripts.

Given the following transcript, produce a structured summary with:
1. A short summary (2-3 sentences)
2. Key points (bullet list)
3. Action items (if any)

Transcript:
{transcript}

Summary length: {length}
Tone: {tone}
Format: {format}

Please provide your response in the following JSON format:
{{
  "summary_text": "...",
  "key_points": ["...", "..."],
  "action_items": ["...", "..."]
}}
"""

QA_PROMPT = """\
You are a helpful assistant that answers questions based on a video transcript.

Given the following context from a transcript and a user question, provide a grounded answer.
Your answer must be based ONLY on the provided context. If the context doesn't contain enough
information to answer the question, say so clearly.

Context:
{context}

Question: {question}

Please provide your response in the following JSON format:
{{
  "answer": "...",
  "citations": [
    {{"text": "...", "start": 0.0, "end": 0.0}}
  ],
  "confidence": 0.0
}}

The confidence score should be between 0.0 (not confident) and 1.0 (very confident).
Citations should reference actual segments from the context with accurate timestamps.
"""
