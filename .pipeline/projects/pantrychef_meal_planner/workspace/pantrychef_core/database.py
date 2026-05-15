"""Database module with SQLite connection management.

This module re-exports the canonical Database implementation from the inner
package so that both ``from pantrychef_core.database import Database`` and
``from pantrychef_core.pantrychef_core.database import Database`` resolve to
the same, test-compatible class.
"""

from pantrychef_core.pantrychef_core.database import Database  # noqa: F401

__all__ = ["Database"]
