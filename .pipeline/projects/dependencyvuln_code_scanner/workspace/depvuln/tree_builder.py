"""Dependency tree builder — constructs a tree of dependencies from parsed data."""
from typing import Any


class DependencyTreeBuilder:
    """Build a dependency tree from parsed dependency data."""

    def build(self, dependencies: list[dict[str, Any]]) -> dict[str, Any]:
        """Build a dependency tree from a list of dependency dicts.

        Args:
            dependencies: List of dependency dicts from parsers.

        Returns:
            A tree dict with root node and children.
        """
        root = {
            "name": "root",
            "version": "",
            "ecosystem": "root",
            "children": [],
        }

        for dep in dependencies:
            node = {
                "name": dep.get("name", ""),
                "version": dep.get("version", ""),
                "ecosystem": dep.get("ecosystem", ""),
                "children": [],
            }
            root["children"].append(node)

        return root

    def to_dict(self, tree: dict[str, Any]) -> dict[str, Any]:
        """Convert the tree to a serializable dict."""
        return {
            "name": tree["name"],
            "version": tree["version"],
            "ecosystem": tree["ecosystem"],
            "children": [self.to_dict(child) for child in tree.get("children", [])],
        }

    def count(self, tree: dict[str, Any]) -> int:
        """Count total nodes in the tree."""
        count = 1  # Count this node
        for child in tree.get("children", []):
            count += self.count(child)
        return count

    def find_by_name(self, tree: dict[str, Any], name: str) -> dict[str, Any] | None:
        """Find a node by name in the tree (depth-first search)."""
        if tree["name"] == name:
            return tree
        for child in tree.get("children", []):
            result = self.find_by_name(child, name)
            if result:
                return result
        return None

    def get_dependencies(self, tree: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract all leaf dependencies from the tree."""
        deps = []
        if not tree.get("children"):
            if tree["name"] != "root":
                deps.append({
                    "name": tree["name"],
                    "version": tree["version"],
                    "ecosystem": tree["ecosystem"],
                })
        else:
            for child in tree["children"]:
                deps.extend(self.get_dependencies(child))
        return deps
