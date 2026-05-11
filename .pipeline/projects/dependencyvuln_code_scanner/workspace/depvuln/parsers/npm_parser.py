"""npm / yarn lockfile parser."""
import json
import os
from typing import Any

from depvuln.parsers.base import DependencyParser


class NpmParser(DependencyParser):
    """Parse package-lock.json or yarn.lock files."""

    ECOSYSTEM = "npm"

    def parse(self, filepath: str) -> list[dict[str, Any]]:
        """Parse a package-lock.json file and return dependency dicts."""
        if not os.path.isfile(filepath):
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read().strip()
        except (OSError, UnicodeDecodeError):
            return []

        if not content:
            return []

        # Try package-lock.json format first
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return []

        deps: list[dict[str, Any]] = []

        # package-lock.json v2/v3 structure
        packages = data.get("packages", {})
        if packages:
            for pkg_path, info in packages.items():
                if not pkg_path:
                    continue  # root entry
                name = info.get("name", "")
                version = info.get("version", "")
                if name and version:
                    deps.append({
                        "name": name,
                        "version": version,
                        "ecosystem": self.ECOSYSTEM,
                    })
        else:
            # v1 structure: dependencies -> name -> version
            dependencies = data.get("dependencies", {})
            if dependencies:
                for name, info in dependencies.items():
                    version = ""
                    if isinstance(info, dict):
                        version = info.get("version", "")
                    elif isinstance(info, str):
                        version = info
                    if name and version:
                        deps.append({
                            "name": name,
                            "version": version,
                            "ecosystem": self.ECOSYSTEM,
                        })

        return deps
