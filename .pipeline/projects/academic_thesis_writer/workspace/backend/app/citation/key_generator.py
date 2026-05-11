"""Citation key generator.

Produces deterministic, collision-free citation keys (e.g. "AuthorYear")
from source metadata.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional, Set

from ..models import Source


class KeyGenerator:
    """Generate unique citation keys for sources."""

    def __init__(self):
        self._keys: Set[str] = set()

    def generate_key(self, source: Source) -> str:
        """Generate a unique citation key for a source."""
        base = self._make_base_key(source)
        key = self._ensure_unique(base)
        self._keys.add(key)
        return key

    def generate_keys(self, sources: List[Source]) -> Dict[Source, str]:
        """Generate unique keys for multiple sources."""
        return {s: self.generate_key(s) for s in sources}

    def _make_base_key(self, source: Source) -> str:
        """Create a base key from author and year."""
        author = source.authors[0].split()[-1] if source.authors else "Unknown"
        year = str(source.year) if source.year else "n"
        return f"{author}{year}"

    def _ensure_unique(self, base: str) -> str:
        """Ensure the key is unique by appending a hash if needed."""
        if base not in self._keys:
            return base
        # Append a short hash to make it unique
        hash_suffix = hashlib.md5(base.encode()).hexdigest()[:4]
        key = f"{base}_{hash_suffix}"
        while key in self._keys:
            hash_suffix = hashlib.md5(hash_suffix.encode()).hexdigest()[:4]
            key = f"{base}_{hash_suffix}"
        return key
