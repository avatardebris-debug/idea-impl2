"""Proposal Builder — Assemble a client-ready proposal from SOP + client data."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.service_offering import ServiceOffering
from core.client_profile import ClientProfile
from sop_engine.scope_extractor import ScopeExtractor
from sop_engine.pricing_calculator import PricingCalculator


@dataclass
class Proposal:
    """A generated proposal combining SOP and client data."""
    proposal_id: str
    title: str
    client_name: str
    client_email: str
    service_title: str
    overview: str
    scope: dict[str, Any]
    pricing_summary: dict[str, Any]
    recommended_tier: str = ""
    timeline_days: int = 0
    terms: str = ""
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class ProposalBuilder:
    """
    Assembles a Proposal from a ServiceOffering and ClientProfile.
    Uses ScopeExtractor and PricingCalculator to enrich the proposal.
    """

    def __init__(self):
        self.scope_extractor = ScopeExtractor()
        self.pricing_calculator = PricingCalculator()

    def build(
        self,
        offering: ServiceOffering,
        client: ClientProfile,
        budget: float | None = None,
        custom_terms: str | None = None,
    ) -> Proposal:
        """
        Build a proposal from an SOP and client profile.

        Args:
            offering: The service offering (SOP).
            client: The client profile.
            budget: Optional client budget for tier recommendation.
            custom_terms: Optional custom terms text.

        Returns:
            A Proposal object.
        """
        scope = self.scope_extractor.extract(offering)
        pricing = self.pricing_calculator.calculate(offering)

        # Recommend a tier if budget is provided
        recommended_tier = ""
        if budget is not None:
            tier = self.pricing_calculator.recommend_tier(offering, budget)
            if tier:
                recommended_tier = tier.name

        # Build overview
        overview = (
            f"Dear {client.name},\n\n"
            f"Thank you for your interest in our {offering.title} service. "
            f"Based on your requirements and our expertise in {client.industry or 'your industry'}, "
            f"we have prepared the following proposal.\n\n"
            f"Service Overview: {offering.description}"
        )

        # Build terms
        terms = custom_terms or (
            f"Terms and Conditions:\n"
            f"1. Payment is due upon delivery of each milestone.\n"
            f"2. Revisions are included within the agreed scope.\n"
            f"3. Timeline starts upon contract signing and initial payment.\n"
            f"4. Additional work outside scope will be quoted separately.\n"
            f"5. Confidentiality of all shared information is guaranteed."
        )

        proposal_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"

        return Proposal(
            proposal_id=proposal_id,
            title=f"Proposal: {offering.title} for {client.name}",
            client_name=client.name,
            client_email=client.email,
            service_title=offering.title,
            overview=overview,
            scope=scope,
            pricing_summary=pricing,
            recommended_tier=recommended_tier,
            timeline_days=scope["total_days"],
            terms=terms,
        )
