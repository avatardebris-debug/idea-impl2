"""Network analysis module — builds and analyzes corporate relationship networks."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from osint_corp.correlation import Relationship
from osint_corp.models.entities import Company, Filing

logger = logging.getLogger(__name__)


@dataclass
class NetworkNode:
    """A node in the corporate network."""
    id: str
    name: str
    node_type: str  # "company", "person", "address", "officer", "director"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "metadata": self.metadata,
        }


@dataclass
class NetworkEdge:
    """An edge in the corporate network."""
    source: str
    target: str
    relationship_type: str
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class NetworkAnalysis:
    """Results of network analysis."""
    company_name: str
    ticker: Optional[str]
    nodes: list[NetworkNode] = field(default_factory=list)
    edges: list[NetworkEdge] = field(default_factory=list)
    communities: list[list[str]] = field(default_factory=list)
    centrality_scores: dict[str, float] = field(default_factory=dict)
    key_officers: list[dict] = field(default_factory=list)
    related_companies: list[dict] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "ticker": self.ticker,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "communities": self.communities,
            "centrality_scores": self.centrality_scores,
            "key_officers": self.key_officers,
            "related_companies": self.related_companies,
            "insights": self.insights,
        }


class NetworkAnalyzer:
    """Analyzes corporate networks from relationships and filings."""

    def __init__(self):
        self._cache: dict[str, NetworkAnalysis] = {}

    def analyze(
        self,
        company: Company,
        relationships: Optional[list[Relationship]] = None,
        filings: Optional[list[Filing]] = None,
    ) -> NetworkAnalysis:
        """Analyze the corporate network for a company.

        Args:
            company: The target Company.
            relationships: List of relationships (if None, will be inferred from filings).
            filings: List of filings to extract relationships from.

        Returns:
            NetworkAnalysis with nodes, edges, and insights.
        """
        cache_key = f"{company.cik}_{company.ticker}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        analysis = self._build_network(company, relationships, filings)
        self._cache[cache_key] = analysis
        return analysis

    def _build_network(
        self,
        company: Company,
        relationships: Optional[list[Relationship]],
        filings: Optional[list[Filing]],
    ) -> NetworkAnalysis:
        """Build the network from company data, relationships, and filings."""
        analysis = NetworkAnalysis(
            company_name=company.name,
            ticker=company.ticker,
        )

        # Add the target company as the root node
        analysis.nodes.append(NetworkNode(
            id=company.cik or company.name,
            name=company.name,
            node_type="company",
            metadata={"ticker": company.ticker, "cik": company.cik},
        ))

        # Collect relationships
        all_relationships = relationships or []

        # Extract relationships from filings if available
        if filings:
            filing_relationships = self._extract_relationships_from_filings(filings)
            all_relationships.extend(filing_relationships)

        # Build nodes and edges from relationships
        node_map: dict[str, NetworkNode] = {}
        edge_set: set[tuple[str, str, str]] = set()

        for rel in all_relationships:
            # Add source node
            if rel.source_id not in node_map:
                source_name = rel.source_name or "Unknown"
                node_map[rel.source_id] = NetworkNode(
                    id=rel.source_id,
                    name=source_name,
                    node_type=rel.source_type,
                    metadata={"relationship": rel.relationship_type},
                )
                analysis.nodes.append(node_map[rel.source_id])

            # Add target node
            if rel.target_id not in node_map:
                target_name = rel.target_name or "Unknown"
                node_map[rel.target_id] = NetworkNode(
                    id=rel.target_id,
                    name=target_name,
                    node_type=rel.target_type,
                    metadata={"relationship": rel.relationship_type},
                )
                analysis.nodes.append(node_map[rel.target_id])

            # Add edge
            edge_key = (rel.source_id, rel.target_id, rel.relationship_type)
            if edge_key not in edge_set:
                analysis.edges.append(NetworkEdge(
                    source=rel.source_id,
                    target=rel.target_id,
                    relationship_type=rel.relationship_type,
                    confidence=rel.confidence,
                    metadata={"source": rel.source},
                ))
                edge_set.add(edge_key)

        # Extract key officers from filings
        if filings:
            analysis.key_officers = self._extract_officers(filings)

        # Detect communities (simple connected components)
        analysis.communities = self._detect_communities(analysis.edges)

        # Calculate centrality scores
        analysis.centrality_scores = self._calculate_centrality(analysis.edges)

        # Find related companies
        analysis.related_companies = self._find_related_companies(analysis.edges, node_map)

        # Generate insights
        analysis.insights = self._generate_insights(analysis)

        return analysis

    def _extract_relationships_from_filings(
        self,
        filings: list[Filing],
    ) -> list[Relationship]:
        """Extract relationships from filing metadata."""
        relationships = []

        for filing in filings:
            # Extract officers/directors from filing metadata
            if filing.metadata and "raw_filing" in filing.metadata:
                raw = filing.metadata["raw_filing"]
                if isinstance(raw, dict):
                    # Look for officer/director information
                    officers = raw.get("officers", [])
                    if isinstance(officers, list):
                        for officer in officers:
                            if isinstance(officer, dict):
                                name = officer.get("name", "Unknown")
                                role = officer.get("role", "officer")
                                relationships.append(Relationship(
                                    source_id=filing.cik or filing.company_name,
                                    source_name=filing.company_name,
                                    source_type="company",
                                    target_id=name,
                                    target_name=name,
                                    target_type="person",
                                    relationship_type="officer",
                                    confidence=0.8,
                                    source=filing.accession_number,
                                ))

                    directors = raw.get("directors", [])
                    if isinstance(directors, list):
                        for director in directors:
                            if isinstance(director, dict):
                                name = director.get("name", "Unknown")
                                relationships.append(Relationship(
                                    source_id=filing.cik or filing.company_name,
                                    source_name=filing.company_name,
                                    source_type="company",
                                    target_id=name,
                                    target_name=name,
                                    target_type="person",
                                    relationship_type="director",
                                    confidence=0.8,
                                    source=filing.accession_number,
                                ))

        return relationships

    def _extract_officers(self, filings: list[Filing]) -> list[dict]:
        """Extract key officers from filings."""
        officers = []
        seen = set()

        for filing in filings:
            if filing.metadata and "raw_filing" in filing.metadata:
                raw = filing.metadata["raw_filing"]
                if isinstance(raw, dict):
                    for key in ["officers", "directors", "executives"]:
                        items = raw.get(key, [])
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    name = item.get("name", "")
                                    role = item.get("role", item.get("title", ""))
                                    if name and name not in seen:
                                        officers.append({
                                            "name": name,
                                            "role": role,
                                            "filing_date": filing.filing_date,
                                        })
                                        seen.add(name)

        return officers

    def _detect_communities(self, edges: list[NetworkEdge]) -> list[list[str]]:
        """Detect communities using simple connected components."""
        if not edges:
            return []

        # Build adjacency list
        adj: dict[str, set[str]] = defaultdict(set)
        all_nodes: set[str] = set()

        for edge in edges:
            adj[edge.source].add(edge.target)
            adj[edge.target].add(edge.source)
            all_nodes.add(edge.source)
            all_nodes.add(edge.target)

        # Find connected components using BFS
        visited: set[str] = set()
        communities = []

        for node in all_nodes:
            if node not in visited:
                community = []
                queue = [node]
                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        community.append(current)
                        for neighbor in adj[current]:
                            if neighbor not in visited:
                                queue.append(neighbor)
                communities.append(community)

        return communities

    def _calculate_centrality(self, edges: list[NetworkEdge]) -> dict[str, float]:
        """Calculate degree centrality for each node."""
        degree: dict[str, int] = defaultdict(int)

        for edge in edges:
            degree[edge.source] += 1
            degree[edge.target] += 1

        # Normalize by total possible connections
        total_nodes = max(len(degree), 1)
        centrality = {node: count / (total_nodes - 1) if total_nodes > 1 else 0
                      for node, count in degree.items()}

        return centrality

    def _find_related_companies(self, edges: list[NetworkEdge], node_map: dict[str, NetworkNode]) -> list[dict]:
        """Find companies related to the target company."""
        related = []
        seen = set()

        for edge in edges:
            # Find the node that is not the target company
            for node_id in [edge.source, edge.target]:
                if node_id not in node_map:
                    continue
                node = node_map[node_id]
                if node.node_type == "company" and node_id not in seen:
                    seen.add(node_id)
                    related.append({
                        "id": node_id,
                        "name": node.name,
                        "relationship_type": edge.relationship_type,
                        "confidence": edge.confidence,
                    })

        return related

    def _generate_insights(self, analysis: NetworkAnalysis) -> list[str]:
        """Generate insights from the network analysis."""
        insights = []

        # Number of connections
        num_edges = len(analysis.edges)
        if num_edges > 10:
            insights.append(f"Highly connected entity with {num_edges} relationships")
        elif num_edges < 3:
            insights.append("Limited network connections — may be a standalone entity")

        # Officer density
        officer_count = sum(1 for e in analysis.edges if e.relationship_type in ("officer", "director"))
        if officer_count > 5:
            insights.append(f"Multiple officers/directors ({officer_count}) — complex governance structure")

        # Cross-entity relationships
        company_nodes = [n for n in analysis.nodes if n.node_type == "company"]
        if len(company_nodes) > 3:
            insights.append(f"Network includes {len(company_nodes)} companies — potential corporate group")

        # High centrality nodes
        high_centrality = {k: v for k, v in analysis.centrality_scores.items() if v > 0.5}
        if high_centrality:
            insights.append(f"Key hub nodes identified: {', '.join(high_centrality.keys())[:50]}")

        return insights

    def clear_cache(self):
        """Clear the analysis cache."""
        self._cache.clear()
