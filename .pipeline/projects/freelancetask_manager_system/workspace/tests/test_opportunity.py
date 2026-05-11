"""Tests for the opportunity engine module."""

import json
import os
import sys
import tempfile
import uuid

import pytest

# Add workspace to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.client_profile import ClientProfile
from core.service_offering import ServiceOffering
from opportunity.models import Opportunity, OpportunityPipeline, OpportunityStage
from opportunity.opportunity_engine import OpportunityEngine
from opportunity.pipeline_manager import PipelineManager
from opportunity.matching import OpportunityMatcher


# ─── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_client():
    """Create a sample client profile."""
    return ClientProfile(
        name="Acme Corp",
        email="contact@acme.com",
        industry="Technology",
        needs=["Build a customer portal", "Improve website performance"],
        pain_points=["Slow load times", "Outdated design"],
        goals=["Increase conversion by 20%", "Reduce bounce rate"],
        budget_range="$5000-$15000",
        timeline="1-2 months",
        metadata={},
    )


@pytest.fixture
def sample_offering():
    """Create a sample service offering."""
    return ServiceOffering(
        title="Website Redesign & Optimization",
        description="Complete website overhaul with performance improvements",
        deliverables=[
            "Custom website design",
            "Performance optimization",
            "Mobile responsive layout",
            "SEO audit and implementation",
        ],
        features=["Analytics integration", "CMS setup", "Security hardening"],
        pricing=[
            ServiceOffering.PricingTier(name="Basic", price=5000, description="Core redesign"),
            ServiceOffering.PricingTier(name="Pro", price=10000, description="Redesign + optimization"),
            ServiceOffering.PricingTier(name="Enterprise", price=15000, description="Full package"),
        ],
        timeline={"total_days": 45, "milestones": 3},
        version=1,
    )


@pytest.fixture
def sample_opportunity(sample_offering, sample_client):
    """Create a sample opportunity."""
    engine = OpportunityEngine()
    return engine.create_opportunity(sample_offering, sample_client)


@pytest.fixture
def sample_pipeline():
    """Create a sample pipeline."""
    return OpportunityPipeline.create_pipeline("Test Pipeline")


# ─── Opportunity Model Tests ────────────────────────────────────────────────────

class TestOpportunityModel:
    """Tests for the Opportunity data model."""

    def test_create_opportunity(self, sample_opportunity):
        """Test opportunity creation."""
        assert sample_opportunity.opportunity_id.startswith("OPP-")
        assert sample_opportunity.client_name == "Acme Corp"
        assert sample_opportunity.service_title == "Website Redesign & Optimization"
        assert sample_opportunity.stage == OpportunityStage.NEW
        assert sample_opportunity.score > 0

    def test_opportunity_stage_transition(self, sample_opportunity):
        """Test stage transitions."""
        sample_opportunity.update_stage(OpportunityStage.MATCHED)
        assert sample_opportunity.stage == OpportunityStage.MATCHED

        sample_opportunity.update_stage(OpportunityStage.PROPOSAL_SENT)
        assert sample_opportunity.stage == OpportunityStage.PROPOSAL_SENT

    def test_opportunity_to_dict(self, sample_opportunity):
        """Test serialization to dict."""
        d = sample_opportunity.to_dict()
        assert d["client_name"] == "Acme Corp"
        assert d["stage"] == "new"  # Enum value, not object
        assert "opportunity_id" in d
        assert "created_at" in d

    def test_opportunity_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "opportunity_id": "OPP-TEST123",
            "client_name": "Test Client",
            "client_email": "test@test.com",
            "service_title": "Test Service",
            "stage": "matched",
            "score": 0.85,
        }
        opp = Opportunity.from_dict(data)
        assert opp.opportunity_id == "OPP-TEST123"
        assert opp.stage == OpportunityStage.MATCHED
        assert opp.score == 0.85

    def test_opportunity_to_json(self, sample_opportunity):
        """Test JSON serialization."""
        json_str = sample_opportunity.to_json()
        parsed = json.loads(json_str)
        assert parsed["client_name"] == "Acme Corp"

    def test_opportunity_from_json(self):
        """Test JSON deserialization."""
        data = {
            "opportunity_id": "OPP-JSON123",
            "client_name": "JSON Client",
            "client_email": "json@test.com",
            "service_title": "JSON Service",
            "stage": "won",
            "score": 0.9,
        }
        opp = Opportunity.from_json(json.dumps(data))
        assert opp.opportunity_id == "OPP-JSON123"
        assert opp.stage == OpportunityStage.WON


class TestOpportunityPipelineModel:
    """Tests for the OpportunityPipeline data model."""

    def test_create_pipeline(self):
        """Test pipeline creation."""
        pipeline = OpportunityPipeline.create_pipeline("My Pipeline")
        assert pipeline.name == "My Pipeline"
        assert pipeline.pipeline_id.startswith("PIPE-")
        assert len(pipeline.opportunities) == 0

    def test_add_opportunity(self, sample_pipeline, sample_opportunity):
        """Test adding opportunities to a pipeline."""
        sample_pipeline.add_opportunity(sample_opportunity)
        assert len(sample_pipeline.opportunities) == 1
        assert sample_pipeline.get_by_id(sample_opportunity.opportunity_id) == sample_opportunity

    def test_get_by_stage(self, sample_pipeline, sample_opportunity):
        """Test filtering by stage."""
        opp1 = sample_opportunity
        opp1.update_stage(OpportunityStage.NEW)
        opp2 = Opportunity(
            opportunity_id="OPP-2",
            client_name="Client 2",
            client_email="c2@test.com",
            service_title="Service 2",
            stage=OpportunityStage.MATCHED,
        )
        sample_pipeline.add_opportunity(opp1)
        sample_pipeline.add_opportunity(opp2)

        new_opps = sample_pipeline.get_by_stage(OpportunityStage.NEW)
        assert len(new_opps) == 1
        assert new_opps[0].opportunity_id == opp1.opportunity_id

    def test_get_won_opportunities(self, sample_pipeline):
        """Test getting won opportunities."""
        won_opp = Opportunity(
            opportunity_id="OPP-WON",
            client_name="Won Client",
            client_email="won@test.com",
            service_title="Won Service",
            stage=OpportunityStage.WON,
        )
        sample_pipeline.add_opportunity(won_opp)
        assert len(sample_pipeline.get_won_opportunities()) == 1

    def test_get_lost_opportunities(self, sample_pipeline):
        """Test getting lost opportunities."""
        lost_opp = Opportunity(
            opportunity_id="OPP-LOST",
            client_name="Lost Client",
            client_email="lost@test.com",
            service_title="Lost Service",
            stage=OpportunityStage.LOST,
        )
        sample_pipeline.add_opportunity(lost_opp)
        assert len(sample_pipeline.get_lost_opportunities()) == 1

    def test_pipeline_serialization(self, sample_pipeline, sample_opportunity):
        """Test pipeline JSON serialization/deserialization."""
        sample_pipeline.add_opportunity(sample_opportunity)
        json_str = sample_pipeline.to_json()
        restored = OpportunityPipeline.from_json(json_str)
        assert restored.name == sample_pipeline.name
        assert len(restored.opportunities) == 1
        assert restored.opportunities[0].client_name == sample_opportunity.client_name


# ─── Opportunity Engine Tests ───────────────────────────────────────────────────

class TestOpportunityEngine:
    """Tests for the OpportunityEngine."""

    def test_create_opportunity(self, sample_offering, sample_client):
        """Test opportunity creation from offering and client."""
        engine = OpportunityEngine()
        opp = engine.create_opportunity(sample_offering, sample_client)
        assert opp.client_name == "Acme Corp"
        assert opp.service_title == "Website Redesign & Optimization"
        assert opp.score > 0

    def test_update_stage(self, sample_opportunity):
        """Test stage updates."""
        engine = OpportunityEngine()
        engine.update_stage(sample_opportunity, OpportunityStage.MATCHED)
        assert sample_opportunity.stage == OpportunityStage.MATCHED

    def test_update_stage_invalid(self, sample_opportunity):
        """Test invalid stage update."""
        engine = OpportunityEngine()
        with pytest.raises(ValueError):
            engine.update_stage(sample_opportunity, "invalid_stage")

    def test_get_opportunity(self, sample_opportunity):
        """Test retrieving an opportunity."""
        engine = OpportunityEngine()
        retrieved = engine.get_opportunity(sample_opportunity.opportunity_id)
        assert retrieved is not None
        assert retrieved.opportunity_id == sample_opportunity.opportunity_id

    def test_get_opportunity_not_found(self):
        """Test retrieving non-existent opportunity."""
        engine = OpportunityEngine()
        assert engine.get_opportunity("OPP-NONEXISTENT") is None

    def test_list_opportunities(self, sample_opportunity):
        """Test listing opportunities."""
        engine = OpportunityEngine()
        engine.create_opportunity(
            ServiceOffering(
                title="Service 2",
                description="Desc 2",
                deliverables=["Deliverable 2"],
                features=[],
                pricing=[ServiceOffering.PricingTier(name="T1", price=1000, description="")],
                version=1,
            ),
            ClientProfile(
                name="Client 2",
                email="c2@test.com",
                industry="Tech",
                needs=["Need 2"],
                pain_points=[],
                goals=[],
                budget_range="$1000-$5000",
                timeline="flexible",
                metadata={},
            ),
        )
        opps = engine.list_opportunities()
        assert len(opps) >= 2

    def test_delete_opportunity(self, sample_opportunity):
        """Test deleting an opportunity."""
        engine = OpportunityEngine()
        engine.delete_opportunity(sample_opportunity.opportunity_id)
        assert engine.get_opportunity(sample_opportunity.opportunity_id) is None

    def test_opportunity_persistence(self, sample_offering, sample_client):
        """Test that opportunities persist across engine instances."""
        engine1 = OpportunityEngine()
        opp1 = engine1.create_opportunity(sample_offering, sample_client)
        opp_id = opp1.opportunity_id

        engine2 = OpportunityEngine()
        opp2 = engine2.get_opportunity(opp_id)
        assert opp2 is not None
        assert opp2.client_name == opp1.client_name


# ─── Pipeline Manager Tests ─────────────────────────────────────────────────────

class TestPipelineManager:
    """Tests for the PipelineManager."""

    def test_create_pipeline(self):
        """Test pipeline creation."""
        manager = PipelineManager()
        pipeline = manager.create_pipeline("Test Pipeline")
        assert pipeline.name == "Test Pipeline"
        assert pipeline.pipeline_id.startswith("PIPE-")

    def test_list_pipelines(self):
        """Test listing pipelines."""
        manager = PipelineManager()
        manager.create_pipeline("Pipeline 1")
        manager.create_pipeline("Pipeline 2")
        pipelines = manager.list_pipelines()
        assert len(pipelines) >= 2

    def test_add_opportunity_to_pipeline(self, sample_opportunity):
        """Test adding opportunity to pipeline."""
        manager = PipelineManager()
        pipeline = manager.create_pipeline("Test Pipeline")
        manager.add_opportunity(pipeline.pipeline_id, sample_opportunity)
        
        # Verify it was added
        pipelines = manager.list_pipelines()
        for p in pipelines:
            if p.pipeline_id == pipeline.pipeline_id:
                assert len(p.opportunities) == 1
                break

    def test_get_pipeline_stats(self, sample_opportunity):
        """Test pipeline statistics."""
        manager = PipelineManager()
        pipeline = manager.create_pipeline("Stats Pipeline")
        manager.add_opportunity(pipeline.pipeline_id, sample_opportunity)
        
        stats = manager.get_pipeline_stats(pipeline.pipeline_id)
        assert stats["total_opportunities"] >= 1
        assert "avg_score" in stats
        assert "by_stage" in stats

    def test_pipeline_persistence(self):
        """Test pipeline persistence across instances."""
        manager1 = PipelineManager()
        p1 = manager1.create_pipeline("Persistent Pipeline")
        pid = p1.pipeline_id

        manager2 = PipelineManager()
        p2 = manager2.get_pipeline(pid)
        assert p2 is not None
        assert p2.name == "Persistent Pipeline"


# ─── Matching Engine Tests ──────────────────────────────────────────────────────

class TestOpportunityMatcher:
    """Tests for the OpportunityMatcher."""

    def test_keyword_overlap_score(self, sample_offering, sample_client):
        """Test keyword overlap scoring."""
        matcher = OpportunityMatcher()
        score = matcher._score_keyword_overlap(sample_offering, sample_client)
        assert 0 <= score <= 1.0

    def test_industry_alignment_score(self, sample_offering, sample_client):
        """Test industry alignment scoring."""
        matcher = OpportunityMatcher()
        score = matcher._score_industry_alignment(sample_offering, sample_client)
        assert 0 <= score <= 1.0

    def test_budget_compatibility_score(self, sample_offering, sample_client):
        """Test budget compatibility scoring."""
        matcher = OpportunityMatcher()
        score = matcher._score_budget_compatibility(sample_offering, sample_client)
        assert 0 <= score <= 1.0

    def test_urgency_match_score(self, sample_offering, sample_client):
        """Test urgency match scoring."""
        matcher = OpportunityMatcher()
        score = matcher._score_urgency_match(sample_offering, sample_client)
        assert 0 <= score <= 1.0

    def test_goal_alignment_score(self, sample_offering, sample_client):
        """Test goal alignment scoring."""
        matcher = OpportunityMatcher()
        score = matcher._score_goal_alignment(sample_offering, sample_client)
        assert 0 <= score <= 1.0

    def test_find_matched_keywords(self, sample_offering, sample_client):
        """Test finding matched keywords."""
        matcher = OpportunityMatcher()
        keywords = matcher._find_matched_keywords(sample_offering, sample_client)
        assert isinstance(keywords, list)
        # Should have some matches given the sample data
        assert len(keywords) > 0

    def test_generate_recommendations(self, sample_offering, sample_client):
        """Test recommendation generation."""
        matcher = OpportunityMatcher()
        breakdown = {
            "keyword_overlap": 0.5,
            "industry_alignment": 0.5,
            "budget_compatibility": 0.5,
            "urgency_match": 0.5,
            "goal_alignment": 0.5,
        }
        recs = matcher._generate_recommendations(breakdown, sample_offering, sample_client)
        assert isinstance(recs, list)

    def test_match_method(self, sample_offering, sample_client):
        """Test the main match method."""
        matcher = OpportunityMatcher()
        result = matcher.match(sample_offering, sample_client)
        assert "score" in result
        assert "breakdown" in result
        assert "matched_keywords" in result
        assert "recommendations" in result
        assert 0 <= result["score"] <= 1

    def test_rank_matches(self, sample_offering):
        """Test ranking multiple clients."""
        matcher = OpportunityMatcher()
        clients = [
            ClientProfile(
                name=f"Client {i}",
                email=f"client{i}@test.com",
                industry="Technology",
                needs=["Build website"],
                pain_points=["Slow performance"],
                goals=["Improve speed"],
                budget_range="$5000-$15000",
                timeline="1-2 months",
                metadata={},
            )
            for i in range(3)
        ]
        ranked = matcher.rank_matches(sample_offering, clients)
        assert len(ranked) == 3
        # Should be sorted by score descending
        for i in range(len(ranked) - 1):
            assert ranked[i]["score"] >= ranked[i + 1]["score"]

    def test_budget_mismatch_handling(self):
        """Test handling of budget mismatches."""
        offering = ServiceOffering(
            title="Premium Service",
            description="High-end service",
            deliverables=["Premium deliverable"],
            features=["Premium feature"],
            pricing=[ServiceOffering.PricingTier(name="Premium", price=50000, description="")],
            version=1,
        )
        client = ClientProfile(
            name="Budget Client",
            email="budget@test.com",
            industry="Technology",
            needs=["Build website"],
            pain_points=[],
            goals=[],
            budget_range="$1000-$3000",
            timeline="flexible",
            metadata={},
        )
        matcher = OpportunityMatcher()
        result = matcher.match(offering, client)
        # Should still return a score, but lower due to budget mismatch
        assert result["score"] < 1.0

    def test_unknown_industry_handling(self):
        """Test handling of unknown industries."""
        offering = ServiceOffering(
            title="Generic Service",
            description="Generic",
            deliverables=["Deliverable"],
            features=[],
            pricing=[ServiceOffering.PricingTier(name="T1", price=1000, description="")],
            version=1,
        )
        client = ClientProfile(
            name="Unknown Industry Client",
            email="unknown@test.com",
            industry="NonExistentIndustry",
            needs=["Need"],
            pain_points=[],
            goals=[],
            budget_range="$1000-$5000",
            timeline="flexible",
            metadata={},
        )
        matcher = OpportunityMatcher()
        result = matcher.match(offering, client)
        # Should handle gracefully
        assert "score" in result


# ─── Integration Tests ──────────────────────────────────────────────────────────

class TestIntegration:
    """Integration tests for the opportunity system."""

    def test_full_workflow(self, sample_offering, sample_client):
        """Test the full opportunity workflow."""
        # Create opportunity
        engine = OpportunityEngine()
        opp = engine.create_opportunity(sample_offering, sample_client)
        
        # Update stage
        engine.update_stage(opp, OpportunityStage.MATCHED)
        
        # Add to pipeline
        pipeline_mgr = PipelineManager()
        pipeline = pipeline_mgr.create_pipeline("Test Workflow")
        pipeline_mgr.add_opportunity(pipeline.pipeline_id, opp)
        
        # Get stats
        stats = pipeline_mgr.get_pipeline_stats(pipeline.pipeline_id)
        assert stats["total_opportunities"] >= 1
        
        # Verify persistence
        engine2 = OpportunityEngine()
        opp2 = engine2.get_opportunity(opp.opportunity_id)
        assert opp2.stage == OpportunityStage.MATCHED

    def test_multiple_opportunities_in_pipeline(self, sample_offering):
        """Test multiple opportunities in a single pipeline."""
        engine = OpportunityEngine()
        pipeline_mgr = PipelineManager()
        pipeline = pipeline_mgr.create_pipeline("Multi Opp Pipeline")
        
        for i in range(3):
            client = ClientProfile(
                name=f"Client {i}",
                email=f"client{i}@test.com",
                industry="Technology",
                needs=["Build website"],
                pain_points=[],
                goals=[],
                budget_range="$5000-$15000",
                timeline="flexible",
                metadata={},
            )
            opp = engine.create_opportunity(sample_offering, client)
            pipeline_mgr.add_opportunity(pipeline.pipeline_id, opp)
        
        stats = pipeline_mgr.get_pipeline_stats(pipeline.pipeline_id)
        assert stats["total_opportunities"] == 3

    def test_opportunity_lifecycle(self, sample_offering, sample_client):
        """Test complete opportunity lifecycle."""
        engine = OpportunityEngine()
        
        # Create
        opp = engine.create_opportunity(sample_offering, sample_client)
        assert opp.stage == OpportunityStage.NEW
        
        # Progress through stages
        engine.update_stage(opp, OpportunityStage.MATCHED)
        engine.update_stage(opp, OpportunityStage.PROPOSAL_SENT)
        engine.update_stage(opp, OpportunityStage.WON)
        
        assert opp.stage == OpportunityStage.WON
        
        # Verify in pipeline
        pipeline_mgr = PipelineManager()
        pipeline = pipeline_mgr.create_pipeline("Lifecycle Test")
        pipeline_mgr.add_opportunity(pipeline.pipeline_id, opp)
        
        won_opps = pipeline.get_won_opportunities()
        assert len(won_opps) == 1


# ─── Edge Case Tests ────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_client_needs(self):
        """Test with client having no needs."""
        client = ClientProfile(
            name="Empty Needs Client",
            email="empty@test.com",
            industry="Technology",
            needs=[],
            pain_points=[],
            goals=[],
            budget_range="$1000-$5000",
            timeline="flexible",
            metadata={},
        )
        offering = ServiceOffering(
            title="Service",
            description="Desc",
            deliverables=["Deliverable"],
            features=[],
            pricing=[ServiceOffering.PricingTier(name="T1", price=1000, description="")],
            version=1,
        )
        engine = OpportunityEngine()
        opp = engine.create_opportunity(offering, client)
        assert opp is not None

    def test_very_high_budget(self):
        """Test with very high budget."""
        client = ClientProfile(
            name="High Budget Client",
            email="high@test.com",
            industry="Technology",
            needs=["Build enterprise system"],
            pain_points=[],
            goals=[],
            budget_range="$100000-$200000",
            timeline="flexible",
            metadata={},
        )
        offering = ServiceOffering(
            title="Enterprise Service",
            description="Enterprise",
            deliverables=["Enterprise deliverable"],
            features=[],
            pricing=[ServiceOffering.PricingTier(name="Enterprise", price=150000, description="")],
            version=1,
        )
        engine = OpportunityEngine()
        opp = engine.create_opportunity(offering, client)
        assert opp is not None
        assert opp.score > 0

    def test_very_low_budget(self):
        """Test with very low budget."""
        client = ClientProfile(
            name="Low Budget Client",
            email="low@test.com",
            industry="Technology",
            needs=["Build website"],
            pain_points=[],
            goals=[],
            budget_range="$100-$500",
            timeline="flexible",
            metadata={},
        )
        offering = ServiceOffering(
            title="Premium Service",
            description="Premium",
            deliverables=["Premium deliverable"],
            features=[],
            pricing=[ServiceOffering.PricingTier(name="Premium", price=10000, description="")],
            version=1,
        )
        engine = OpportunityEngine()
        opp = engine.create_opportunity(offering, client)
        assert opp is not None
        # Score should be lower due to budget mismatch
        assert opp.score < 0.5

    def test_concurrent_pipeline_creation(self):
        """Test concurrent pipeline creation doesn't cause conflicts."""
        manager = PipelineManager()
        pipelines = []
        for i in range(10):
            p = manager.create_pipeline(f"Concurrent Pipeline {i}")
            pipelines.append(p)
        
        # All should have unique IDs
        ids = [p.pipeline_id for p in pipelines]
        assert len(ids) == len(set(ids))
