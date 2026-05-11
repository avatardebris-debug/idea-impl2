"""NVD API CVE fetcher with SQLite caching."""
import json
import os
import time
import requests
from typing import Any

from depvuln.cve.cache import CveCache


class NvdFetcher:
    """Fetch CVE records from the NVD API, with optional SQLite caching."""

    NVD_API = "https://services.nvd.org.az/1.0/json/cve/{cve_id}"
    NVD_SEARCH_API = "https://services.nvd.org.az/2.0/cves?keywordSearch={keyword}"

    def __init__(self, cache_enabled: bool = True, cache_dir: str | None = None, ttl: int = 3600):
        if cache_enabled:
            if cache_dir is None:
                cache_dir = os.path.join(os.path.expanduser("~"), ".depvuln", "cache")
            self.cache = CveCache(os.path.join(cache_dir, "nvd.db"), ttl=ttl)
        else:
            self.cache = None

    def _cache_key(self, cve_id: str) -> str:
        return f"nvd:{cve_id}"

    def fetch(self, cve_id: str) -> list[dict[str, Any]]:
        """Fetch a specific CVE from NVD API.

        Args:
            cve_id: CVE identifier (e.g., "CVE-2023-1234")

        Returns:
            List of CVE dicts with keys: id, severity, description, cvss, vector_string
        """
        if self.cache:
            cached = self.cache.get(self._cache_key(cve_id))
            if cached is not None:
                return cached

        url = self.NVD_API.format(cve_id=cve_id)
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            body = resp.json()
        except (requests.RequestException, json.JSONDecodeError):
            return []

        results: list[dict[str, Any]] = []
        cve_data = body.get("vulnerabilities", [])
        for vuln in cve_data:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")
            description = cve.get("descriptions", [{}])[0].get("value", "")
            
            # Extract CVSS
            cvss = 0.0
            vector_string = ""
            metrics = cve.get("metrics", {})
            for metric_key in metrics:
                if "cvssV3" in metric_key:
                    cvss_data = metrics[metric_key][0].get("cvssData", {})
                    cvss = cvss_data.get("baseScore", 0.0)
                    vector_string = cvss_data.get("vectorString", "")
                    break
            
            # Extract severity
            severity = "UNKNOWN"
            if cvss >= 9.0:
                severity = "CRITICAL"
            elif cvss >= 7.0:
                severity = "HIGH"
            elif cvss >= 4.0:
                severity = "MEDIUM"
            elif cvss > 0:
                severity = "LOW"

            results.append({
                "id": cve_id,
                "severity": severity,
                "description": description,
                "cvss": cvss,
                "vector_string": vector_string,
                "source": "nvd",
            })

        if self.cache:
            self.cache.set(self._cache_key(cve_id), results)

        return results

    def fetch_by_package(self, package_name: str) -> list[dict[str, Any]]:
        """Search NVD for CVEs related to a package.

        Args:
            package_name: Package name to search for

        Returns:
            List of CVE dicts
        """
        url = self.NVD_SEARCH_API.format(keyword=package_name)
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            body = resp.json()
        except (requests.RequestException, json.JSONDecodeError):
            return []

        results: list[dict[str, Any]] = []
        cve_data = body.get("vulnerabilities", [])
        for vuln in cve_data:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")
            description = cve.get("descriptions", [{}])[0].get("value", "")
            
            # Extract CVSS
            cvss = 0.0
            vector_string = ""
            metrics = cve.get("metrics", {})
            for metric_key in metrics:
                if "cvssV3" in metric_key:
                    cvss_data = metrics[metric_key][0].get("cvssData", {})
                    cvss = cvss_data.get("baseScore", 0.0)
                    vector_string = cvss_data.get("vectorString", "")
                    break
            
            # Extract severity
            severity = "UNKNOWN"
            if cvss >= 9.0:
                severity = "CRITICAL"
            elif cvss >= 7.0:
                severity = "HIGH"
            elif cvss >= 4.0:
                severity = "MEDIUM"
            elif cvss > 0:
                severity = "LOW"

            results.append({
                "id": cve_id,
                "severity": severity,
                "description": description,
                "cvss": cvss,
                "vector_string": vector_string,
                "source": "nvd",
            })

        return results
