"""Embedding generation using sentence-transformers."""

from __future__ import annotations

from typing import Optional

from sentence_transformers import SentenceTransformer

from .config import settings


class EmbeddingGenerator:
    """Generates sentence embeddings using a lightweight model."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model: Optional[SentenceTransformer] = None

    def _ensure_model(self) -> SentenceTransformer:
        """Load or return the embedding model."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def generate(self, text: str) -> list[float]:
        """Generate a normalized embedding vector for the given text."""
        model = self._ensure_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        model = self._ensure_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]
