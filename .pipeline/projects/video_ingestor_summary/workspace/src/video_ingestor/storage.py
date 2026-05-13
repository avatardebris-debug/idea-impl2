"""SQLite storage layer for jobs and transcripts."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import settings


class Storage:
    """Manages SQLite storage for ingest jobs and transcripts.

    Uses thread-local storage so that each thread gets its own connection,
    avoiding SQLite threading errors.
    """

    CREATE_TABLES_SQL = """
    CREATE TABLE IF NOT EXISTS jobs (
        id              TEXT PRIMARY KEY,
        status          TEXT NOT NULL DEFAULT 'pending',
        video_path      TEXT,
        audio_path      TEXT,
        transcript_json TEXT,
        full_text       TEXT,
        summary_json    TEXT,
        metadata_json   TEXT,
        error           TEXT,
        created_at      TEXT NOT NULL,
        completed_at    TEXT
    );
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        # Ensure parent directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create a thread-local connection."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.executescript(self.CREATE_TABLES_SQL)
            conn.commit()
            self._local.conn = conn
        return conn

    def connect(self) -> None:
        """Open the database and ensure all tables exist."""
        self._get_conn()

    def close(self) -> None:
        """Close the database connection for the current thread."""
        conn = getattr(self._local, "conn", None)
        if conn:
            conn.close()
            self._local.conn = None

    def _ensure_connected(self) -> None:
        # Thread-local connections are auto-created by _get_conn
        pass

    def create_job(self, video_path: str, metadata: dict) -> str:
        """Create a new ingest job and return its ID."""
        conn = self._get_conn()
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO jobs (id, status, video_path, metadata_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (job_id, "pending", video_path, json.dumps(metadata), now),
        )
        conn.commit()
        return job_id

    def update_job_status(self, job_id: str, status: str, error: Optional[str] = None) -> None:
        """Update job status and optionally set error."""
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        if status == "completed":
            conn.execute(
                "UPDATE jobs SET status=?, completed_at=? WHERE id=?",
                (status, now, job_id),
            )
        elif status == "failed":
            conn.execute(
                "UPDATE jobs SET status=?, error=?, completed_at=? WHERE id=?",
                (status, error, now, job_id),
            )
        else:
            conn.execute(
                "UPDATE jobs SET status=? WHERE id=?",
                (status, job_id),
            )
        conn.commit()

    def update_job_transcript(self, job_id: str, transcript_json: str, full_text: str) -> None:
        """Store transcript data for a completed job."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE jobs SET transcript_json=?, full_text=?, status='completed', "
            "completed_at=? WHERE id=? AND status='processing'",
            (transcript_json, full_text, datetime.now(timezone.utc).isoformat(), job_id),
        )
        conn.commit()

    def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a job by ID."""
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT id, status, video_path, audio_path, transcript_json, "
            "full_text, summary_json, metadata_json, error, created_at, completed_at "
            "FROM jobs WHERE id=?",
            (job_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "job_id": row[0],
            "status": row[1],
            "video_path": row[2],
            "audio_path": row[3],
            "transcript": json.loads(row[4]) if row[4] else [],
            "full_text": row[5] or "",
            "summary": json.loads(row[6]) if row[6] else None,
            "metadata": json.loads(row[7]) if row[7] else {},
            "error": row[8],
            "created_at": row[9],
            "completed_at": row[10],
        }

    def list_jobs(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """List recent jobs."""
        conn = self._get_conn()
        cur = conn.execute(
            "SELECT id, status, video_path, created_at, completed_at "
            "FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        return [
            {
                "job_id": r[0],
                "status": r[1],
                "video_path": r[2],
                "created_at": r[3],
                "completed_at": r[4],
            }
            for r in cur.fetchall()
        ]

    def delete_job(self, job_id: str) -> bool:
        """Delete a job and its associated files."""
        conn = self._get_conn()
        job = self.get_job(job_id)
        if not job:
            return False
        # Remove temp files
        for field in ("video_path", "audio_path"):
            path = job.get(field)
            if path and os.path.exists(path):
                os.remove(path)
        conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        conn.commit()
        return True

    def update_job_summary(self, job_id: str, summary_json: str) -> None:
        """Store summary data for a job."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE jobs SET summary_json=? WHERE id=?",
            (summary_json, job_id),
        )
        conn.commit()

    def index_transcript(self, job_id: str) -> bool:
        """Index a completed job's transcript into the vector store.

        Triggers chunking + vector upsert for the job's transcript.
        Returns True if indexing was successful, False otherwise.
        """
        job = self.get_job(job_id)
        if not job:
            return False
        if not job.get("full_text") or not job.get("transcript"):
            return False

        from .chunker import TextChunker
        from .embeddings import EmbeddingGenerator
        from .vector_store import VectorStore

        chunker = TextChunker()
        generator = EmbeddingGenerator()
        vector_store = VectorStore()

        # Convert dict segments to TranscriptSegment objects
        from .models import TranscriptSegment
        segments = [
            TranscriptSegment(**seg) for seg in job["transcript"]
        ]

        chunks = chunker.chunk(segments, job["full_text"], job_id)

        # Generate embeddings for all chunks
        for chunk in chunks:
            chunk.embedding = generator.generate(chunk.text)

        # Upsert into vector store
        vector_store.upsert(job_id, chunks)
        return True
