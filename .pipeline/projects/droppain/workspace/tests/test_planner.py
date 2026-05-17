"""Tests for droppain.planner module."""

import pytest

from droppain.planner import CampaignPlan, CampaignPlanner, ChannelConfig, ContentBrief
from droppain.models import Product


class TestChannelConfig:
    """Tests for ChannelConfig."""

    def test_channel_config_creation(self):
        """Test channel config creation."""
        config = ChannelConfig(platform="facebook", frequency="daily", budget=50.0)
        assert config.platform == "facebook"
        assert config.frequency == "daily"
        assert config.budget == 50.0
        assert config.target_audience == ""
        assert config.priority == 1

    def test_channel_config_with_all_params(self):
        """Test channel config with all params."""
        config = ChannelConfig(
            platform="instagram",
            frequency="weekly",
            budget=100.0,
            target_audience="Fashion enthusiasts",
            priority=2,
        )
        assert config.platform == "instagram"
        assert config.frequency == "weekly"
        assert config.budget == 100.0
        assert config.target_audience == "Fashion enthusiasts"
        assert config.priority == 2


class TestContentBrief:
    """Tests for ContentBrief."""

    def test_content_brief_creation(self):
        """Test basic content brief creation."""
        brief = ContentBrief(
            title="Test Brief",
            copy="Test copy",
            target_audience="General audience",
            platform="facebook",
        )
        assert brief.title == "Test Brief"
        assert brief.copy == "Test copy"
        assert brief.target_audience == "General audience"
        assert brief.platform == "facebook"
        assert brief.product_ids == []
        assert brief.hashtags == []


class TestCampaignPlan:
    """Tests for CampaignPlan."""

    def test_campaign_plan_creation(self):
        """Test basic campaign plan creation."""
        plan = CampaignPlan(
            campaign_name="Test Campaign",
            channels=[ChannelConfig(platform="facebook", frequency="daily", budget=50.0)],
            content_briefs=[],
            schedule=[],
            total_budget=100.0,
        )
        assert plan.campaign_name == "Test Campaign"
        assert len(plan.channels) == 1
        assert plan.total_budget == 100.0
        assert plan.status == "draft"

    def test_campaign_plan_status(self):
        """Test campaign plan status."""
        plan = CampaignPlan(
            campaign_name="Test",
            channels=[],
            content_briefs=[],
            schedule=[],
            total_budget=0.0,
        )
        assert plan.status == "draft"


class TestCampaignPlanner:
    """Tests for CampaignPlanner."""

    def test_planner_creation(self):
        """Test planner creation."""
        planner = CampaignPlanner()
        assert planner is not None

    def test_create_plan(self):
        """Test creating a campaign plan."""
        planner = CampaignPlanner()
        products = [Product(id="1", title="Test", price=10.0)]
        plan = planner.create_plan(products, campaign_name="Test Campaign")
        assert plan.campaign_name == "Test Campaign"
        assert len(plan.channels) > 0
        assert len(plan.content_briefs) > 0
        assert plan.total_budget == 0.0  # no budget set means 0

    def test_create_plan_no_products(self):
        """Test creating a plan with no products."""
        planner = CampaignPlanner()
        plan = planner.create_plan([], campaign_name="Test")
        assert plan.campaign_name == "Test"
        assert len(plan.channels) > 0
        assert len(plan.content_briefs) == 0

    def test_create_plan_with_custom_budget(self):
        """Test creating a plan with custom budget."""
        planner = CampaignPlanner()
        products = [Product(id="1", title="Test", price=10.0)]
        plan = planner.create_plan(products, campaign_name="Test", total_budget=500.0)
        assert plan.total_budget == 500.0

    def test_create_plan_with_custom_channels(self):
        """Test creating a plan with custom channels."""
        planner = CampaignPlanner()
        products = [Product(id="1", title="Test", price=10.0)]
        channels = [ChannelConfig(platform="tiktok", frequency="daily", budget=100.0)]
        plan = planner.create_plan(products, campaign_name="Test", channels=channels)
        assert plan.total_budget == 100.0
        assert len(plan.channels) == 1
        assert plan.channels[0].platform == "tiktok"
