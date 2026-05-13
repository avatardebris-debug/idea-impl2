"""Tests for video_ingestor.embeddings."""

import pytest

from video_ingestor.embeddings import EmbeddingGenerator


class TestEmbeddingGenerator:
    def test_generate_single_text(self):
        generator = EmbeddingGenerator()
        embedding = generator.generate("Hello world")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        # Check that embedding is normalized (L2 norm ≈ 1)
        norm = (sum(x ** 2 for x in embedding)) ** 0.5
        assert abs(norm - 1.0) < 0.01

    def test_generate_different_texts_different_embeddings(self):
        generator = EmbeddingGenerator()
        emb1 = generator.generate("Hello world")
        emb2 = generator.generate("Goodbye world")
        assert emb1 != emb2

    def test_generate_same_text_same_embedding(self):
        generator = EmbeddingGenerator()
        emb1 = generator.generate("Hello world")
        emb2 = generator.generate("Hello world")
        assert emb1 == emb2

    def test_generate_batch(self):
        generator = EmbeddingGenerator()
        texts = ["Hello", "World", "Test"]
        embeddings = generator.generate_batch(texts)
        assert len(embeddings) == 3
        for emb in embeddings:
            assert isinstance(emb, list)
            assert len(emb) > 0
            # Check normalization
            norm = (sum(x ** 2 for x in emb)) ** 0.5
            assert abs(norm - 1.0) < 0.01

    def test_generate_empty_text(self):
        generator = EmbeddingGenerator()
        embedding = generator.generate("")
        assert isinstance(embedding, list)
        assert len(embedding) > 0

    def test_generate_long_text(self):
        generator = EmbeddingGenerator()
        long_text = " ".join([f"Word{i}" for i in range(1000)])
        embedding = generator.generate(long_text)
        assert isinstance(embedding, list)
        assert len(embedding) > 0

    def test_generate_special_characters(self):
        generator = EmbeddingGenerator()
        embedding = generator.generate("Hello! @#$% 🌍")
        assert isinstance(embedding, list)
        assert len(embedding) > 0

    def test_generate_unicode_text(self):
        generator = EmbeddingGenerator()
        embedding = generator.generate("こんにちは世界")
        assert isinstance(embedding, list)
        assert len(embedding) > 0

    def test_embedding_dimension_consistency(self):
        generator = EmbeddingGenerator()
        emb1 = generator.generate("Text one")
        emb2 = generator.generate("Text two")
        assert len(emb1) == len(emb2)
