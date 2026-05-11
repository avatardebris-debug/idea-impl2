"""SQLite database layer for manuscript analytics data."""

import os
import sqlite3
from typing import Any


# ── Schema definitions ──────────────────────────────────────────────

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS sales_data (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT,
    book_title  TEXT,
    units_sold  INTEGER,
    revenue     REAL,
    platform    TEXT
);

CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_data(date);
CREATE INDEX IF NOT EXISTS idx_sales_book ON sales_data(book_title);
CREATE INDEX IF NOT EXISTS idx_sales_platform ON sales_data(platform);

CREATE TABLE IF NOT EXISTS demographics_data (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    age_group    TEXT,
    gender       TEXT,
    country      TEXT,
    rating       REAL,
    review_count INTEGER
);

CREATE INDEX IF NOT EXISTS idx_demo_age ON demographics_data(age_group);
CREATE INDEX IF NOT EXISTS idx_demo_gender ON demographics_data(gender);
CREATE INDEX IF NOT EXISTS idx_demo_country ON demographics_data(country);

CREATE TABLE IF NOT EXISTS content_metrics (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter           INTEGER,
    word_count        INTEGER,
    read_through_rate REAL,
    completion_rate   REAL
);

CREATE INDEX IF NOT EXISTS idx_content_chapter ON content_metrics(chapter);
"""


class Database:
    """Manages the SQLite database for manuscript analytics."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "manuscript_data.db")
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    # ── Connection lifecycle ────────────────────────────────────────

    def connect(self) -> None:
        """Open the database and ensure all tables exist."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(CREATE_TABLES_SQL)
        self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Insert helpers ──────────────────────────────────────────────

    def insert_records(self, data_type: str, records: list[dict[str, Any]]) -> int:
        """Insert a list of record dicts into the appropriate table.

        Parameters
        ----------
        data_type : str
            One of ``'sales_data'``, ``'demographics_data'``, ``'content_metrics'``.
        records : list[dict]
            Each dict must have keys matching the table columns (minus ``id``).

        Returns
        -------
        int
            Number of rows inserted.
        """
        if not self._conn:
            raise RuntimeError("Database not connected. Call connect() first.")

        table_map = {
            "sales_data": "sales_data",
            "demographics_data": "demographics_data",
            "content_metrics": "content_metrics",
        }
        table = table_map.get(data_type)
        if table is None:
            raise ValueError(f"Unknown data_type: {data_type!r}")

        if not records:
            return 0

        columns = list(records[0].keys())
        placeholders = ", ".join("?" for _ in columns)
        col_names = ", ".join(columns)
        sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

        values = [tuple(r[col] for col in columns) for r in records]
        self._conn.executemany(sql, values)
        self._conn.commit()
        return len(values)

    # ── Query helpers ───────────────────────────────────────────────

    def get_sales_summary(self) -> dict[str, Any] | None:
        """Return summary stats for sales_data, or None if empty."""
        if not self._conn:
            raise RuntimeError("Database not connected.")
        cur = self._conn.execute(
            "SELECT COUNT(*) AS cnt, "
            "       COALESCE(SUM(units_sold),0) AS total_units, "
            "       COALESCE(SUM(revenue),0) AS total_revenue, "
            "       COALESCE(AVG(revenue),0) AS avg_revenue, "
            "       COALESCE(AVG(units_sold),0) AS avg_units "
            "FROM sales_data"
        )
        row = cur.fetchone()
        if row is None or row[0] == 0:
            return None

        result = {
            "record_count": row[0],
            "total_units": row[1],
            "total_revenue": row[2],
            "avg_revenue": row[3],
            "avg_units": row[4],
        }

        # Platform breakdown
        cur2 = self._conn.execute(
            "SELECT platform, COUNT(*) AS cnt, "
            "       SUM(units_sold) AS units, SUM(revenue) AS rev "
            "FROM sales_data GROUP BY platform ORDER BY rev DESC"
        )
        result["platform_breakdown"] = {
            r[0]: {"count": r[1], "units": r[2], "revenue": r[3]}
            for r in cur2.fetchall()
        }
        return result

    def get_demographics_summary(self) -> dict[str, Any] | None:
        """Return summary stats for demographics_data, or None if empty."""
        if not self._conn:
            raise RuntimeError("Database not connected.")
        cur = self._conn.execute("SELECT COUNT(*) FROM demographics_data")
        total = cur.fetchone()[0]
        if total == 0:
            return None

        result = {"total_records": total}

        # Age breakdown
        cur_age = self._conn.execute(
            "SELECT age_group, COUNT(*) AS cnt, AVG(rating) AS avg_rating "
            "FROM demographics_data GROUP BY age_group ORDER BY cnt DESC"
        )
        result["age_breakdown"] = {
            r[0]: {"count": r[1], "pct": r[1] / total * 100, "avg_rating": r[2]}
            for r in cur_age.fetchall()
        }

        # Gender breakdown
        cur_gender = self._conn.execute(
            "SELECT gender, COUNT(*) AS cnt, AVG(rating) AS avg_rating "
            "FROM demographics_data GROUP BY gender ORDER BY cnt DESC"
        )
        result["gender_breakdown"] = {
            r[0]: {"count": r[1], "pct": r[1] / total * 100, "avg_rating": r[2]}
            for r in cur_gender.fetchall()
        }

        # Country breakdown
        cur_country = self._conn.execute(
            "SELECT country, COUNT(*) AS cnt, AVG(rating) AS avg_rating "
            "FROM demographics_data GROUP BY country ORDER BY cnt DESC"
        )
        result["country_breakdown"] = {
            r[0]: {"count": r[1], "pct": r[1] / total * 100, "avg_rating": r[2]}
            for r in cur_country.fetchall()
        }

        return result

    def get_content_metrics_summary(self) -> dict[str, Any] | None:
        """Return summary stats for content_metrics, or None if empty."""
        if not self._conn:
            raise RuntimeError("Database not connected.")
        cur = self._conn.execute(
            "SELECT COUNT(*) AS cnt, "
            "       SUM(word_count) AS total_words, "
            "       AVG(word_count) AS avg_words, "
            "       AVG(read_through_rate) AS avg_read_through, "
            "       AVG(completion_rate) AS avg_completion "
            "FROM content_metrics"
        )
        row = cur.fetchone()
        if row is None or row[0] == 0:
            return None

        result = {
            "total_chapters": row[0],
            "total_words": row[1],
            "avg_words": row[2],
            "avg_read_through": row[3],
            "avg_completion": row[4],
        }

        # Chapter-level details
        cur2 = self._conn.execute(
            "SELECT chapter, word_count, read_through_rate, completion_rate "
            "FROM content_metrics ORDER BY chapter"
        )
        result["chapter_details"] = [
            {
                "chapter": r[0],
                "word_count": r[1],
                "read_through": r[2],
                "completion": r[3],
            }
            for r in cur2.fetchall()
        ]
        return result

    # ──────────────────────────────────────────────
    # Trend / Comparison helpers (Phase 2)
    # ──────────────────────────────────────────────

    def get_unique_books(self) -> list[str]:
        """Return a list of unique book titles from sales data."""
        if not self._conn:
            raise RuntimeError("Database not connected.")
        rows = self._execute("SELECT DISTINCT book_title FROM sales_data ORDER BY book_title")
        return [r[0] for r in rows]

    def get_book_sales_series(self, book_title: str) -> list[dict[str, Any]]:
        """Return daily sales records for *book_title*, ordered by date."""
        if not self._conn:
            raise RuntimeError("Database not connected.")
        rows = self._execute(
            "SELECT date, book_title, units_sold, revenue FROM sales_data WHERE book_title = ? ORDER BY date",
            (book_title,),
        )
        return [
            {"date": r[0], "book_title": r[1], "units_sold": r[2], "revenue": r[3]}
            for r in rows
        ]

    def get_book_ranking(self, metric: str = "revenue") -> list[dict[str, Any]]:
        """Return books ranked by *metric* (``'revenue'`` or ``'units_sold'``)."""
        valid = {"revenue", "units_sold"}
        if metric not in valid:
            raise ValueError(f"metric must be one of {valid}")
        col = "SUM(revenue)" if metric == "revenue" else "SUM(units_sold)"
        rows = self._execute(
            f"SELECT book_title, {col} as total FROM sales_data GROUP BY book_title ORDER BY total DESC"
        )
        return [{"book_title": r[0], metric: r[1]} for r in rows]

    def get_book_engagement(self) -> list[dict[str, Any]]:
        """Return books ranked by average reader engagement (rating from demographics).

        Uses demographics rating data as a proxy for engagement.
        """
        if not self._conn:
            raise RuntimeError("Database not connected.")
        cur = self._conn.execute(
            "SELECT book_title, AVG(units_sold) AS avg_engagement, COUNT(*) AS cnt "
            "FROM sales_data GROUP BY book_title ORDER BY avg_engagement DESC"
        )
        return [
            {"book_title": r[0], "engagement": round(r[1], 2)}
            for r in cur.fetchall()
        ]

    def _execute(self, query: str, params: tuple = ()) -> list[tuple]:
        """Execute a query and return all rows."""
        if not self._conn:
            raise RuntimeError("Database not connected.")
        cur = self._conn.execute(query, params)
        return cur.fetchall()