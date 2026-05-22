"""droppain — Dropship marketing campaign planner and execution engine."""

__version__ = "0.1.0"

from droppain.config import Config, get_config
from droppain.exceptions import (
    DroppainError,
    APIError,
    ConfigurationError,
    ValidationError,
    PublishingError,
)
from droppain.models import Product, Variant
from droppain.planner import CampaignPlanner, CampaignPlan, ChannelConfig, ContentBrief
from droppain.content_generator import ContentGenerator, GeneratedContent
from droppain.executor import CampaignExecutor, CampaignExecutionResult, PublishingResult

__all__ = [
    "Config",
    "get_config",
    "DroppainError",
    "APIError",
    "ConfigurationError",
    "ValidationError",
    "PublishingError",
    "Product",
    "Variant",
    "CampaignPlanner",
    "CampaignPlan",
    "ChannelConfig",
    "ContentBrief",
    "ContentGenerator",
    "GeneratedContent",
    "CampaignExecutor",
    "CampaignExecutionResult",
    "PublishingResult",
]
