"""Vector store integration using ChromaDB."""

from __future__ import annotations

import json
from typing import Optional

import chromadb
from chromadb.config import Settings

from .config import settings
from .chunker import Chunk


class VectorStore:
    """Manages per-job ChromaDB collections for transcript chunks."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        top_k: Optional[int] = None,
    ):
        self.db_path = db_path or settings.VECTOR_DB_PATH
        self.top_k = top_k or settings.VECTOR_TOP_K
        self._client: Optional[chromadb.ClientAPI] = None

    def _ensure_client(self) -> chromadb.ClientAPI:
        """Ensure ChromaDB client is initialized."""
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self.db_path)
        return self._client

    def _get_collection(self, job_id: str) -> chromadb.Collection:
        """Get or create a collection for a specific job."""
        client = self._ensure_client()
        collection_name = f"job_{job_id}"
        try:
            return client.get_collection(collection_name)
        except (chromadb.errors.NotFoundError, KeyError):
            return client.create_collection(
                collection_name,
                metadata={"description": f"Transcript chunks for job {job_id}"},
            )

    def upsert(self, job_id: str, chunks: list[Chunk]) -> None:
        """Upsert chunks with their embeddings and metadata into the job's collection."""
        if not chunks:
            return

        collection = self._get_collection(job_id)

        ids = [f"chunk_{i}" for i in range(len(chunks))]
        texts = [chunk.text for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks if chunk.embedding is not None]

        # If embeddings are not set, generate them
        if not embeddings or len(embeddings) < len(chunks):
            from .embeddings import EmbeddingGenerator
            generator = EmbeddingGenerator()
            embeddings = generator.generate_batch([chunk.text for chunk in chunks])

        # Ensure all chunks have embeddings
        for i, chunk in enumerate(chunks):
            if chunk.embedding is None:
                chunk.embedding = embeddings[i]

        metadatas = [
            {
                "job_id": job_id,
                "start": chunk.start,
                "end": chunk.end,
                "segment_indices": json.dumps(chunk.segment_indices),
                "text_preview": chunk.text[:100],
            }
            for chunk in chunks
        ]

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts,
        )

    def search(
        self,
        job_id: str,
        query_text: str,
        top_k: Optional[int] = None,
    ) -> list[dict]:
        """Search for the most similar chunks to the query text."""
        top_k = top_k or self.top_k

        from .embeddings import EmbeddingGenerator
        generator = EmbeddingGenerator()
        query_embedding = generator.generate(query_text)

        collection = self._get_collection(job_id)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "documents", "distances"],
        )

        chunks = []
        for i in range(len(results["ids"][0])):
            chunks.append({
                "text": results["documents"][0][i],
                "start": results["metadatas"][0][i]["start"],
                "end": results["metadatas"][0][i]["end"],
                "segment_indices": json.loads(results["metadatas"][0][i]["segment_indices"]),
                "distance": results["distances"][0][i],
            })

        return chunks

    def delete_collection(self, job_id: str) -> bool:
        """Delete the collection for a specific job."""
        try:
            client = self._ensure_client()
            client.delete_collection(f"job_{job_id}")
            return True
        except (chromadb.errors.NotFoundError, KeyError):
            return False
