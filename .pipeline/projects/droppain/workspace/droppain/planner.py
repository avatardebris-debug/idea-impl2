"""Campaign planner core for droppain.

Takes a list of products and generates a structured marketing campaign plan
including channels, schedules, and content briefs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional

from droppain.config import Config, get_config
from droppain.models import Product


@dataclass
class ChannelConfig:
    """Configuration for a single marketing channel."""

    platform: str
    frequency: str
    budget: float
    target_audience: str = ""
    priority: int = 1


@dataclass
class ContentBrief:
    """A content brief for generating marketing copy."""

    title: str
    copy: str
    target_audience: str
    platform: str
    product_ids: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)


@dataclass
class CampaignPlan:
    """A structured marketing campaign plan."""

    campaign_name: str
    channels: List[ChannelConfig]
    content_briefs: List[ContentBrief]
    schedule: List[str]
    total_budget: float
    status: str = "draft"


class CampaignPlanner:
    """Generates marketing campaign plans from product data."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the planner.

        Args:
            config: Optional configuration. If not provided, loads from environment.
        """
        self.config = config or get_config()

    def create_plan(
        self,
        products: List[Product],
        campaign_name: Optional[str] = None,
        total_budget: Optional[float] = None,
        channels: Optional[List[ChannelConfig]] = None,
        budget: Optional[float] = None,
    ) -> CampaignPlan:
        """Create a campaign plan from products.

        Args:
            products: List of products to feature.
            campaign_name: Optional campaign name.
            total_budget: Optional total budget.
            channels: Optional list of channel configurations.
            budget: Alias for total_budget (for compatibility).

        Returns:
            A CampaignPlan instance.
        """
        # Support both 'budget' and 'total_budget' parameter names
        if budget is not None:
            total_budget = budget

        if not campaign_name:
            campaign_name = f"{self.config.campaign_name_prefix} {hashlib.md5(str(products).encode()).hexdigest()[:8]}"

        if channels is None:
            channels = self._generate_default_channels(total_budget)
            if total_budget is None:
                total_budget = 100.0
        else:
            if total_budget is None:
                total_budget = sum(ch.budget for ch in channels)

        if total_budget is None:
            total_budget = 0.0

        content_briefs = []
        if products:
            content_briefs = self._generate_content_briefs(products, channels)

        return CampaignPlan(
            campaign_name=campaign_name,
            channels=channels,
            content_briefs=content_briefs,
            schedule=[],
            total_budget=total_budget,
        )

    def _generate_default_channels(self, total_budget: Optional[float]) -> List[ChannelConfig]:
        """Generate default channel configurations."""
        if total_budget is None:
            total_budget = 100.0

        # Split budget across channels
        facebook_budget = total_budget * 0.4
        instagram_budget = total_budget * 0.3
        tiktok_budget = total_budget * 0.2
        google_budget = total_budget * 0.1

        return [
            ChannelConfig(platform="facebook", frequency="daily", budget=facebook_budget, target_audience="General"),
            ChannelConfig(platform="instagram", frequency="daily", budget=instagram_budget, target_audience="Visual shoppers"),
            ChannelConfig(platform="tiktok", frequency="daily", budget=tiktok_budget, target_audience="Young adults"),
            ChannelConfig(platform="google", frequency="weekly", budget=google_budget, target_audience="Search intent"),
        ]

    def _generate_content_briefs(
        self, products: List[Product], channels: List[ChannelConfig]
    ) -> List[ContentBrief]:
        """Generate content briefs for each product."""
        briefs = []
        for product in products:
            # Use the first channel's platform as the default
            platform = channels[0].platform if channels else "facebook"
            brief = ContentBrief(
                title=product.title,
                copy=f"Check out {product.title}! Great product.",
                target_audience="General",
                platform=platform,
                product_ids=[product.id],
            )
            briefs.append(brief)
        return briefs
