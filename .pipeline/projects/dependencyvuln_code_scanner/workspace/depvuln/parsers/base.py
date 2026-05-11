"""Base class for dependency parsers."""
from abc import ABC, abstractmethod
from typing import Any


class DependencyParser(ABC):
    """Abstract base class for dependency file parsers.

    Each concrete parser handles a specific package-manager lockfile format
    and returns a list of dependency dicts.
    """

    @abstractmethod
    def parse(self, filepath: str) -> list[dict[str, Any]]:
        """Parse a dependency file and return a list of dependency dicts.

        Each dict must contain:
            - name (str): package name
            - version (str): resolved version string
            - ecosystem (str): e.g. 'npm', 'pip'

        Returns an empty list if the file is missing, empty, or malformed.
        """
        ...
