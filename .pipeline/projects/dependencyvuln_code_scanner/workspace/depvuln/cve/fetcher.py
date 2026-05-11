"""CVE fetcher that queries the OSV API with SQLite caching."""
import json
import os
import time
import requests
from typing import Any

from depvuln.cve.cache import CveCache


class CveFetcher:
    """Fetch CVE records from the OSV API, with optional SQLite caching."""

    OSV_API = "https://api.osv.dev/v1/query"

    def __init__(self, cache_enabled: bool = True, cache_dir: str | None = None, ttl: int = 3600):
        if cache_enabled:
            if cache_dir is None:
                cache_dir = os.path.join(os.path.expanduser("~"), ".depvuln", "cache")
            self.cache = CveCache(os.path.join(cache_dir, "osv.db"), ttl=ttl)
        else:
            self.cache = None

    def _cache_key(self, package: str, version: str, ecosystem: str) -> str:
        return f"osv:{ecosystem}:{package}:{version}"

    def fetch(self, package: str, version: str, ecosystem: str) -> list[dict[str, Any]]:
        """Fetch CVEs for a specific package version from OSV API.

        Args:
            package: Package name
            version: Package version
            ecosystem: Package ecosystem (e.g., "pypi", "npm")

        Returns:
            List of CVE dicts with keys: id, severity, description, cvss, vector_string
        """
        cache_key = self._cache_key(package, version, ecosystem)
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        query = {
            "package": {"name": package, "ecosystem": ecosystem},
            "version": version,
        }

        try:
            resp = requests.post(self.OSV_API, json=query, timeout=15)
            resp.raise_for_status()
            body = resp.json()
        except (requests.RequestException, json.JSONDecodeError):
            return []

        results: list[dict[str, Any]] = []
        vulns = body.get("vulns", [])
        for vuln in vulns:
            cve_id = vuln.get("id", "")
            description = vuln.get("details", "")
            
            # Extract CVSS from aliases or severity
            cvss = 0.0
            vector_string = ""
            aliases = vuln.get("aliases", [])
            for alias in aliases:
                if alias.startswith("CVE-"):
                    # Try to get CVSS from the alias data if available
                    pass
            
            # Check for severity field
            severity_list = vuln.get("severity", [])
            if severity_list:
                for sev in severity_list:
                    if sev.get("type") == "CVSS_V3":
                        cvss_data = sev.get("cvssData", {})
                        cvss = cvss_data.get("baseScore", 0.0)
                        vector_string = cvss_data.get("vectorString", "")
                        break
            
            # Extract severity label
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
                "source": "osv",
            })

        if self.cache:
            self.cache.set(cache_key, results)

        return results
