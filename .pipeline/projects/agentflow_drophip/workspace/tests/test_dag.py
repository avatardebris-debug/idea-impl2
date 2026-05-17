"""Tests for the DAG data structure."""

import pytest

from agentflow_drophip.exceptions import CycleDetectedError
from agentflow_drophip.workflow.dag import DAG, Edge, Node


class TestNode:
    """Tests for Node dataclass."""

    def test_node_creation(self):
        """Test creating a Node."""
        node = Node(id="test", label="Test Node")
        assert node.id == "test"
        assert node.label == "Test Node"
        assert node.dependencies == []
        assert node.data == {}
        assert node.status == "pending"

    def test_node_with_dependencies(self):
        """Test creating a Node with dependencies."""
        node = Node(id="test", label="Test", dependencies=["dep1", "dep2"])
        assert node.dependencies == ["dep1", "dep2"]

    def test_node_equality(self):
        """Test Node equality."""
        node1 = Node(id="test", label="Test")
        node2 = Node(id="test", label="Different Label")
        node3 = Node(id="other", label="Test")
        assert node1 == node2
        assert node1 != node3

    def test_node_hash(self):
        """Test Node hashing."""
        node1 = Node(id="test", label="Test")
        node2 = Node(id="test", label="Different")
        assert hash(node1) == hash(node2)


class TestEdge:
    """Tests for Edge dataclass."""

    def test_edge_creation(self):
        """Test creating an Edge."""
        edge = Edge(source="a", target="b")
        assert edge.source == "a"
        assert edge.target == "b"

    def test_edge_equality(self):
        """Test Edge equality."""
        edge1 = Edge(source="a", target="b")
        edge2 = Edge(source="a", target="b")
        edge3 = Edge(source="b", target="a")
        assert edge1 == edge2
        assert edge1 != edge3

    def test_edge_hash(self):
        """Test Edge hashing."""
        edge1 = Edge(source="a", target="b")
        edge2 = Edge(source="a", target="b")
        assert hash(edge1) == hash(edge2)


class TestDAG:
    """Tests for DAG class."""

    def test_dag_creation(self):
        """Test creating an empty DAG."""
        dag = DAG()
        assert len(dag) == 0
        assert dag.nodes == {}
        assert dag.edges == []

    def test_add_node(self):
        """Test adding a node to the DAG."""
        dag = DAG()
        node = Node(id="test", label="Test")
        dag.add_node(node)
        assert len(dag) == 1
        assert "test" in dag.nodes

    def test_add_duplicate_node_raises_error(self):
        """Test that adding a duplicate node raises ValueError."""
        dag = DAG()
        node1 = Node(id="test", label="Test")
        dag.add_node(node1)
        node2 = Node(id="test", label="Test 2")
        with pytest.raises(ValueError, match="already exists"):
            dag.add_node(node2)

    def test_add_edge(self):
        """Test adding an edge to the DAG."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_edge("a", "b")
        assert len(dag.edges) == 1
        assert dag.edges[0].source == "a"
        assert dag.edges[0].target == "b"

    def test_add_edge_updates_dependencies(self):
        """Test that adding an edge updates node dependencies."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_edge("a", "b")
        assert "a" in dag.nodes["b"].dependencies

    def test_add_edge_to_nonexistent_source_raises_error(self):
        """Test that adding an edge with nonexistent source raises ValueError."""
        dag = DAG()
        dag.add_node(Node(id="b", label="B"))
        with pytest.raises(ValueError, match="Source node 'a' not in DAG"):
            dag.add_edge("a", "b")

    def test_add_edge_to_nonexistent_target_raises_error(self):
        """Test that adding an edge with nonexistent target raises ValueError."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        with pytest.raises(ValueError, match="Target node 'b' not in DAG"):
            dag.add_edge("a", "b")

    def test_add_self_loop_raises_error(self):
        """Test that adding a self-loop raises ValueError."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        with pytest.raises(ValueError, match="Self-loop"):
            dag.add_edge("a", "a")

    def test_add_duplicate_edge(self):
        """Test that adding a duplicate edge does nothing."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_edge("a", "b")
        dag.add_edge("a", "b")
        assert len(dag.edges) == 1

    def test_topological_sort_simple(self):
        """Test topological sort on a simple DAG."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_node(Node(id="c", label="C"))
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        order = dag.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_topological_sort_diamond(self):
        """Test topological sort on a diamond-shaped DAG."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_node(Node(id="c", label="C"))
        dag.add_node(Node(id="d", label="D"))
        dag.add_edge("a", "b")
        dag.add_edge("a", "c")
        dag.add_edge("b", "d")
        dag.add_edge("c", "d")
        order = dag.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_topological_sort_cycle_raises_error(self):
        """Test that topological sort raises CycleDetectedError on cycle."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_node(Node(id="c", label="C"))
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        dag.add_edge("c", "a")
        with pytest.raises(CycleDetectedError):
            dag.topological_sort()

    def test_get_ready_nodes(self):
        """Test getting ready nodes."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A", status="completed"))
        dag.add_node(Node(id="b", label="B", dependencies=["a"], status="pending"))
        dag.add_node(Node(id="c", label="C", dependencies=["a"], status="pending"))
        dag.add_edge("a", "b")
        dag.add_edge("a", "c")
        ready = dag.get_ready_nodes()
        assert "b" in ready
        assert "c" in ready

    def test_get_ready_nodes_with_unmet_dependencies(self):
        """Test that nodes with unmet dependencies are not ready."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A", status="pending"))
        dag.add_node(Node(id="b", label="B", dependencies=["a"], status="pending"))
        dag.add_edge("a", "b")
        ready = dag.get_ready_nodes()
        assert "b" not in ready

    def test_get_dependencies(self):
        """Test getting transitive dependencies."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_node(Node(id="c", label="C"))
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        deps = dag.get_dependencies("c")
        assert "b" in deps
        assert "a" in deps

    def test_get_dependents(self):
        """Test getting transitive dependents."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_node(id="c", label="C")
        dag.add_edge("a", "b")
        dag.add_edge("b", "c")
        dependents = dag.get_dependents("a")
        assert "b" in dependents
        assert "c" in dependents

    def test_validate_valid_dag(self):
        """Test validation of a valid DAG."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_edge("a", "b")
        assert dag.validate() is True

    def test_validate_invalid_dag(self):
        """Test validation of an invalid DAG."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_edge("a", "b")
        # Add a dependency to a nonexistent node
        dag.nodes["b"].dependencies.append("nonexistent")
        assert dag.validate() is False

    def test_validate_cycle(self):
        """Test validation of a DAG with a cycle."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        dag.add_edge("a", "b")
        dag.add_edge("b", "a")
        assert dag.validate() is False

    def test_len(self):
        """Test __len__ method."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        assert len(dag) == 2

    def test_repr(self):
        """Test __repr__ method."""
        dag = DAG()
        dag.add_node(Node(id="a", label="A"))
        dag.add_node(Node(id="b", label="B"))
        repr_str = repr(dag)
        assert "nodes=2" in repr_str
        assert "edges=0" in repr_str
