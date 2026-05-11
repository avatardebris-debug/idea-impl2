"""CocoaPods Podfile parser."""
import os
import re
from typing import Any

from depvuln.parsers.base import DependencyParser


class PodfileParser(DependencyParser):
    """Parse CocoaPods Podfile files."""

    ECOSYSTEM = "podfile"

    def parse(self, filepath: str) -> list[dict[str, Any]]:
        """Parse a Podfile and return dependency dicts."""
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

        # Match pod declarations: pod 'Name', 'version_constraint'
        # Patterns:
        #   pod 'AFNetworking'
        #   pod 'AFNetworking', '~> 4.0'
        #   pod 'AFNetworking', '>= 4.0'
        #   pod 'AFNetworking', '= 4.0.0'
        #   pod 'AFNetworking', '< 5.0'
        #   pod 'Name', :path => '../path'
        #   pod 'Name', :git => 'https://...'
        pattern = re.compile(
            r"^\s*pod\s+['\"]([^'\"]+)['\"]"  # pod 'name'
            r"(?:\s*,\s*['\"]([^'\"]+)['\"])?",  # optional version
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            name = match.group(1)
            version = match.group(2) or ""
            if name:
                deps.append({
                    "name": name,
                    "version": version,
                    "ecosystem": self.ECOSYSTEM,
                })

        return deps
