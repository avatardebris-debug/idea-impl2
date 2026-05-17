"""End-to-end integration test for droppain.

Exercises the full pipeline: create mock products -> plan campaign ->
generate content -> execute campaign -> verify results.
"""

from __future__ import annotations

import json
import pathlib
import tempfile
from typing import Any

import pytest

from droppain.models import Product, Variant
from droppain.planner import CampaignPlanner
from droppain.content_generator import ContentGenerator
from droppain.executor import CampaignExecutor, CampaignExecutionResult


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_products() -> list[Product]:
    """Return a list of mock products for testing."""
    return [
        Product(
            id="prod_1",
            title="Wireless Earbuds",
            description="High-quality wireless earbuds with noise cancellation",
            price=49.99,
            variants=[
                Variant(id="var_1", title="Black", price=49.99),
                Variant(id="var_2", title="White", price=49.99),
            ],
            tags=["electronics", "audio"],
        ),
        Product(
            id="prod_2",
            title="Phone Case",
            description="Durable protective phone case",
            price=19.99,
            variants=[
                Variant(id="var_3", title="Clear", price=19.99),
            ],
            tags=["accessories", "phone"],
        ),
    ]


@pytest.fixture
def products_json(sample_products: list[Product]) -> pathlib.Path:
    """Write sample products to a temporary JSON file."""
    data = [p.to_dict() for p in sample_products]
    tmp = pathlib.Path(tempfile.mkdtemp()) / "products.json"
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return tmp


# ── Tests ────────────────────────────────────────────────────────────────────


class TestCampaignPlanner:
    """Tests for the campaign planning step."""

    def test_create_plan(self, sample_products: list[Product]) -> None:
        planner = CampaignPlanner()
        plan = planner.create_plan(
            products=sample_products,
            campaign_name="Test Campaign",
        )

        assert plan.campaign_name == "Test Campaign"
        assert len(plan.content_briefs) == 2  # one brief per product
        assert plan.total_budget == 0.0  # no budget set

    def test_create_plan_with_budget(self, sample_products: list[Product]) -> None:
        planner = CampaignPlanner()
        plan = planner.create_plan(
            products=sample_products,
            campaign_name="Budget Campaign",
            total_budget=500.0,
        )

        assert plan.total_budget == 500.0


class TestContentGenerator:
    """Tests for the content generation step."""

    def test_generate_batch(self, sample_products: list[Product]) -> None:
        planner = CampaignPlanner()
        plan = planner.create_plan(
            products=sample_products,
            campaign_name="Test Campaign",
        )

        generator = ContentGenerator()
        contents = generator.generate_batch(plan.content_briefs)

        assert len(contents) == 2
        for content in contents:
            assert content.body is not None
            assert len(content.body) > 0
            assert content.platform in ("facebook", "instagram", "email", "google", "tiktok")


class TestCampaignExecutor:
    """Tests for the campaign execution step."""

    def test_execute_with_mock(self, sample_products: list[Product]) -> None:
        """Execute a campaign with mock publishing (default)."""
        planner = CampaignPlanner()
        plan = planner.create_plan(
            products=sample_products,
            campaign_name="Mock Campaign",
        )

        executor = CampaignExecutor(mock_publishing=True)
        result = executor.execute(plan)

        assert result["status"] == "completed"
        assert result["total_published"] == 2
        assert result["total_failed"] == 0
        assert len(result["results"]) == 2
        for res in result["results"]:
            assert res["status"] == "success"
            assert res["post_id"] == "mock_123"

    def test_execute_with_simulated_channels(self, sample_products: list[Product]) -> None:
        """Execute a campaign with simulated channel publishing."""
        planner = CampaignPlanner()
        plan = planner.create_plan(
            products=sample_products,
            campaign_name="Sim Campaign",
        )

        executor = CampaignExecutor(mock_publishing=False)
        result = executor.execute(plan)

        assert result["status"] == "completed"
        assert result["total_published"] == 2
        assert result["total_failed"] == 0

    def test_execute_campaign(self, sample_products: list[Product]) -> None:
        """Test the high-level execute_campaign method."""
        executor = CampaignExecutor(mock_publishing=True)
        result = executor.execute_campaign(
            products=sample_products,
            campaign_name="High-Level Campaign",
        )

        assert isinstance(result, CampaignExecutionResult)
        assert result.campaign_plan.campaign_name == "High-Level Campaign"
        assert result.total_published == 2
        assert result.total_failed == 0
        assert result.status == "completed"

    def test_execute_campaign_from_store(self) -> None:
        """Test execute_campaign_from_store (returns empty products)."""
        executor = CampaignExecutor(mock_publishing=True)
        result = executor.execute_campaign_from_store(
            store_name="test-store",
            campaign_name="Store Campaign",
        )

        assert isinstance(result, CampaignExecutionResult)
        assert result.total_published == 0
        assert result.total_failed == 0


class TestEndToEnd:
    """Full pipeline integration test."""

    def test_full_pipeline(self, sample_products: list[Product]) -> None:
        """Exercise the entire pipeline end-to-end."""
        # Step 1: Plan
        planner = CampaignPlanner()
        plan = planner.create_plan(
            products=sample_products,
            campaign_name="E2E Campaign",
            budget=1000.0,
        )
        assert plan.campaign_name == "E2E Campaign"
        assert plan.total_budget == 1000.0
        assert len(plan.content_briefs) == 2

        # Step 2: Generate content
        generator = ContentGenerator()
        contents = generator.generate_batch(plan.content_briefs)
        assert len(contents) == 2
        for content in contents:
            assert content.body is not None
            assert len(content.body) > 0

        # Step 3: Execute
        executor = CampaignExecutor(mock_publishing=True)
        result = executor.execute(plan)

        assert result["status"] == "completed"
        assert result["total_published"] == 2
        assert result["total_failed"] == 0

        # Step 4: Verify results
        for res in result["results"]:
            assert res["status"] == "success"
            assert res["post_id"] == "mock_123"

    def test_full_pipeline_via_execute_campaign(self, sample_products: list[Product]) -> None:
        """Exercise the full pipeline via the high-level execute_campaign method."""
        executor = CampaignExecutor(mock_publishing=True)
        result = executor.execute_campaign(
            products=sample_products,
            campaign_name="High-Level E2E",
        )

        assert result.status == "completed"
        assert result.total_published == 2
        assert result.total_failed == 0
        assert len(result.publishing_results) == 2
        for pr in result.publishing_results:
            assert pr.success is True
            assert pr.error is None

    def test_products_json_roundtrip(self, products_json: pathlib.Path) -> None:
        """Test that products can be serialized to JSON and deserialized back."""
        # Read the JSON file
        data = json.loads(products_json.read_text(encoding="utf-8"))
        assert len(data) == 2

        # Deserialize to Product objects
        products = [Product.from_dict(p) for p in data]
        assert len(products) == 2
        assert products[0].title == "Wireless Earbuds"
        assert products[1].title == "Phone Case"

        # Serialize back
        roundtrip = [p.to_dict() for p in products]
        assert json.dumps(roundtrip, sort_keys=True) == json.dumps(data, sort_keys=True)
