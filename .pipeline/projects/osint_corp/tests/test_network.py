"""Tests for analysis/network module."""

import pytest
from osint_corp.analysis.network import NetworkAnalyzer, NetworkAnalysis
from osint_corp.models.entities import Company


class TestNetworkAnalysis:
    """Tests for NetworkAnalysis."""

    def test_network_analysis_creation(self):
        """Test creating a NetworkAnalysis."""
        analysis = NetworkAnalysis(
            nodes=[{"id": "A", "type": "company"}],
            edges=[{"source": "A", "target": "B"}],
            communities=[["A"]],
        )
        assert len(analysis.nodes) == 1
        assert len(analysis.edges) == 1
        assert len(analysis.communities) == 1

    def test_network_analysis_to_dict(self):
        """Test NetworkAnalysis serialization."""
        analysis = NetworkAnalysis(
            nodes=[{"id": "A", "type": "company"}],
            edges=[{"source": "A", "target": "B"}],
            key_officers=[{"name": "John", "role": "CEO"}],
            insights=["Test insight"],
        )
        d = analysis.to_dict()
        assert d["nodes"] == [{"id": "A", "type": "company"}]
        assert d["key_officers"][0]["name"] == "John"
        assert d["insights"][0] == "Test insight"

    def test_network_analysis_from_dict(self):
        """Test NetworkAnalysis deserialization."""
        d = {
            "nodes": [{"id": "A", "type": "company"}],
            "edges": [{"source": "A", "target": "B"}],
            "communities": [["A"]],
            "key_officers": [{"name": "John", "role": "CEO"}],
            "related_companies": [{"name": "B", "relationship_type": "subsidiary"}],
            "insights": ["Test insight"],
        }
        analysis = NetworkAnalysis.from_dict(d)
        assert len(analysis.nodes) == 1
        assert analysis.key_officers[0]["name"] == "John"


class TestNetworkAnalyzer:
    """Tests for NetworkAnalyzer."""

    def test_analyze_network_empty(self):
        """Test analysis with no relationships."""
        analyzer = NetworkAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")
        analysis = analyzer.analyze_network(company, [])
        assert analysis is not None
        assert len(analysis.nodes) == 1  # Just the company node
        assert len(analysis.edges) == 0

    def test_analyze_network_with_relationships(self):
        """Test analysis with relationships."""
        analyzer = NetworkAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        relationships = [
            {
                "source_name": "Test Corp",
                "target_name": "Subsidiary Inc",
                "relationship_type": "subsidiary",
                "strength": 0.8,
            },
            {
                "source_name": "Test Corp",
                "target_name": "Partner LLC",
                "relationship_type": "partner",
                "strength": 0.5,
            },
        ]

        analysis = analyzer.analyze_network(company, relationships)
        assert analysis is not None
        assert len(analysis.nodes) == 3  # Test Corp + 2 others
        assert len(analysis.edges) == 2

    def test_analyze_network_with_officers(self):
        """Test analysis with officer data."""
        analyzer = NetworkAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        relationships = [
            {
                "source_name": "Test Corp",
                "target_name": "John Doe",
                "relationship_type": "officer",
                "strength": 1.0,
                "metadata": {"role": "CEO"},
            },
        ]

        analysis = analyzer.analyze_network(company, relationships)
        assert analysis is not None
        assert len(analysis.key_officers) == 1
        assert analysis.key_officers[0]["name"] == "John Doe"

    def test_analyze_network_generates_insights(self):
        """Test that insights are generated."""
        analyzer = NetworkAnalyzer()
        company = Company(name="Test Corp", ticker="TEST")

        relationships = [
            {
                "source_name": "Test Corp",
                "target_name": "Subsidiary Inc",
                "relationship_type": "subsidiary",
                "strength": 0.8,
            },
        ]

        analysis = analyzer.analyze_network(company, relationships)
        assert analysis is not None
        assert len(analysis.insights) > 0
        assert "subsidiary" in analysis.insights[0].lower()
