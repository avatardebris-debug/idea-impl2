"""Opportunity Engine — creates and manages opportunities from SOPs and client profiles."""

from __future__ import annotations

import uuid
from typing import Any

from core.client_profile import ClientProfile
from core.service_offering import ServiceOffering
from opportunity.models import Opportunity, OpportunityStage


class OpportunityEngine:
    """
    Creates opportunities by matching ServiceOfferings with ClientProfiles.
    
    An opportunity is created when a client's needs align with a service offering's
    deliverables. The engine calculates a match score based on keyword overlap,
    industry alignment, and budget compatibility.
    """

    # Class-level store so opportunities persist across instances
    _store: dict[str, Opportunity] = {}

    def __init__(self):
        self._opportunities = OpportunityEngine._store

    def create_opportunity(
        self,
        offering: ServiceOffering,
        client: ClientProfile,
        stage: OpportunityStage = OpportunityStage.NEW,
        notes: str = "",
    ) -> Opportunity:
        """Create a new opportunity from an offering and client."""
        # Calculate match score
        score = self._calculate_match_score(offering, client)

        opportunity_id = f"OPP-{uuid.uuid4().hex[:8].upper()}"

        opp = Opportunity(
            opportunity_id=opportunity_id,
            client_name=client.name,
            client_email=client.email,
            service_title=offering.title,
            stage=stage,
            score=score,
            notes=notes,
            metadata={
                "sop_version": offering.version,
                "client_industry": client.industry,
                "client_budget_range": client.budget_range,
            },
        )
        self._opportunities[opportunity_id] = opp
        return opp

    def get_opportunity(self, opportunity_id: str) -> Opportunity | None:
        """Retrieve an opportunity by ID."""
        return self._opportunities.get(opportunity_id)

    def list_opportunities(self) -> list[Opportunity]:
        """List all tracked opportunities."""
        return list(self._opportunities.values())

    def delete_opportunity(self, opportunity_id: str) -> None:
        """Delete an opportunity by ID."""
        self._opportunities.pop(opportunity_id, None)

    def update_stage(self, opportunity: Opportunity, stage: OpportunityStage) -> None:
        """Update the stage of an opportunity."""
        if not isinstance(stage, OpportunityStage):
            raise ValueError(f"Invalid stage: {stage}")
        opportunity.update_stage(stage)

    def create_opportunities_from_clients(
        self,
        offering: ServiceOffering,
        clients: list[ClientProfile],
        min_score: float = 0.0,
    ) -> list[Opportunity]:
        """Create opportunities for all clients that meet the minimum score threshold."""
        opportunities = []
        for client in clients:
            score = self._calculate_match_score(offering, client)
            if score >= min_score:
                opp = self.create_opportunity(
                    offering=offering,
                    client=client,
                    notes=f"Auto-generated with match score {score:.2f}",
                )
                opp.score = score
                opportunities.append(opp)
        return opportunities

    def _calculate_match_score(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """
        Calculate a match score between an offering and a client.
        
        Scoring components:
        - Keyword overlap between client needs/pain_points and offering deliverables: 50%
        - Industry alignment bonus: 20%
        - Budget compatibility: 30%
        
        Returns a score between 0.0 and 1.0.
        """
        score = 0.0

        # 1. Keyword overlap (50% weight)
        keyword_score = self._calculate_keyword_score(offering, client)
        score += keyword_score * 0.5

        # 2. Industry alignment (20% weight)
        industry_score = self._calculate_industry_score(offering, client)
        score += industry_score * 0.2

        # 3. Budget compatibility (30% weight)
        budget_score = self._calculate_budget_score(offering, client)
        score += budget_score * 0.3

        return min(score, 1.0)

    def _calculate_keyword_score(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Calculate keyword overlap score between client needs and offering deliverables."""
        # Collect all keywords from client
        client_keywords = set()
        for text in client.needs + client.pain_points + client.goals:
            client_keywords.update(text.lower().split())

        # Collect all keywords from offering deliverables
        offering_keywords = set()
        for deliverable in offering.deliverables:
            offering_keywords.update(deliverable.lower().split())

        if not client_keywords or not offering_keywords:
            return 0.0

        # Calculate Jaccard similarity
        intersection = client_keywords & offering_keywords
        union = client_keywords | offering_keywords

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _calculate_industry_score(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Calculate industry alignment score."""
        # Define industry affinities for common service types
        industry_affinities = {
            "Technology": {"SaaS", "E-commerce", "Digital Agency"},
            "E-commerce": {"Retail", "Manufacturing", "Technology"},
            "Healthcare": {"Wellness", "Fitness", "Technology"},
            "Education": {"Publishing", "Media", "Technology"},
            "Real Estate": {"Construction", "Architecture", "Technology"},
            "Finance": {"Banking", "Insurance", "Technology"},
            "Food & Beverage": {"Retail", "Hospitality", "E-commerce"},
            "SaaS": {"Technology", "Enterprise", "Consulting"},
            "Digital Agency": {"Marketing", "Media", "Technology"},
            "Consulting": {"Enterprise", "Finance", "Technology"},
        }

        # Check if client industry has affinity with offering's implied industry
        # Use the offering title to infer industry
        offering_industry = self._infer_industry_from_title(offering.title)

        if offering_industry in industry_affinities:
            compatible_industries = industry_affinities[offering_industry]
            if client.industry in compatible_industries:
                return 1.0
            # Check reverse
            for opp_industry, affinities in industry_affinities.items():
                if offering_industry in affinities and client.industry == opp_industry:
                    return 0.8
        return 0.3  # Neutral score

    def _infer_industry_from_title(self, title: str) -> str:
        """Infer the target industry from the service offering title."""
        title_lower = title.lower()
        if "ecommerce" in title_lower or "shop" in title_lower or "store" in title_lower:
            return "E-commerce"
        elif "saas" in title_lower or "software" in title_lower:
            return "SaaS"
        elif "health" in title_lower or "medical" in title_lower:
            return "Healthcare"
        elif "education" in title_lower or "learning" in title_lower:
            return "Education"
        elif "real estate" in title_lower or "property" in title_lower:
            return "Real Estate"
        elif "finance" in title_lower or "bank" in title_lower or "fintech" in title_lower:
            return "Finance"
        elif "food" in title_lower or "restaurant" in title_lower or "catering" in title_lower:
            return "Food & Beverage"
        elif "marketing" in title_lower or "seo" in title_lower or "agency" in title_lower:
            return "Digital Agency"
        elif "consulting" in title_lower or "advisory" in title_lower:
            return "Consulting"
        return "Technology"

    def _calculate_budget_score(self, offering: ServiceOffering, client: ClientProfile) -> float:
        """Calculate budget compatibility score."""
        # Get the offering's price range
        prices = [t.price for t in offering.pricing]
        if not prices:
            return 0.5

        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)

        # Parse client budget range
        client_budget = self._parse_budget_range(client.budget_range)
        if client_budget is None:
            return 0.5  # Neutral if we can't parse

        client_min, client_max = client_budget

        # Calculate overlap between offering prices and client budget
        overlap_start = max(min_price, client_min)
        overlap_end = min(max_price, client_max)

        if overlap_start <= overlap_end:
            # There's overlap
            overlap_range = overlap_end - overlap_start
            offering_range = max_price - min_price
            if offering_range == 0:
                return 1.0
            return min(overlap_range / offering_range + 0.5, 1.0)
        else:
            # No overlap - calculate how far apart they are
            if max_price < client_min:
                gap = client_min - max_price
            else:
                gap = min_price - client_max

            # Normalize gap (assume $10k gap is max)
            gap_score = max(0, 1.0 - gap / 10000)
            return gap_score * 0.5  # Max 0.5 if no overlap

    def _parse_budget_range(self, budget_str: str) -> tuple[float, float] | None:
        """Parse a budget range string like '$5000-$15000' into (min, max)."""
        import re
        match = re.search(r'\$?(\d+)[\s-]*[\$]?(\d+)', budget_str)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        # Try with dollar signs
        match = re.search(r'\$(\d+)[\s-]*\$?(\d+)', budget_str)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        return None
