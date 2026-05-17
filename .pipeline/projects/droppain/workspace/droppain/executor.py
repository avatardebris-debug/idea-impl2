"""Campaign execution engine for droppain.

Orchestrates the full flow: load products → plan campaign → generate content → publish to channels.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from droppain.config import Config, get_config
from droppain.content_generator import ContentGenerator, GeneratedContent
from droppain.exceptions import PublishingError
from droppain.models import Product
from droppain.planner import CampaignPlan, CampaignPlanner

logger = logging.getLogger(__name__)


@dataclass
class PublishingResult:
    """Result of publishing content to a channel."""

    channel: str
    success: bool
    content: Optional[GeneratedContent] = None
    error: Optional[str] = None
    published_at: Optional[str] = None


@dataclass
class CampaignExecutionResult:
    """Result of executing a full campaign."""

    campaign_plan: CampaignPlan
    publishing_results: List[PublishingResult] = field(default_factory=list)
    total_published: int = 0
    total_failed: int = 0
    status: str = "completed"  # completed, failed, partial


class CampaignExecutor:
    """Executes marketing campaigns end-to-end.

    Orchestrates product loading, campaign planning, content generation,
    and publishing to multiple channels.
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        mock_publishing: bool = False,
    ):
        """Initialize the campaign executor.

        Args:
            config: Configuration object.
            mock_publishing: If True, simulate publishing instead of doing real API calls.
        """
        self.config = config or get_config()
        self.mock_publishing = mock_publishing
        self.planner = CampaignPlanner(config)
        self.content_generator = ContentGenerator()

    def execute(self, plan: CampaignPlan) -> Dict[str, Any]:
        """Execute a campaign plan and return results as a dict.

        Args:
            plan: CampaignPlan to execute.

        Returns:
            Dict with 'status' and 'results' keys.
        """
        logger.info("Starting campaign execution for %s", plan.campaign_name)

        # Generate content for all briefs
        generated_contents = self.content_generator.generate_batch(plan.content_briefs)
        logger.info("Generated %d content pieces", len(generated_contents))

        # Publish to channels
        results = []
        for content in generated_contents:
            result = self._publish_to_channel(content.platform, content)
            results.append(result)

        # Compile results
        total_published = sum(1 for r in results if r.get("status") == "success")
        total_failed = sum(1 for r in results if r.get("status") != "success")

        status = "completed"

        logger.info(
            "Campaign execution complete: %d published, %d failed",
            total_published,
            total_failed,
        )

        return {
            "status": status,
            "results": results,
            "total_published": total_published,
            "total_failed": total_failed,
        }

    def _publish_to_channel(
        self,
        channel: str,
        content: GeneratedContent,
    ) -> Dict[str, Any]:
        """Publish content to a single channel.

        Args:
            channel: Channel platform name.
            content: GeneratedContent to publish.

        Returns:
            Dict with 'status', 'post_id' (on success), or 'error' (on failure).
        """
        if self.mock_publishing:
            logger.info("Mock publishing to %s: %s", channel, content.body[:50] + "..." if len(content.body) > 50 else content.body)
            return {
                "status": "success",
                "post_id": "mock_123",
            }

        # Simulate publishing for known channels
        known_channels = {"facebook", "instagram", "email", "google", "tiktok"}
        if channel in known_channels:
            logger.info("Publishing to %s (simulated)", channel)
            return {
                "status": "success",
                "post_id": f"sim_{channel}_123",
            }
        else:
            error_msg = f"Unknown channel: {channel}"
            logger.warning(error_msg)
            return {
                "status": "error",
                "error": error_msg,
            }

    def execute_campaign(
        self,
        products: List[Product],
        campaign_name: Optional[str] = None,
    ) -> CampaignExecutionResult:
        """Execute a full marketing campaign.

        Args:
            products: List of Product objects to market.
            campaign_name: Optional custom campaign name.

        Returns:
            CampaignExecutionResult with publishing outcomes.
        """
        logger.info("Executing campaign for %d products", len(products))

        # Create plan
        plan = self.planner.create_plan(
            products=products,
            campaign_name=campaign_name,
        )

        # Execute plan
        result_dict = self.execute(plan)

        # Convert to CampaignExecutionResult
        publishing_results = []
        for res in result_dict.get("results", []):
            publishing_results.append(PublishingResult(
                channel=res.get("post_id", "unknown"),
                success=res.get("status") == "success",
                error=res.get("error"),
            ))

        return CampaignExecutionResult(
            campaign_plan=plan,
            publishing_results=publishing_results,
            total_published=result_dict.get("total_published", 0),
            total_failed=result_dict.get("total_failed", 0),
            status=result_dict.get("status", "failed"),
        )

    def execute_campaign_from_store(
        self,
        store_name: str,
        campaign_name: Optional[str] = None,
    ) -> CampaignExecutionResult:
        """Execute a campaign using products from a Shopify store.

        Args:
            store_name: Shopify store name.
            campaign_name: Optional custom campaign name.

        Returns:
            CampaignExecutionResult with publishing outcomes.
        """
        logger.info("Loading products from store: %s", store_name)

        # In a real implementation, this would call Shopify API
        # For now, return empty result
        products: List[Product] = []

        return self.execute_campaign(products, campaign_name)
