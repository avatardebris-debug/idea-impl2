"""Maven pom.xml parser."""
import os
import xml.etree.ElementTree as ET
from typing import Any

from depvuln.parsers.base import DependencyParser


class MavenParser(DependencyParser):
    """Parse Maven pom.xml files."""

    ECOSYSTEM = "maven"

    # Maven pom.xml namespace
    NS = {"m": "http://maven.apache.org/POM/4.0.0"}

    def parse(self, filepath: str) -> list[dict[str, Any]]:
        """Parse a pom.xml file and return dependency dicts."""
        if not os.path.isfile(filepath):
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                content = fh.read().strip()
        except (OSError, UnicodeDecodeError):
            return []

        if not content:
            return []

        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return []

        deps: list[dict[str, Any]] = []

        # Try with namespace first
        for dep in root.findall(".//m:dependency", self.NS):
            group_id = dep.findtext("m:groupId", "", self.NS)
            artifact_id = dep.findtext("m:artifactId", "", self.NS)
            version = dep.findtext("m:version", "", self.NS)
            if group_id and artifact_id and version:
                deps.append({
                    "name": f"{group_id}:{artifact_id}",
                    "version": version,
                    "ecosystem": self.ECOSYSTEM,
                })

        # Also try without namespace (some pom.xml files omit it)
        if not deps:
            for dep in root.findall(".//dependency"):
                group_id = dep.findtext("groupId", "")
                artifact_id = dep.findtext("artifactId", "")
                version = dep.findtext("version", "")
                if group_id and artifact_id and version:
                    deps.append({
                        "name": f"{group_id}:{artifact_id}",
                        "version": version,
                        "ecosystem": self.ECOSYSTEM,
                    })

        return deps
