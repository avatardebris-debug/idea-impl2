"""Base parser interface for DocsAI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseParser(ABC):
    """Abstract base class for source code parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a source file and return a list of symbol dicts.

        Each symbol dict must contain:
            - name: str
            - kind: str (function/class/method/interface/enum)
            - params: list of {name: str, type: str}
            - return_type: str
            - docstring: str
            - line_number: int
        """
        ...
