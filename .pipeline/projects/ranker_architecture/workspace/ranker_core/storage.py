"""SQLite-backed persistent storage for the Ranker Architecture.

Provides TasteProfileStore backed by SQLite with schema migration support.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .profile import TasteProfile, TasteProfileValidationError


class StorageError(Exception):
    """Raised on storage backend errors."""


class SchemaError(StorageError):
    """Raised when schema validation or migration fails."""


# ---------------------------------------------------------------------------
# Schema management
# ---------------------------------------------------------------------------

CURRENT_SCHEMA_VERSION = 2

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS taste_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    taste_vector TEXT NOT NULL,
    metadata TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    domain_name TEXT,
    UNIQUE(user_id, domain_name)
);

CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    value REAL NOT NULL,
    weight REAL NOT NULL,
    timestamp TEXT NOT NULL,
    domain_name TEXT,
    FOREIGN KEY (user_id) REFERENCES taste_profiles(user_id)
);

CREATE TABLE IF NOT EXISTS schema_info (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);
"""

MIGRATION_V1_TO_V2 = """
ALTER TABLE taste_profiles ADD COLUMN domain_name TEXT;
ALTER TABLE signals ADD COLUMN domain_name TEXT;
"""


def _ensure_schema(conn: sqlite3.Connection, schema_version: int) -> None:
    """Ensure the database schema matches the current version.

    Args:
        conn: SQLite connection.
        schema_version: Expected schema version.

    Raises:
        SchemaError: If migration fails or schema is incompatible.
    """
    cursor = conn.cursor()

    # Check if schema_info table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_info'")
    if not cursor.fetchone():
        # Fresh database, create schema
        conn.executescript(SCHEMA_SQL)
        cursor.execute(
            "INSERT INTO schema_info (version, applied_at) VALUES (?, ?)",
            (CURRENT_SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return

    # Get current version
    cursor.execute("SELECT version FROM schema_info ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    if row is None:
        raise SchemaError("Schema info table is empty")
    current_version = row[0]

    if current_version == CURRENT_SCHEMA_VERSION:
        return

    if current_version == 1 and CURRENT_SCHEMA_VERSION == 2:
        # Apply migration V1 -> V2
        try:
            conn.executescript(MIGRATION_V1_TO_V2)
            cursor.execute(
                "INSERT INTO schema_info (version, applied_at) VALUES (?, ?)",
                (CURRENT_SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        except sqlite3.Error as e:
            raise SchemaError(f"Migration failed: {e}")
    else:
        raise SchemaError(f"Cannot migrate from version {current_version} to {CURRENT_SCHEMA_VERSION}")


# ---------------------------------------------------------------------------
# TasteProfileStore (SQLite-backed)
# ---------------------------------------------------------------------------

class TasteProfileStore:
    """SQLite-backed persistent store for taste profiles and signals.

    Attributes:
        db_path: Path to the SQLite database file.
        conn: SQLite connection (lazy-initialized).
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Get or create the database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            _ensure_schema(self._conn, CURRENT_SCHEMA_VERSION)
        return self._conn

    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # -- Profile CRUD ------------------------------------------------------

    def create_profile(self, profile: TasteProfile, domain_name: Optional[str] = None) -> None:
        """Create or update a taste profile.

        Args:
            profile: TasteProfile to persist.
            domain_name: Optional domain name for the profile.

        Raises:
            TasteProfileValidationError: If profile is invalid.
            StorageError: On database errors.
        """
        if not isinstance(profile, TasteProfile):
            raise TasteProfileValidationError("profile must be a TasteProfile instance")

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO taste_profiles (id, user_id, taste_vector, metadata, created_at, updated_at, domain_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, domain_name) DO UPDATE SET
                taste_vector = excluded.taste_vector,
                metadata = excluded.metadata,
                updated_at = excluded.updated_at
            """,
            (
                profile.id,
                profile.user_id,
                json.dumps(profile.taste_vector),
                json.dumps(profile.metadata),
                profile.created_at.isoformat(),
                profile.updated_at.isoformat(),
                domain_name,
            ),
        )

    def get_profile(self, user_id: str, domain_name: Optional[str] = None) -> Optional[TasteProfile]:
        """Retrieve a taste profile by user_id and optional domain.

        Args:
            user_id: User identifier.
            domain_name: Optional domain name.

        Returns:
            TasteProfile if found, None otherwise.
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM taste_profiles WHERE user_id = ?"
        params: list = [user_id]
        if domain_name is not None:
            query += " AND domain_name = ?"
            params.append(domain_name)

        cursor.execute(query, params)
        row = cursor.fetchone()
        if row is None:
            return None

        return self._row_to_profile(row)

    def update_profile(self, profile: TasteProfile, domain_name: Optional[str] = None) -> None:
        """Update an existing taste profile.

        Args:
            profile: Updated TasteProfile.
            domain_name: Optional domain name.

        Raises:
            TasteProfileValidationError: If profile is invalid.
            StorageError: If profile doesn't exist.
        """
        existing = self.get_profile(profile.user_id, domain_name)
        if existing is None:
            raise StorageError(f"Profile not found for user_id={profile.user_id}, domain={domain_name}")
        self.create_profile(profile, domain_name)

    def delete_profile(self, user_id: str, domain_name: Optional[str] = None) -> bool:
        """Delete a taste profile.

        Args:
            user_id: User identifier.
            domain_name: Optional domain name.

        Returns:
            True if deleted, False if not found.
        """
        cursor = self.conn.cursor()
        query = "DELETE FROM taste_profiles WHERE user_id = ?"
        params: list = [user_id]
        if domain_name is not None:
            query += " AND domain_name = ?"
            params.append(domain_name)

        cursor.execute(query, params)
        return cursor.rowcount > 0

    def list_profiles(self, domain_name: Optional[str] = None) -> List[TasteProfile]:
        """List all taste profiles, optionally filtered by domain.

        Args:
            domain_name: Optional domain name filter.

        Returns:
            List of TasteProfile instances.
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM taste_profiles"
        params: list = []
        if domain_name is not None:
            query += " WHERE domain_name = ?"
            params.append(domain_name)

        cursor.execute(query, params)
        return [self._row_to_profile(row) for row in cursor.fetchall()]

    def _row_to_profile(self, row: sqlite3.Row) -> TasteProfile:
        """Convert a database row to a TasteProfile."""
        return TasteProfile(
            user_id=row["user_id"],
            taste_vector=json.loads(row["taste_vector"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            id=row["id"],
        )

    # -- Signal CRUD ------------------------------------------------------

    def add_signal(self, signal_data: Dict[str, Any], domain_name: Optional[str] = None) -> None:
        """Add a signal to the database.

        Args:
            signal_data: Dictionary with signal fields.
            domain_name: Optional domain name.

        Raises:
            StorageError: On database errors.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO signals (id, user_id, tool_id, item_id, signal_type, value, weight, timestamp, domain_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_data["id"],
                signal_data["user_id"],
                signal_data["tool_id"],
                signal_data["item_id"],
                signal_data["signal_type"],
                signal_data["value"],
                signal_data["weight"],
                signal_data["timestamp"],
                domain_name,
            ),
        )

    def get_signals(
        self,
        user_id: Optional[str] = None,
        domain_name: Optional[str] = None,
        tool_id: Optional[str] = None,
        signal_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve signals with optional filters.

        Args:
            user_id: Filter by user.
            domain_name: Filter by domain.
            tool_id: Filter by tool.
            signal_type: Filter by signal type.

        Returns:
            List of signal dictionaries.
        """
        cursor = self.conn.cursor()
        query = "SELECT * FROM signals WHERE 1=1"
        params: list = []

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        if domain_name is not None:
            query += " AND domain_name = ?"
            params.append(domain_name)
        if tool_id is not None:
            query += " AND tool_id = ?"
            params.append(tool_id)
        if signal_type is not None:
            query += " AND signal_type = ?"
            params.append(signal_type)

        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def delete_signals(self, user_id: str, domain_name: Optional[str] = None) -> int:
        """Delete all signals for a user and optional domain.

        Args:
            user_id: User identifier.
            domain_name: Optional domain name.

        Returns:
            Number of signals deleted.
        """
        cursor = self.conn.cursor()
        query = "DELETE FROM signals WHERE user_id = ?"
        params: list = [user_id]
        if domain_name is not None:
            query += " AND domain_name = ?"
            params.append(domain_name)

        cursor.execute(query, params)
        return cursor.rowcount

    # -- Schema management ----------------------------------------------------

    def get_schema_version(self) -> int:
        """Get the current schema version."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT version FROM schema_info ORDER BY version DESC LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            return 0
        return row[0]

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> TasteProfileStore:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
