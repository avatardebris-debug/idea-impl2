"""Corporate registry data source."""

from __future__ import annotations

import os
import json
import pathlib
from typing import Optional

from osint_corp.models.entities import Company


class CorporateRegistry:
    """Local or remote corporate registry for company lookups."""

    def __init__(self):
        self._cache: dict[str, Company] = {}

    def search_by_name(
        self,
        name: str,
        limit: int = 10,
        output_dir: Optional[str] = None,
    ) -> list[Company]:
        """Search the corporate registry by company name.

        Returns a list of matching Company objects.
        """
        # In a real implementation, this would query a database or API.
        # For now, return an empty list (placeholder for external registry).
        results: list[Company] = []

        if output_dir:
            pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
            cache_file = pathlib.Path(output_dir) / "corporate_registry_cache.json"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                for entry in cache_data:
                    if name.lower() in entry.get("name", "").lower():
                        results.append(Company.from_dict(entry))
                        if len(results) >= limit:
                            break

        return results

    def search_by_cik(self, cik: str) -> Optional[Company]:
        """Look up a company by CIK number."""
        if cik in self._cache:
            return self._cache[cik]
        return None

    def add_company(self, company: Company) -> None:
        """Add a company to the local cache."""
        if company.cik:
            self._cache[company.cik] = company
        if company.ticker:
            self._cache[company.ticker] = company
