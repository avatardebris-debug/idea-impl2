"""Core data models for the subgoal generator."""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field


@dataclass
class Subgoal:
    """A single decomposed subgoal."""
    title: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    priority: int = 1

    def to_pipeline_entry(self) -> str:
        """Format this subgoal as a YAML pipeline idea entry."""
        entry = {
            "title": self.title,
            "description": self.description,
            "dependencies": self.dependencies,
            "priority": self.priority,
        }
        return yaml.dump(entry, default_flow_style=False)

    @classmethod
    def from_pipeline_entry(cls, yaml_str: str) -> Subgoal:
        """Parse a YAML pipeline entry string into a Subgoal."""
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}") from e
        if not isinstance(data, dict):
            raise ValueError("YAML must be a mapping")
        if "title" not in data:
            raise ValueError("Missing required field: title")
        return cls(
            title=str(data["title"]),
            description=str(data.get("description", "")),
            dependencies=list(data.get("dependencies", [])),
            priority=int(data.get("priority", 1)),
        )


@dataclass
class DependencyGraph:
    """Directed acyclic graph of subgoals."""

    subgoals: dict[str, Subgoal] = field(default_factory=dict)

    def add_subgoal(self, subgoal: Subgoal) -> None:
        """Add a subgoal to the graph."""
        self.subgoals[subgoal.title] = subgoal

    def validate(self) -> bool:
        """Validate that the graph has no circular dependencies."""
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _has_cycle(title: str) -> bool:
            visited.add(title)
            rec_stack.add(title)
            sg = self.subgoals.get(title)
            if sg:
                for dep in sg.dependencies:
                    if dep not in visited:
                        if _has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True
            rec_stack.discard(title)
            return False

        for title in self.subgoals:
            if title not in visited:
                if _has_cycle(title):
                    return False
        return True

    def topological_sort(self) -> list[Subgoal]:
        """Return subgoals in dependency order (dependencies first)."""
        visited: set[str] = set()
        result: list[str] = []

        def _visit(title: str) -> None:
            if title in visited:
                return
            visited.add(title)
            sg = self.subgoals.get(title)
            if sg:
                for dep in sg.dependencies:
                    _visit(dep)
            result.append(title)

        for title in self.subgoals:
            _visit(title)
        return [self.subgoals[t] for t in result]
