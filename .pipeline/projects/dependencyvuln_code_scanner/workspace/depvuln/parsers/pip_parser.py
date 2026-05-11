"""pip dependency file parser (requirements.txt and Pipfile.lock)."""
import json
import os
import re
from typing import Any

from depvuln.parsers.base import DependencyParser


class PipParser(DependencyParser):
    """Parse requirements.txt or Pipfile.lock files."""

    ECOSYSTEM = "pip"

    def parse(self, filepath: str) -> list[dict[str, Any]]:
        """Parse a requirements.txt or Pipfile.lock file."""
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

        # Try Pipfile.lock (JSON) first
        if content.startswith("{"):
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                return []
            for section in ("default", "develop"):
                packages = data.get(section, {})
                for name, info in packages.items():
                    version = ""
                    if isinstance(info, dict):
                        version = info.get("version", "").lstrip("=<>=~! ")
                    elif isinstance(info, str):
                        version = info.lstrip("=<>=~! ")
                    if name and version:
                        deps.append({
                            "name": name,
                            "version": version,
                            "ecosystem": self.ECOSYSTEM,
                        })
            return deps

        # requirements.txt format
        for line in content.splitlines():
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Parse name==version, name>=version, name~=version, etc.
            match = re.match(r"^([A-Za-z0-9_][A-Za-z0-9._-]*)\s*([><=!~]+)\s*([\d][\dA-Za-z._-]*)", line)
            if match:
                name = match.group(1)
                version = match.group(3)
                deps.append({
                    "name": name,
                    "version": version,
                    "ecosystem": self.ECOSYSTEM,
                })

        return deps
