"""Tests for proposal engine."""

import pytest
from core.service_offering import ServiceOffering
from core.client_profile import ClientProfile
from proposal_engine.proposal_builder import ProposalBuilder
from proposal_engine.template_renderer import TemplateRenderer


class TestProposalBuilder:
    def setup_method(self):
        self.offering = ServiceOffering.from_dict({
            "title": "Website Development",
            "description": "Custom website",
            "deliverables": ["Homepage", "About Page"],
            "timeline": {
                "total_days": 14,
                "milestones": [
                    {
                        "title": "Design",
                        "description": "Design approval",
                        "deadline_days": 5,
                        "deliverables": ["Mockups"]
                    }
                ]
            },
            "pricing": [
                {"name": "Basic", "price": 1000, "description": "Basic tier"},
                {"name": "Pro", "price": 3000, "description": "Pro tier"}
            ],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })

        self.client = ClientProfile.from_dict({
            "name": "Test Client",
            "email": "test@example.com",
            "industry": "Tech",
            "company_size": "10-50",
            "budget_range": "$2000-$4000",
            "needs": ["New website"],
            "pain_points": ["Old site"],
            "goals": ["Better UX"],
            "decision_maker": "Jane Doe",
            "timeline_preference": "2 weeks",
            "notes": "Test client"
        })

    def test_build_proposal(self):
        builder = ProposalBuilder()
        proposal = builder.build(self.offering, self.client)

        assert proposal.title == "Proposal: Website Development for Test Client"
        assert proposal.client_name == "Test Client"
        assert proposal.client_email == "test@example.com"
        assert proposal.service_title == "Website Development"
        assert proposal.timeline_days == 14
        assert proposal.proposal_id.startswith("PROP-")
        assert "test@example.com" in proposal.overview

    def test_build_with_budget(self):
        builder = ProposalBuilder()
        proposal = builder.build(self.offering, self.client, budget=3000)
        assert proposal.recommended_tier == "Pro"

    def test_build_with_custom_terms(self):
        builder = ProposalBuilder()
        custom = "Custom terms here."
        proposal = builder.build(self.offering, self.client, custom_terms=custom)
        assert proposal.terms == custom


class TestTemplateRenderer:
    def setup_method(self):
        self.offering = ServiceOffering.from_dict({
            "title": "Test Service",
            "description": "Test",
            "deliverables": ["Del 1"],
            "timeline": {"total_days": 10, "milestones": []},
            "pricing": [{"name": "Basic", "price": 100, "description": "Basic"}],
            "requirements": [],
            "assumptions": [],
            "risks": [],
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })

        self.client = ClientProfile.from_dict({
            "name": "Test Client",
            "email": "test@example.com",
            "industry": "Tech",
            "company_size": "10-50",
            "budget_range": "$1000-$5000",
            "needs": [],
            "pain_points": [],
            "goals": [],
            "decision_maker": "John",
            "timeline_preference": "2 weeks",
            "notes": ""
        })

        builder = ProposalBuilder()
        self.proposal = builder.build(self.offering, self.client)

    def test_render_markdown(self):
        renderer = TemplateRenderer()
        output = renderer.render_markdown(self.proposal)

        assert "# Proposal: Test Service for Test Client" in output
        assert "## Overview" in output
        assert "## Scope of Work" in output
        assert "## Pricing" in output
        assert "## Terms and Conditions" in output
        assert "$100.00" in output

    def test_render_html(self):
        renderer = TemplateRenderer()
        output = renderer.render_html(self.proposal)

        assert "<!DOCTYPE html>" in output
        assert "<h1>Proposal: Test Service for Test Client</h1>" in output
        assert "<h2>Overview</h2>" in output
        assert "<h2>Pricing</h2>" in output
        assert "$100.00" in output

    def test_render_default_format(self):
        renderer = TemplateRenderer()
        output = renderer.render(self.proposal)
        assert "# Proposal:" in output  # Markdown default

    def test_render_html_format(self):
        renderer = TemplateRenderer()
        output = renderer.render(self.proposal, fmt="html")
        assert "<!DOCTYPE html>" in output
