"""Opportunity engine — client matching, proposal generation, and pipeline tracking."""

from opportunity.models import Opportunity, OpportunityPipeline, OpportunityStage
from opportunity.opportunity_engine import OpportunityEngine
from opportunity.pipeline_manager import PipelineManager
from opportunity.matching import OpportunityMatcher

__all__ = [
    "Opportunity",
    "OpportunityPipeline",
    "OpportunityStage",
    "OpportunityEngine",
    "PipelineManager",
    "OpportunityMatcher",
]
