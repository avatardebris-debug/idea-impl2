"""Text chunking utility for transcript segmentation.

Splits transcript full_text and segments into overlapping chunks
suitable for vector search.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .config import settings
from .models import TranscriptSegment


@dataclass
class Chunk:
    """A single text chunk with metadata."""
    text: str
    start: float
    end: float
    job_id: str
    segment_indices: list[int] = field(default_factory=list)
    embedding: Optional[list[float]] = None


class TextChunker:
    """Splits transcript text into overlapping chunks."""

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        overlap_ratio: Optional[float] = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.overlap_ratio = overlap_ratio if overlap_ratio is not None else settings.CHUNK_OVERLAP_RATIO

    def chunk(
        self,
        segments: list[TranscriptSegment],
        full_text: str,
        job_id: str,
    ) -> list[Chunk]:
        """Split transcript segments into overlapping chunks.

        Chunks overlap by 20% to preserve context across boundaries.
        chunk_size is measured in words.
        """
        if not segments:
            return []

        chunks: list[Chunk] = []
        step = int(self.chunk_size * (1 - self.overlap_ratio))
        if step < 1:
            step = 1

        # Build a combined text with segment boundaries
        # We work on segments directly to preserve timestamps
        current_text = ""
        current_start = segments[0].start
        current_end = segments[0].end
        current_segments: list[int] = []

        for i, seg in enumerate(segments):
            # Count words in current_text + new segment
            current_words = len(current_text.split()) if current_text else 0
            new_words = len(seg.text.split()) if seg.text else 0
            total_words = current_words + new_words

            # If adding this segment exceeds chunk_size, emit current chunk
            if current_text and total_words > self.chunk_size:
                chunks.append(Chunk(
                    text=current_text.strip(),
                    start=current_start,
                    end=current_end,
                    job_id=job_id,
                    segment_indices=list(current_segments),
                ))
                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_text)
                current_text = overlap_text + seg.text
                current_start = segments[current_segments[-1]].start
                current_end = seg.end
                current_segments = [i]
            else:
                current_text += " " + seg.text if current_text else seg.text
                current_end = seg.end
                current_segments.append(i)

        # Emit final chunk
        if current_text.strip():
            chunks.append(Chunk(
                text=current_text.strip(),
                start=current_start,
                end=current_end,
                job_id=job_id,
                segment_indices=list(current_segments),
            ))

        return chunks

    def _get_overlap(self, text: str) -> str:
        """Get the last portion of text for overlap (20% of chunk_size)."""
        overlap_len = int(self.chunk_size * self.overlap_ratio)
        if len(text) <= overlap_len:
            return text
        # Find a word boundary near the overlap point
        overlap_text = text[-overlap_len:]
        space_idx = overlap_text.rfind(" ")
        if space_idx > 0:
            return overlap_text[space_idx + 1:]
        return overlap_text

    def chunk_from_text(
        self,
        text: str,
        job_id: str,
        start: float = 0.0,
        end: Optional[float] = None,
    ) -> list[Chunk]:
        """Split raw text into overlapping chunks (no segment info)."""
        if not text.strip():
            return []

        words = text.split()
        if not words:
            return []

        chunks: list[Chunk] = []
        step = int(self.chunk_size * (1 - self.overlap_ratio))
        if step < 1:
            step = 1

        for i in range(0, len(words), step):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            chunks.append(Chunk(
                text=chunk_text,
                start=start + i * 0.5,  # Approximate timestamp
                end=end or (start + len(words) * 0.5),
                job_id=job_id,
            ))

        return chunks
