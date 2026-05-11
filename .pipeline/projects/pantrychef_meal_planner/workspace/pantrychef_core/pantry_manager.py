"""PantryManager — CRUD operations for pantry items."""

from __future__ import annotations

from datetime import date
from typing import Optional

from .models import PantryItem
from .database import Database


class PantryManager:
    """Manage pantry items backed by SQLite."""

    def __init__(self, db: Database | None = None):
        self.db = db or Database()
        self.db.init_db()

    def add_item(
        self,
        name: str,
        quantity: float,
        unit: str,
        category: str,
        expiry_date: date | None = None,
    ) -> PantryItem:
        """Insert a pantry item and return it."""
        with self.db.get_connection_ctx() as conn:
            cursor = conn.execute(
                "INSERT INTO pantry_items (name, quantity, unit, category, expiry_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, quantity, unit, category, expiry_date.isoformat() if expiry_date else None),
            )
            conn.commit()
            return PantryItem(
                id=cursor.lastrowid,
                name=name,
                quantity=quantity,
                unit=unit,
                category=category,
                expiry_date=expiry_date,
            )

    def remove_item(self, item_id: int) -> bool:
        """Delete a pantry item by id. Returns True if deleted."""
        with self.db.get_connection_ctx() as conn:
            cursor = conn.execute(
                "DELETE FROM pantry_items WHERE id = ?", (item_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_items(self) -> list[PantryItem]:
        """Return all pantry items."""
        with self.db.get_connection_ctx() as conn:
            rows = conn.execute(
                "SELECT id, name, quantity, unit, category, expiry_date FROM pantry_items"
            ).fetchall()
        items = []
        for row in rows:
            items.append(
                PantryItem(
                    id=row[0],
                    name=row[1],
                    quantity=row[2],
                    unit=row[3],
                    category=row[4],
                    expiry_date=date.fromisoformat(row[5]) if row[5] else None,
                )
            )
        return items

    def get_item(self, item_id: int) -> Optional[PantryItem]:
        """Return a pantry item by id, or None."""
        with self.db.get_connection_ctx() as conn:
            row = conn.execute(
                "SELECT id, name, quantity, unit, category, expiry_date FROM pantry_items WHERE id = ?",
                (item_id,),
            ).fetchone()
        if row is None:
            return None
        return PantryItem(
            id=row[0],
            name=row[1],
            quantity=row[2],
            unit=row[3],
            category=row[4],
            expiry_date=date.fromisoformat(row[5]) if row[5] else None,
        )
