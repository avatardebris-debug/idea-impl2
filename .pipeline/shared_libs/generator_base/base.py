"""Base generator interface for DocsAI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseGenerator(ABC):
    """Abstract base class for API spec generators."""

    @abstractmethod
    def generate(self, symbols: List[Dict[str, Any]], output_format: str = "yaml") -> str:
        """Generate an API spec from parsed symbol data.

        Args:
            symbols: List of parsed symbol dicts from a parser.
            output_format: 'yaml' or 'json'.

        Returns:
            A string containing the formatted API spec.
        """
        ...
