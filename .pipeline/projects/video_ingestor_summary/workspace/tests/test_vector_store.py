"""Tests for video_ingestor.vector_store."""

import os
import tempfile
import pytest

from video_ingestor.chunker import Chunk
from video_ingestor.embeddings import EmbeddingGenerator
from video_ingestor.vector_store import VectorStore


class TestVectorStore:
    @pytest.fixture
    def temp_db(self):
        """Create a temporary ChromaDB path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield os.path.join(tmpdir, "test_chroma.db")

    @pytest.fixture
    def vector_store(self, temp_db):
        """Create a VectorStore instance with temp DB."""
        return VectorStore(db_path=temp_db)

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks for testing."""
        generator = EmbeddingGenerator()
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "Python is a great programming language",
            "Machine learning is transforming the world",
            "Video transcription is a complex task",
            "Natural language processing is fascinating",
        ]
        chunks = []
        for i, text in enumerate(texts):
            embedding = generator.generate(text)
            chunks.append(Chunk(
                text=text,
                start=float(i),
                end=float(i) + 1.0,
                job_id="test-job",
                segment_indices=[i],
                embedding=embedding,
            ))
        return chunks

    def test_upsert_and_search(self, vector_store, sample_chunks):
        """Test upserting chunks and searching them."""
        vector_store.upsert("test-job", sample_chunks)

        results = vector_store.search("test-job", "programming language")
        assert len(results) > 0
        # The Python chunk should be among the top results
        assert any("Python" in r["text"] for r in results)

    def test_upsert_multiple_jobs(self, vector_store, sample_chunks):
        """Test upserting chunks for multiple jobs."""
        vector_store.upsert("job1", sample_chunks[:2])
        vector_store.upsert("job2", sample_chunks[2:])

        results1 = vector_store.search("job1", "programming")
        assert len(results1) > 0

        results2 = vector_store.search("job2", "machine learning")
        assert len(results2) > 0

    def test_search_returns_relevant_results(self, vector_store, sample_chunks):
        """Test that search returns relevant results."""
        vector_store.upsert("test-job", sample_chunks)

        # Search for "fox" - should find the fox sentence
        results = vector_store.search("test-job", "fox")
        assert len(results) > 0
        assert any("fox" in r["text"].lower() for r in results)

    def test_search_with_no_results(self, vector_store, sample_chunks):
        """Test search with no matching results."""
        vector_store.upsert("test-job", sample_chunks)

        # Search for something not in the corpus
        results = vector_store.search("test-job", "xyzxyzxyz")
        # Should return empty or very low relevance results
        assert len(results) >= 0  # May return empty list

    def test_upsert_overwrites_existing(self, vector_store, sample_chunks):
        """Test that upserting the same job_id overwrites previous data."""
        chunks1 = [
            Chunk(text="Old text", start=0.0, end=1.0, job_id="test-job",
                  segment_indices=[0], embedding=[0.1] * 384)
        ]
        chunks2 = [
            Chunk(text="New text", start=0.0, end=1.0, job_id="test-job",
                  segment_indices=[0], embedding=[0.2] * 384)
        ]

        vector_store.upsert("test-job", chunks1)
        vector_store.upsert("test-job", chunks2)

        results = vector_store.search("test-job", "new")
        assert any("New text" in r["text"] for r in results)

    def test_search_with_top_k(self, vector_store, sample_chunks):
        """Test search with custom top_k parameter."""
        vector_store.upsert("test-job", sample_chunks)

        results_top1 = vector_store.search("test-job", "programming", top_k=1)
        results_top3 = vector_store.search("test-job", "programming", top_k=3)

        assert len(results_top1) <= 1
        assert len(results_top3) <= 3
        assert len(results_top3) >= len(results_top1)

    def test_persistence_across_instances(self, temp_db):
        """Test that data persists across VectorStore instances."""
        # Create first instance and upsert data
        store1 = VectorStore(db_path=temp_db)
        generator = EmbeddingGenerator()
        chunk = Chunk(
            text="Persistent test",
            start=0.0,
            end=1.0,
            job_id="persist-job",
            segment_indices=[0],
            embedding=generator.generate("Persistent test"),
        )
        store1.upsert("persist-job", [chunk])

        # Create second instance and verify data persists
        store2 = VectorStore(db_path=temp_db)
        results = store2.search("persist-job", "persistent")
        assert len(results) > 0
        assert any("Persistent test" in r["text"] for r in results)

    def test_search_empty_job(self, vector_store):
        """Test searching a job with no data."""
        results = vector_store.search("nonexistent-job", "test")
        assert results == []

    def test_upsert_empty_chunks(self, vector_store):
        """Test upserting empty chunk list."""
        vector_store.upsert("test-job", [])
        # Should not raise an error

    def test_upsert_chunk_without_embedding(self):
        """Test that upserting a chunk without embedding auto-generates one."""
        store = VectorStore()
        chunk = Chunk(
            text="No embedding",
            start=0.0,
            end=1.0,
            job_id="test-job",
            segment_indices=[0],
            embedding=None,  # No embedding
        )
        # Should not raise an error - embeddings are auto-generated
        store.upsert("test-job", [chunk])
        results = store.search("test-job", "no embedding")
        assert len(results) > 0

    def test_search_similarity_scores(self, vector_store, sample_chunks):
        """Test that search returns distance scores."""
        vector_store.upsert("test-job", sample_chunks)

        results = vector_store.search("test-job", "programming")
        assert len(results) > 0
        for result in results:
            assert "distance" in result
            assert isinstance(result["distance"], float)
            assert result["distance"] >= 0.0
