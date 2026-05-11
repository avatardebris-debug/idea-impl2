"""Merge and deduplicate CVE data from OSV and NVD sources."""
from typing import Any


class CveDataMerger:
    """Merge CVE data from multiple sources (OSV, NVD) with deduplication."""

    def merge(self, osv_results: list[dict[str, Any]], nvd_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Merge OSV and NVD results, deduplicating by CVE ID.

        OSV results take precedence (more detailed). NVD fills in gaps.

        Args:
            osv_results: CVE dicts from OSV fetcher.
            nvd_results: CVE dicts from NVD fetcher.

        Returns:
            Deduplicated list of CVE dicts sorted by CVSS descending.
        """
        # Index by CVE ID
        merged: dict[str, dict[str, Any]] = {}

        # Add OSV results first (they have richer data)
        for cve in osv_results:
            cve_id = cve.get("id", "")
            if cve_id:
                merged[cve_id] = dict(cve)

        # Merge NVD results (fill in gaps)
        for cve in nvd_results:
            cve_id = cve.get("id", "")
            if not cve_id:
                continue
            if cve_id in merged:
                # Merge fields: NVD fills in what OSV might miss
                existing = merged[cve_id]
                if not existing.get("vector_string") and cve.get("vector_string"):
                    existing["vector_string"] = cve["vector_string"]
                if not existing.get("description") and cve.get("description"):
                    existing["description"] = cve["description"]
                # Use higher CVSS if available
                if cve.get("cvss", 0) > existing.get("cvss", 0):
                    existing["cvss"] = cve["cvss"]
            else:
                merged[cve_id] = dict(cve)

        # Sort by CVSS descending
        result = list(merged.values())
        result.sort(key=lambda x: x.get("cvss", 0), reverse=True)
        return result
