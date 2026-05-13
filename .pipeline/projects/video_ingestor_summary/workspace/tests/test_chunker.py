"""Tests for video_ingestor.chunker."""

import pytest

from video_ingestor.chunker import Chunk, TextChunker
from video_ingestor.models import TranscriptSegment


class TestTextChunker:
    def test_chunk_empty_segments(self):
        chunker = TextChunker(chunk_size=100)
        chunks = chunker.chunk([], "", "job1")
        assert chunks == []

    def test_chunk_single_segment(self):
        segments = [
            TranscriptSegment(text="Hello world", start=0.0, end=5.0)
        ]
        chunker = TextChunker(chunk_size=100)
        chunks = chunker.chunk(segments, "Hello world", "job1")
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world"
        assert chunks[0].start == 0.0
        assert chunks[0].end == 5.0
        assert chunks[0].job_id == "job1"
        assert chunks[0].segment_indices == [0]

    def test_chunk_multiple_segments(self):
        segments = [
            TranscriptSegment(text="Hello", start=0.0, end=1.0),
            TranscriptSegment(text="world", start=1.0, end=2.0),
            TranscriptSegment(text="this is a test", start=2.0, end=3.0),
        ]
        chunker = TextChunker(chunk_size=10)
        chunks = chunker.chunk(segments, "Hello world this is a test", "job1")
        assert len(chunks) >= 1
        # First chunk should contain "Hello"
        assert "Hello" in chunks[0].text

    def test_chunk_with_overlap(self):
        segments = [
            TranscriptSegment(text=f"Word{i}", start=float(i), end=float(i) + 1.0)
            for i in range(20)
        ]
        chunker = TextChunker(chunk_size=5, overlap_ratio=0.2)
        chunks = chunker.chunk(segments, " ".join(seg.text for seg in segments), "job1")
        assert len(chunks) >= 1
        # Verify overlap exists between consecutive chunks
        if len(chunks) > 1:
            # Overlap should be about 20% of chunk_size
            overlap_len = int(5 * 0.2)
            # The end of chunk 0 and start of chunk 1 should have some overlap
            assert chunks[0].end >= chunks[1].start

    def test_chunk_respects_chunk_size(self):
        long_text = " ".join([f"Word{i}" for i in range(100)])
        segments = [
            TranscriptSegment(text=long_text, start=0.0, end=100.0)
        ]
        chunker = TextChunker(chunk_size=10)
        chunks = chunker.chunk(segments, long_text, "job1")
        # Each chunk should be approximately chunk_size words
        for chunk in chunks:
            word_count = len(chunk.text.split())
            assert word_count <= 12  # Allow some tolerance

    def test_chunk_preserves_timestamps(self):
        segments = [
            TranscriptSegment(text="First", start=0.0, end=1.0),
            TranscriptSegment(text="Second", start=1.0, end=2.0),
        ]
        chunker = TextChunker(chunk_size=10)
        chunks = chunker.chunk(segments, "First Second", "job1")
        assert len(chunks) == 1
        assert chunks[0].start == 0.0
        assert chunks[0].end == 2.0

    def test_chunk_job_id_propagation(self):
        segments = [
            TranscriptSegment(text="Test", start=0.0, end=1.0)
        ]
        chunker = TextChunker(chunk_size=10)
        chunks = chunker.chunk(segments, "Test", "unique-job-id")
        assert all(chunk.job_id == "unique-job-id" for chunk in chunks)

    def test_chunk_empty_text(self):
        segments = [
            TranscriptSegment(text="", start=0.0, end=1.0)
        ]
        chunker = TextChunker(chunk_size=10)
        chunks = chunker.chunk(segments, "", "job1")
        assert chunks == []

    def test_chunk_large_text(self):
        segments = [
            TranscriptSegment(text=f"Word{i}", start=float(i), end=float(i) + 1.0)
            for i in range(1000)
        ]
        chunker = TextChunker(chunk_size=50)
        chunks = chunker.chunk(segments, " ".join(seg.text for seg in segments), "job1")
        assert len(chunks) > 1
        # Verify all chunks have valid timestamps
        for chunk in chunks:
            assert chunk.start >= 0
            assert chunk.end > chunk.start
            assert chunk.text.strip()

    def test_chunk_with_special_characters(self):
        segments = [
            TranscriptSegment(text="Hello! @#$%", start=0.0, end=1.0),
            TranscriptSegment(text="World 🌍", start=1.0, end=2.0),
        ]
        chunker = TextChunker(chunk_size=10)
        chunks = chunker.chunk(segments, "Hello! @#$% World 🌍", "job1")
        assert len(chunks) >= 1
        # Verify special characters are preserved
        full_text = " ".join(chunk.text for chunk in chunks)
        assert "@" in full_text or "🌍" in full_text
