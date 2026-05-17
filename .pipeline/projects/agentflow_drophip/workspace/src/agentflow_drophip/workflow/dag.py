"""DAG data structure with Node, Edge, topological sort, and cycle detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from agentflow_drophip.exceptions import CycleDetectedError


@dataclass
class Node:
    """A node in the DAG representing a workflow task."""

    id: str
    label: str
    dependencies: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.id == other.id
        return False


@dataclass
class Edge:
    """An edge in the DAG representing a dependency relationship."""

    source: str
    target: str

    def __hash__(self):
        return hash((self.source, self.target))

    def __eq__(self, other):
        if isinstance(other, Edge):
            return self.source == other.source and self.target == other.target
        return False


class DAG:
    """Directed Acyclic Graph for workflow task dependencies.

    Supports:
    - Node and edge management
    - Topological sort for execution ordering
    - Cycle detection
    - Dependency resolution
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self._adjacency: Dict[str, List[str]] = {}  # node_id -> list of dependent node_ids
        self._reverse_adjacency: Dict[str, List[str]] = {}  # node_id -> list of dependency node_ids

    def add_node(self, node: Node) -> None:
        """Add a node to the DAG."""
        if node.id in self.nodes:
            raise ValueError(f"Node '{node.id}' already exists in DAG")
        self.nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []
        if node.id not in self._reverse_adjacency:
            self._reverse_adjacency[node.id] = []

    def add_edge(self, source_id: str, target_id: str) -> None:
        """Add a directed edge from source to target (source must complete before target)."""
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' not in DAG")
        if target_id not in self.nodes:
            raise ValueError(f"Target node '{target_id}' not in DAG")
        if source_id == target_id:
            raise ValueError(f"Self-loop detected: '{source_id}'")

        edge = Edge(source=source_id, target=target_id)
        if edge in self.edges:
            return  # Edge already exists

        self.edges.append(edge)
        self._adjacency.setdefault(source_id, []).append(target_id)
        self._reverse_adjacency.setdefault(target_id, []).append(source_id)

        # Update node dependencies
        if target_id in self.nodes:
            if source_id not in self.nodes[target_id].dependencies:
                self.nodes[target_id].dependencies.append(source_id)

    def topological_sort(self) -> List[str]:
        """Return nodes in topological order (dependencies first).

        Raises:
            CycleDetectedError: If the DAG contains a cycle.
        """
        self._detect_cycles()

        in_degree: Dict[str, int] = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges:
            in_degree[edge.target] = in_degree.get(edge.target, 0) + 1

        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort for deterministic ordering
            queue.sort()
            node_id = queue.pop(0)
            result.append(node_id)

            for neighbor in self._adjacency.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            raise CycleDetectedError(
                "Cycle detected during topological sort",
                cycle_nodes=[n for n in self.nodes if n not in result],
            )

        return result

    def get_ready_nodes(self) -> List[str]:
        """Get nodes whose dependencies are all completed."""
        ready = []
        for node_id, node in self.nodes.items():
            if node.status != "pending":
                continue
            deps_completed = all(
                self.nodes[dep_id].status == "completed"
                for dep_id in node.dependencies
                if dep_id in self.nodes
            )
            if deps_completed:
                ready.append(node_id)
        return ready

    def _detect_cycles(self) -> bool:
        """Detect if the DAG contains a cycle using DFS.

        Returns:
            True if no cycle detected.

        Raises:
            CycleDetectedError: If a cycle is found.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {node_id: WHITE for node_id in self.nodes}
        path: List[str] = []

        def dfs(node_id: str) -> bool:
            color[node_id] = GRAY
            path.append(node_id)

            for neighbor in self._adjacency.get(node_id, []):
                if color[neighbor] == GRAY:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    raise CycleDetectedError(
                        f"Cycle detected: {' -> '.join(cycle)}",
                        cycle_nodes=list(set(cycle)),
                    )
                if color[neighbor] == WHITE:
                    if not dfs(neighbor):
                        return False

            path.pop()
            color[node_id] = BLACK
            return True

        for node_id in self.nodes:
            if color[node_id] == WHITE:
                if not dfs(node_id):
                    return False
        return True

    def get_dependencies(self, node_id: str) -> List[str]:
        """Get all dependencies (transitive) for a node."""
        if node_id not in self.nodes:
            return []

        visited = set()
        stack = [node_id]
        deps = []

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            for dep_id in self._reverse_adjacency.get(current, []):
                if dep_id not in visited:
                    stack.append(dep_id)
                    deps.append(dep_id)

        return deps

    def get_dependents(self, node_id: str) -> List[str]:
        """Get all dependents (transitive) of a node."""
        if node_id not in self.nodes:
            return []

        visited = set()
        stack = [node_id]
        dependents = []

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            for dep_id in self._adjacency.get(current, []):
                if dep_id not in visited:
                    stack.append(dep_id)
                    dependents.append(dep_id)

        return dependents

    def validate(self) -> bool:
        """Validate the DAG structure.

        Returns:
            True if the DAG is valid (no cycles, all dependencies exist).
        """
        try:
            self._detect_cycles()
            # Check all dependencies exist
            for node_id, node in self.nodes.items():
                for dep_id in node.dependencies:
                    if dep_id not in self.nodes:
                        return False
            return True
        except CycleDetectedError:
            return False

    def __len__(self) -> int:
        return len(self.nodes)

    def __repr__(self) -> str:
        return f"DAG(nodes={len(self.nodes)}, edges={len(self.edges)})"
