"""
pipeline/message_bus.py
SQLite-WAL message queue for inter-agent communication.

Strategy 2 (PufferLib-inspired): replaced the original file-based JSONL queue
with a single SQLite database in WAL mode.  SQLite WAL allows concurrent
readers + one writer without locking, provides sub-millisecond notification,
and eliminates the JSONL parse + file-lock overhead on every poll.

PufferLib analogy: "Replace multiprocessing.Queue with Pipe (3-10× faster),
then replace Pipe with shared Array."  We go one step further — SQLite gives us
a durable, queryable, zero-copy store that also handles crash recovery.

API is 100% backward-compatible with the original MessageBus — no other files
need changes.

Thread/process safety: SQLite's WAL mode handles concurrent access natively.
We use WAL + NORMAL synchronisation for maximum throughput (data survives
crashes, no OS-level fsync stall per write).
"""

from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from pipeline.paths import message_bus_db, queues_dir

# ---------------------------------------------------------------------------
# Message data model  (unchanged from original)
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """A single message in the pipeline queue."""
    msg_id:      str  = ""
    from_agent:  str  = ""
    to_agent:    str  = ""
    type:        str  = "task"       # task | result | signal | context
    priority:    int  = 1            # 1=normal, 0=emergency
    payload:     dict = field(default_factory=dict)
    created_at:  str  = ""
    in_reply_to: str  = ""
    status:      str  = "pending"    # pending | processing | done | failed

    def __post_init__(self):
        if not self.msg_id:
            self.msg_id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def create(
        cls,
        from_agent: str,
        to_agent:   str,
        type:       str  = "task",
        payload:    dict | None = None,
        priority:   int  = 1,
        in_reply_to: str = "",
    ) -> "Message":
        return cls(
            from_agent=from_agent,
            to_agent=to_agent,
            type=type,
            payload=payload or {},
            priority=priority,
            in_reply_to=in_reply_to,
        )


# ---------------------------------------------------------------------------
# SQLite connection pool (one connection per thread for thread safety)
# ---------------------------------------------------------------------------

_local = threading.local()


def _get_conn(db_path: pathlib.Path) -> sqlite3.Connection:
    """Return a thread-local SQLite connection, creating it if needed."""
    conn = getattr(_local, "conn", None)
    db_str = str(db_path)
    if conn is None or getattr(_local, "db_path", None) != db_str:
        conn = sqlite3.connect(db_str, check_same_thread=False, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")   # safe + fast
        conn.execute("PRAGMA cache_size=-8000")     # 8 MB page cache
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.row_factory = sqlite3.Row
        _local.conn = conn
        _local.db_path = db_str
    return conn


def _init_db(db_path: pathlib.Path) -> None:
    """Create the messages table if it doesn't exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            rowid      INTEGER PRIMARY KEY AUTOINCREMENT,
            msg_id     TEXT NOT NULL,
            from_agent TEXT NOT NULL,
            to_agent   TEXT NOT NULL,
            type       TEXT NOT NULL DEFAULT 'task',
            priority   INTEGER NOT NULL DEFAULT 1,
            payload    TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            in_reply_to TEXT NOT NULL DEFAULT '',
            status     TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_to_status ON messages(to_agent, status, priority, created_at)")
    conn.commit()


# ---------------------------------------------------------------------------
# MessageBus  (same public API as original)
# ---------------------------------------------------------------------------

class MessageBus:
    """SQLite-WAL message queue for the agent pipeline.

    Replaces the original file-based JSONL queue.  All callers use the same
    public API (send, read_next, ack, nack, fail, peek, etc.) — no other
    files need updating.
    """

    def __init__(self, base_dir: pathlib.Path | None = None):
        # base_dir kept for API compat — we don't use it (single shared DB)
        self.base_dir = base_dir or queues_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._db = message_bus_db()
        _init_db(self._db)

    # ------------------------------------------------------------------
    # Core send / receive
    # ------------------------------------------------------------------

    def send(self, msg: Message) -> None:
        """Insert a message into the queue."""
        conn = _get_conn(self._db)
        conn.execute(
            """INSERT INTO messages
               (msg_id, from_agent, to_agent, type, priority, payload,
                created_at, in_reply_to, status)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (msg.msg_id, msg.from_agent, msg.to_agent, msg.type,
             msg.priority, json.dumps(msg.payload),
             msg.created_at, msg.in_reply_to, "pending"),
        )
        conn.commit()

    def read_next(self, agent_name: str) -> Message | None:
        """Atomically claim the next pending message (FIFO, priority-aware).

        Returns None if no pending messages exist.
        Uses a BEGIN IMMEDIATE transaction to prevent two agents from
        claiming the same message under concurrent access.
        """
        conn = _get_conn(self._db)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """SELECT rowid, * FROM messages
                   WHERE to_agent=? AND status='pending'
                   ORDER BY priority ASC, created_at ASC
                   LIMIT 1""",
                (agent_name,),
            ).fetchone()
            if row is None:
                conn.execute("ROLLBACK")
                return None
            conn.execute(
                "UPDATE messages SET status='processing' WHERE rowid=?",
                (row["rowid"],),
            )
            conn.execute("COMMIT")
        except sqlite3.OperationalError:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            return None

        return Message(
            msg_id      = row["msg_id"],
            from_agent  = row["from_agent"],
            to_agent    = row["to_agent"],
            type        = row["type"],
            priority    = row["priority"],
            payload     = json.loads(row["payload"]),
            created_at  = row["created_at"],
            in_reply_to = row["in_reply_to"],
            status      = "processing",
        )

    def ack(self, msg: Message) -> None:
        """Mark message done."""
        self._set_status(msg.msg_id, "done")

    def nack(self, msg: Message, increment_retry: bool = True) -> None:
        """Return message to pending for retry. Optionally increments retry_count in payload."""
        conn = _get_conn(self._db)
        try:
            # First fetch the existing payload to ensure we preserve other fields
            row = conn.execute(
                "SELECT payload FROM messages WHERE msg_id=?", (msg.msg_id,)
            ).fetchone()
            if row:
                payload = json.loads(row["payload"])
            else:
                payload = msg.payload or {}
            
            if increment_retry:
                payload["retry_count"] = payload.get("retry_count", 0) + 1
                msg.payload["retry_count"] = payload["retry_count"]
            
            conn.execute(
                "UPDATE messages SET status='pending', payload=? WHERE msg_id=?",
                (json.dumps(payload), msg.msg_id)
            )
            conn.commit()
        except Exception:
            # Fallback to simple set status if anything fails
            self._set_status(msg.msg_id, "pending")


    def fail(self, msg: Message) -> None:
        """Mark message permanently failed."""
        self._set_status(msg.msg_id, "failed")

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def peek(self, agent_name: str) -> list[Message]:
        """Return all pending messages without consuming them."""
        conn = _get_conn(self._db)
        rows = conn.execute(
            """SELECT * FROM messages
               WHERE to_agent=? AND status='pending'
               ORDER BY priority ASC, created_at ASC""",
            (agent_name,),
        ).fetchall()
        return [self._row_to_msg(r) for r in rows]

    def queue_depth(self, agent_name: str) -> int:
        conn = _get_conn(self._db)
        row = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE to_agent=? AND status='pending'",
            (agent_name,),
        ).fetchone()
        return row[0] if row else 0

    def all_queues_empty(self, exclude: list[str] | None = None) -> bool:
        """True if no pending messages exist (optionally excluding agents)."""
        conn = _get_conn(self._db)
        if exclude:
            placeholders = ",".join("?" * len(exclude))
            row = conn.execute(
                f"SELECT COUNT(*) FROM messages WHERE status='pending' AND to_agent NOT IN ({placeholders})",
                exclude,
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE status='pending'",
            ).fetchone()
        return (row[0] if row else 0) == 0

    def has_active_work(self) -> bool:
        """True if any pending OR processing messages exist."""
        conn = _get_conn(self._db)
        row = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE status IN ('pending','processing')",
        ).fetchone()
        return (row[0] if row else 0) > 0

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def send_signal(
        self,
        from_agent: str,
        to_agent:   str,
        signal:     str,
        payload:    dict | None = None,
        priority:   int = 1,
    ) -> None:
        msg = Message.create(
            from_agent=from_agent,
            to_agent=to_agent,
            type="signal",
            payload={"signal": signal, **(payload or {})},
            priority=priority,
        )
        self.send(msg)

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def clear_queue(self, agent_name: str) -> int:
        """Delete all messages for an agent. Returns count removed."""
        conn = _get_conn(self._db)
        cur = conn.execute(
            "DELETE FROM messages WHERE to_agent=?", (agent_name,)
        )
        conn.commit()
        return cur.rowcount

    def compact(self, agent_name: str) -> int:
        """Delete done/failed messages for an agent. Returns count removed."""
        conn = _get_conn(self._db)
        cur = conn.execute(
            "DELETE FROM messages WHERE to_agent=? AND status IN ('done','failed')",
            (agent_name,),
        )
        conn.commit()
        return cur.rowcount

    def compact_all(self) -> int:
        """Delete all done/failed messages across all agents."""
        conn = _get_conn(self._db)
        cur = conn.execute(
            "DELETE FROM messages WHERE status IN ('done','failed')"
        )
        conn.commit()
        return cur.rowcount

    def reset_stale_processing(self) -> int:
        """Reset 'processing' → 'pending' (called at startup after a crash)."""
        conn = _get_conn(self._db)
        cur = conn.execute(
            "UPDATE messages SET status='pending' WHERE status='processing'"
        )
        conn.commit()
        return cur.rowcount

    def get_processing_messages(self) -> list:
        """Return all messages currently in 'processing' state (for stall diagnostics)."""
        conn = _get_conn(self._db)
        rows = conn.execute(
            "SELECT * FROM messages WHERE status='processing' ORDER BY created_at"
        ).fetchall()
        return [self._row_to_msg(r) for r in rows]


    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg_id: str, status: str) -> None:
        conn = _get_conn(self._db)
        conn.execute(
            "UPDATE messages SET status=? WHERE msg_id=?", (status, msg_id)
        )
        conn.commit()

    @staticmethod
    def _row_to_msg(row: sqlite3.Row) -> Message:
        return Message(
            msg_id      = row["msg_id"],
            from_agent  = row["from_agent"],
            to_agent    = row["to_agent"],
            type        = row["type"],
            priority    = row["priority"],
            payload     = json.loads(row["payload"]),
            created_at  = row["created_at"],
            in_reply_to = row["in_reply_to"],
            status      = row["status"],
        )

    # ------------------------------------------------------------------
    # Legacy JSONL migration  (one-shot, called at first startup)
    # ------------------------------------------------------------------

    def migrate_from_jsonl(self) -> int:
        """Import any legacy .jsonl queue files into the SQLite DB.

        Safe to call multiple times — already-imported messages are skipped
        via INSERT OR IGNORE (msg_id uniqueness).
        Returns count of messages imported.
        """
        if not queues_dir().exists():
            return 0
        conn = _get_conn(self._db)
        # Ensure msg_id uniqueness for idempotent re-import
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_msg_id ON messages(msg_id)"
        )
        conn.commit()
        imported = 0
        for qf in queues_dir().glob("*.jsonl"):
            try:
                with open(qf, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            d = json.loads(line)
                            conn.execute(
                                """INSERT OR IGNORE INTO messages
                                   (msg_id, from_agent, to_agent, type, priority,
                                    payload, created_at, in_reply_to, status)
                                   VALUES (?,?,?,?,?,?,?,?,?)""",
                                (d.get("msg_id",""), d.get("from_agent",""),
                                 d.get("to_agent",""), d.get("type","task"),
                                 d.get("priority",1), json.dumps(d.get("payload",{})),
                                 d.get("created_at",""), d.get("in_reply_to",""),
                                 d.get("status","pending")),
                            )
                            imported += 1
                        except Exception:
                            continue
            except Exception:
                continue
        conn.commit()
        return imported
