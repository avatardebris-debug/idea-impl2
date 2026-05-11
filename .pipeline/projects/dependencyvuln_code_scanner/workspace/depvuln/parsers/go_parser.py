"""Go module go.mod parser."""
import os
import re
from typing import Any

from depvuln.parsers.base import DependencyParser


class GoParser(DependencyParser):
    """Parse go.mod files."""

    ECOSYSTEM = "go"

    def parse(self, filepath: str) -> list[dict[str, Any]]:
        """Parse a go.mod file and return dependency dicts."""
        if not os.path.isfile(filepath):
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read().strip()
        except (OSError, UnicodeDecodeError):
            return []

        if not content:
            return []

        deps: list[dict[str, Any]] = []
        in_require = False

        for line in content.splitlines():
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith("//"):
                continue

            # Start of require block
            if stripped.startswith("require ("):
                in_require = True
                continue

            # End of require block
            if in_require and stripped == ")":
                in_require = False
                continue

            # Single-line require
            if stripped.startswith("require "):
                parts = stripped[len("require "):].split()
                if len(parts) >= 2:
                    module_path = parts[0]
                    version = parts[1]
                    deps.append({
                        "name": module_path,
                        "version": version,
                        "ecosystem": self.ECOSYSTEM,
                    })
                continue

            # Inside require block
            if in_require:
                parts = stripped.split()
                if len(parts) >= 2:
                    module_path = parts[0]
                    version = parts[1]
                    deps.append({
                        "name": module_path,
                        "version": version,
                        "ecosystem": self.ECOSYSTEM,
                    })

        return deps
