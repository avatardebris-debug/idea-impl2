"""Abstract base class for all data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class DataSource(ABC, Generic[T]):
    """Abstract base class defining the contract for data sources.

    Every concrete data source must implement:
    - ``query()`` — filter records by criteria
    - ``fetch_all()`` — return all records
    """

    @abstractmethod
    def query(self, **kwargs) -> list[T]:
        """Query records with optional filters.

        Subclasses define accepted keyword arguments.
        Returns a list of matching records.
        """
        ...

    @abstractmethod
    def fetch_all(self) -> list[T]:
        """Return all records from the source."""
        ...

    @abstractmethod
    def get_by_id(self, record_id: str) -> T | None:
        """Retrieve a single record by its unique identifier.

        Returns None if not found.
        """
        ...
