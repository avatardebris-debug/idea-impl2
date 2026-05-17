"""Tests for droppain.executor module."""

import pytest
from unittest.mock import MagicMock, patch

from droppain.executor import CampaignExecutor
from droppain.planner import CampaignPlan, ChannelConfig, ContentBrief
from droppain.content_generator import GeneratedContent


class TestCampaignExecutor:
    """Tests for CampaignExecutor."""

    def test_executor_creation(self):
        """Test executor creation."""
        executor = CampaignExecutor()
        assert executor is not None

    def test_execute_campaign(self):
        """Test executing a campaign."""
        executor = CampaignExecutor()
        plan = CampaignPlan(
            campaign_name="Test Campaign",
            channels=[ChannelConfig(platform="facebook", frequency="daily", budget=50.0)],
            content_briefs=[ContentBrief(title="Test", copy="Body", target_audience="General", platform="facebook")],
            schedule=[],
            total_budget=50.0,
        )
        result = executor.execute(plan)
        assert result["status"] == "completed"
        assert "results" in result

    @patch("droppain.executor.CampaignExecutor._publish_to_channel")
    def test_execute_campaign_mocked_publish(self, mock_publish):
        """Test campaign execution with mocked publish."""
        mock_publish.return_value = {"status": "success", "post_id": "123"}
        executor = CampaignExecutor()
        plan = CampaignPlan(
            campaign_name="Test",
            channels=[ChannelConfig(platform="facebook", frequency="daily", budget=50.0)],
            content_briefs=[ContentBrief(title="Test", copy="Body", target_audience="General", platform="facebook")],
            schedule=[],
            total_budget=50.0,
        )
        result = executor.execute(plan)
        assert result["status"] == "completed"
        mock_publish.assert_called()

    def test_execute_empty_plan(self):
        """Test executing an empty plan."""
        executor = CampaignExecutor()
        plan = CampaignPlan(
            campaign_name="Empty",
            channels=[],
            content_briefs=[],
            schedule=[],
            total_budget=0.0,
        )
        result = executor.execute(plan)
        assert result["status"] == "completed"
        assert result["results"] == []

    @patch("droppain.executor.CampaignExecutor._publish_to_channel")
    def test_execute_with_failed_channel(self, mock_publish):
        """Test campaign with one failed channel."""
        mock_publish.side_effect = [
            {"status": "success", "post_id": "1"},
            {"status": "error", "error": "Network error"},
        ]
        executor = CampaignExecutor()
        plan = CampaignPlan(
            campaign_name="Test",
            channels=[
                ChannelConfig(platform="facebook", frequency="daily", budget=50.0),
                ChannelConfig(platform="instagram", frequency="daily", budget=50.0),
            ],
            content_briefs=[
                ContentBrief(title="Test", copy="Body", target_audience="General", platform="facebook"),
                ContentBrief(title="Test", copy="Body", target_audience="General", platform="instagram"),
            ],
            schedule=[],
            total_budget=100.0,
        )
        result = executor.execute(plan)
        assert result["status"] == "completed"
        assert len(result["results"]) == 2

    def test_publish_to_channel(self):
        """Test publishing to a channel."""
        executor = CampaignExecutor()
        content = GeneratedContent(platform="facebook", body="Test", hashtags=["#test"])
        result = executor._publish_to_channel("facebook", content)
        assert result["status"] == "success"

    def test_publish_to_channel_unknown(self):
        """Test publishing to unknown channel."""
        executor = CampaignExecutor()
        content = GeneratedContent(platform="unknown", body="Test", hashtags=[])
        result = executor._publish_to_channel("unknown", content)
        assert result["status"] == "error"
        assert "Unknown channel" in result["error"]
