"""
pipeline/capability_search.py
Phase 6 optional: FTS5 text search over capability purpose/title (no external embeddings).
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from pipeline.capability_registry import _connect
from pipeline.paths import registry_db
from pipeline.pipeline_mode import legacy_mode

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS capabilities_fts USING fts5(
    slug UNINDEXED,
    title,
    purpose,
    tokenize='porter'
);
"""


def rebuild_fts_index(conn: sqlite3.Connection | None = None) -> int:
    """Rebuild FTS from verified capabilities (title + purpose)."""
    if legacy_mode():
        return 0
    own = conn is None
    if own:
        conn = _connect()
    conn.executescript(FTS_SCHEMA)
    conn.execute("DELETE FROM capabilities_fts")
    rows = conn.execute(
        """
        SELECT slug, title, purpose FROM capabilities
        WHERE status = 'verified'
        """
    ).fetchall()
    n = 0
    for row in rows:
        text = f"{row['title'] or ''} {(row['purpose'] or '')[:2000]}"
        conn.execute(
            "INSERT INTO capabilities_fts (slug, title, purpose) VALUES (?, ?, ?)",
            (row["slug"], row["title"] or "", text),
        )
        n += 1
    if own:
        conn.commit()
        conn.close()
    return n


def _fts_query(task_text: str) -> str:
    words = re.findall(r"[a-z0-9_]{3,}", task_text.lower())
    if not words:
        return ""
    # OR-join for recall; FTS5 handles porter stemming
    return " OR ".join(words[:12])


def search_capabilities(
    task_text: str,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return [{slug, fts_rank}, ...] or [] if FTS unavailable."""
    if legacy_mode() or not registry_db().exists():
        return []
    q = _fts_query(task_text)
    if not q:
        return []
    try:
        conn = _connect()
        conn.executescript(FTS_SCHEMA)
        rows = conn.execute(
            """
            SELECT slug, bm25(capabilities_fts) AS rank
            FROM capabilities_fts
            WHERE capabilities_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (q, limit),
        ).fetchall()
        conn.close()
        return [{"slug": r["slug"], "fts_rank": float(r["rank"])} for r in rows]
    except sqlite3.OperationalError:
        return []
