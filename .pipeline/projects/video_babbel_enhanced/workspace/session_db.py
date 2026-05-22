"""
session_db.py — SQLite persistence for clip flashcards and review history.

Stores:
    - clips: extracted video clips (metadata from clip JSON files)
    - reviews: spaced repetition review history
    - sessions: named drill sessions

Database schema:
    clips (id, clip_id, l1_text, l2_text, start, end, duration, freq_score,
           word_count, source_video, ease_factor, repetition, interval_days,
           due_date, last_review, last_quality, created_at)
    reviews (id, clip_id, quality, review_date, session_id)
    sessions (id, name, created_at, description)
"""
from __future__ import annotations
import json
import pathlib
import sqlite3
from datetime import datetime
from typing import Any

_DEFAULT_DB = "video_babbel.db"


def _connect(db_path: str | pathlib.Path) -> sqlite3.Connection:
    """Open a connection with WAL mode and foreign keys enabled."""
    db_path = pathlib.Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str | pathlib.Path = _DEFAULT_DB) -> sqlite3.Connection:
    """Initialize the database schema. Returns the connection."""
    conn = _connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clips (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id         TEXT UNIQUE NOT NULL,
            l1_text         TEXT NOT NULL,
            l2_text         TEXT NOT NULL,
            start           REAL NOT NULL,
            end             REAL NOT NULL,
            duration        REAL NOT NULL,
            freq_score      REAL NOT NULL,
            word_count      INTEGER NOT NULL,
            source_video    TEXT,
            ease_factor     REAL DEFAULT 2.5,
            repetition      INTEGER DEFAULT 0,
            interval_days   REAL DEFAULT 0,
            due_date        TEXT,
            last_review     TEXT,
            last_quality    INTEGER,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id         TEXT NOT NULL REFERENCES clips(clip_id),
            quality         INTEGER NOT NULL CHECK(quality BETWEEN 0 AND 5),
            review_date     TEXT NOT NULL,
            session_id      INTEGER REFERENCES sessions(id)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            description     TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_clips_due ON clips(due_date);
        CREATE INDEX IF NOT EXISTS idx_reviews_clip ON reviews(clip_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_session ON reviews(session_id);
    """)
    conn.commit()
    return conn


def import_clips_from_json(
    json_paths: list[str | pathlib.Path],
    db_path: str | pathlib.Path = _DEFAULT_DB,
) -> int:
    """Import clip metadata JSON files into the database.

    Args:
        json_paths: Paths to clip_NNN.json files.
        db_path: Database file path.

    Returns:
        Number of clips imported.
    """
    conn = _connect(db_path)
    imported = 0
    try:
        for jp in json_paths:
            jp = pathlib.Path(jp)
            if not jp.exists():
                continue
            meta = json.loads(jp.read_text(encoding="utf-8"))
            clip_id = meta.get("clip_id", jp.stem)
            conn.execute(
                """INSERT OR IGNORE INTO clips
                   (clip_id, l1_text, l2_text, start, end, duration,
                    freq_score, word_count, source_video, ease_factor,
                    repetition, interval_days, due_date, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 2.5, 0, 0, NULL, datetime('now'))""",
                (
                    clip_id,
                    meta.get("l1_text", ""),
                    meta.get("l2_text", ""),
                    meta.get("start", 0.0),
                    meta.get("end", 0.0),
                    meta.get("duration", 0.0),
                    meta.get("freq_score", 0.0),
                    meta.get("word_count", 0),
                    meta.get("source_video", ""),
                ),
            )
            imported += 1
        conn.commit()
    finally:
        conn.close()
    return imported


def upsert_clip(
    db_path: str | pathlib.Path,
    clip: dict[str, Any],
) -> None:
    """Insert or update a clip in the database.

    Args:
        db_path: Database file path.
        clip: Clip dict with keys like clip_id, l1_text, l2_text, start, end,
              duration, freq_score, word_count, source_video, etc.
    """
    conn = _connect(db_path)
    try:
        conn.execute(
            """INSERT OR REPLACE INTO clips
               (clip_id, l1_text, l2_text, start, end, duration,
                freq_score, word_count, source_video, ease_factor,
                repetition, interval_days, due_date, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 2.5, 0, 0, NULL, datetime('now'))""",
            (
                clip.get("clip_id", "unknown"),
                clip.get("l1_text", ""),
                clip.get("l2_text", ""),
                clip.get("start", clip.get("start_time", 0.0)),
                clip.get("end", clip.get("end_time", 0.0)),
                clip.get("duration", 0.0),
                clip.get("freq_score", 0.0),
                clip.get("word_count", 0),
                clip.get("source_video", ""),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_clips(db_path: str | pathlib.Path = _DEFAULT_DB) -> list[dict[str, Any]]:
    """Return all clips as list of dicts."""
    conn = _connect(db_path)
    try:
        rows = conn.execute("SELECT * FROM clips ORDER BY id").fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM clips LIMIT 1").description]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()


def get_due_clips(db_path: str | pathlib.Path = _DEFAULT_DB) -> list[dict[str, Any]]:
    """Return clips due for review (due_date <= now or no due_date)."""
    conn = _connect(db_path)
    try:
        now = datetime.now().isoformat()
        rows = conn.execute(
            """SELECT * FROM clips
               WHERE due_date IS NULL OR due_date <= ?
               ORDER BY due_date ASC, ease_factor ASC""",
            (now,),
        ).fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM clips LIMIT 1").description]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()


def get_new_clips(db_path: str | pathlib.Path = _DEFAULT_DB, limit: int = 20) -> list[dict[str, Any]]:
    """Return clips that have never been reviewed (no due_date)."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM clips WHERE due_date IS NULL ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM clips LIMIT 1").description]
        return [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()


def record_review(
    clip_id: str,
    quality: int,
    session_id: int | None = None,
    db_path: str | pathlib.Path = _DEFAULT_DB,
) -> dict[str, Any]:
    """Record a review and update the clip's scheduling data.

    Args:
        clip_id: The clip being reviewed.
        quality: Quality rating 0-5.
        session_id: Optional session ID to link the review.
        db_path: Database file path.

    Returns:
        Updated clip dict.
    """
    from video_babbel_enhanced.scheduler import schedule_review

    conn = _connect(db_path)
    try:
        # Get current clip data
        row = conn.execute("SELECT * FROM clips WHERE clip_id = ?", (clip_id,)).fetchone()
        if row is None:
            raise ValueError(f"Clip {clip_id} not found in database")

        cols = [d[0] for d in conn.execute("SELECT * FROM clips LIMIT 1").description]
        clip = dict(zip(cols, row))

        # Schedule next review
        now = datetime.now()
        clip = schedule_review(clip, quality, now)

        # Update clip in DB
        conn.execute(
            """UPDATE clips SET
                ease_factor = ?, repetition = ?, interval_days = ?,
                due_date = ?, last_review = ?, last_quality = ?
               WHERE clip_id = ?""",
            (
                clip["ease_factor"],
                clip["repetition"],
                clip["interval_days"],
                clip["due_date"],
                clip["last_review"],
                clip["last_quality"],
                clip_id,
            ),
        )

        # Record review
        conn.execute(
            """INSERT INTO reviews (clip_id, quality, review_date, session_id)
               VALUES (?, ?, ?, ?)""",
            (clip_id, quality, now.isoformat(), session_id),
        )
        conn.commit()

        # Return updated clip
        return clip
    finally:
        conn.close()


def create_session(
    name: str,
    description: str = "",
    db_path: str | pathlib.Path = _DEFAULT_DB,
) -> int:
    """Create a new drill session. Returns session ID."""
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO sessions (name, description) VALUES (?, ?)",
            (name, description),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_session_stats(db_path: str | pathlib.Path = _DEFAULT_DB) -> dict[str, Any]:
    """Get overall statistics."""
    conn = _connect(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
        due = conn.execute(
            "SELECT COUNT(*) FROM clips WHERE due_date IS NULL OR due_date <= ?",
            (datetime.now().isoformat(),),
        ).fetchone()[0]
        new = conn.execute("SELECT COUNT(*) FROM clips WHERE due_date IS NULL").fetchone()[0]
        mastered = conn.execute("SELECT COUNT(*) FROM clips WHERE repetition >= 5").fetchone()[0]
        reviews = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        avg_ef = conn.execute("SELECT AVG(ease_factor) FROM clips").fetchone()[0] or 2.5

        return {
            "total_clips": total,
            "due": due,
            "new": new,
            "mastered": mastered,
            "total_reviews": reviews,
            "avg_ease_factor": round(avg_ef, 2),
        }
    finally:
        conn.close()
