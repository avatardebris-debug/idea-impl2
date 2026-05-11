"""Cargo Cargo.toml parser."""
import os
from typing import Any

from depvuln.parsers.base import DependencyParser

try:
    import tomllib
except ImportError:
    # Python < 3.11 fallback
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


class CargoParser(DependencyParser):
    """Parse Cargo.toml files."""

    ECOSYSTEM = "cargo"

    def parse(self, filepath: str) -> list[dict[str, Any]]:
        """Parse a Cargo.toml file and return dependency dicts."""
        if not os.path.isfile(filepath):
            return []

        if tomllib is None:
            return []

        try:
            with open(filepath, "rb") as fh:
                content = fh.read()
        except (OSError, UnicodeDecodeError):
            return []

        if not content.strip():
            return []

        try:
            data = tomllib.loads(content.decode("utf-8"))
        except Exception:
            return []

        deps: list[dict[str, Any]] = []

        # Parse [dependencies]
        for name, info in data.get("dependencies", {}).items():
            version = self._extract_version(info)
            if name and version:
                deps.append({
                    "name": name,
                    "version": version,
                    "ecosystem": self.ECOSYSTEM,
                })

        # Parse [dev-dependencies]
        for name, info in data.get("dev-dependencies", {}).items():
            version = self._extract_version(info)
            if name and version:
                deps.append({
                    "name": name,
                    "version": version,
                    "ecosystem": self.ECOSYSTEM,
                })

        # Parse [build-dependencies]
        for name, info in data.get("build-dependencies", {}).items():
            version = self._extract_version(info)
            if name and version:
                deps.append({
                    "name": name,
                    "version": version,
                    "ecosystem": self.ECOSYSTEM,
                })

        return deps

    @staticmethod
    def _extract_version(info: Any) -> str:
        """Extract version string from a Cargo dependency spec."""
        if isinstance(info, str):
            return info
        if isinstance(info, dict):
            return info.get("version", "")
        return ""
