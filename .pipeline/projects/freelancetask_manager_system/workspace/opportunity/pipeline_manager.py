"""Pipeline Manager — manages opportunity pipelines with persistence."""

from __future__ import annotations

import json
import os
from typing import Any

from opportunity.models import Opportunity, OpportunityPipeline, OpportunityStage


class PipelineManager:
    """
    Manages opportunity pipelines with file-backed persistence.
    
    Each pipeline is stored as a JSON file in a configurable directory.
    Supports CRUD operations and stage transitions.
    """

    def __init__(self, storage_dir: str = "opportunity_pipelines"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _filepath(self, pipeline_id: str) -> str:
        """Get the file path for a pipeline."""
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in pipeline_id)
        return os.path.join(self.storage_dir, f"{safe_id}.json")

    def create_pipeline(self, name: str) -> OpportunityPipeline:
        """Create a new pipeline and persist it."""
        pipeline = OpportunityPipeline.create_pipeline(name)
        self.save(pipeline)
        return pipeline

    def save(self, pipeline: OpportunityPipeline) -> None:
        """Save a pipeline to disk."""
        filepath = self._filepath(pipeline.pipeline_id)
        with open(filepath, "w") as f:
            f.write(pipeline.to_json())

    def get(self, pipeline_id: str) -> OpportunityPipeline | None:
        """Load a pipeline by ID."""
        filepath = self._filepath(pipeline_id)
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r") as f:
            return OpportunityPipeline.from_json(f.read())

    # Alias for test compatibility
    get_pipeline = get

    def delete(self, pipeline_id: str) -> bool:
        """Delete a pipeline by ID."""
        filepath = self._filepath(pipeline_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def list_pipelines(self) -> list[OpportunityPipeline]:
        """List all pipelines."""
        pipelines = []
        if not os.path.exists(self.storage_dir):
            return pipelines
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.storage_dir, filename)
                with open(filepath, "r") as f:
                    pipelines.append(OpportunityPipeline.from_json(f.read()))
        return pipelines

    def add_opportunity(self, pipeline_id: str, opportunity: Opportunity) -> OpportunityPipeline:
        """Add an opportunity to an existing pipeline."""
        pipeline = self.get(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        pipeline.add_opportunity(opportunity)
        self.save(pipeline)
        return pipeline

    def update_stage(self, pipeline_id: str, opportunity_id: str, new_stage: OpportunityStage) -> Opportunity:
        """Update the stage of an opportunity."""
        pipeline = self.get(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        opp = pipeline.get_by_id(opportunity_id)
        if opp is None:
            raise ValueError(f"Opportunity {opportunity_id} not found in pipeline")
        
        opp.update_stage(new_stage)
        self.save(pipeline)
        return opp

    def get_pipeline_stats(self, pipeline_id: str) -> dict[str, Any]:
        """Get statistics for a pipeline."""
        pipeline = self.get(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        stats = {
            "pipeline_id": pipeline.pipeline_id,
            "name": pipeline.name,
            "total_opportunities": len(pipeline.opportunities),
            "by_stage": {},
            "avg_score": 0.0,
            "top_opportunities": [],
        }
        
        if not pipeline.opportunities:
            return stats
        
        # Count by stage
        stage_counts = {}
        for opp in pipeline.opportunities:
            stage_name = opp.stage.value
            stage_counts[stage_name] = stage_counts.get(stage_name, 0) + 1
        stats["by_stage"] = stage_counts
        
        # Average score
        scores = [opp.score for opp in pipeline.opportunities]
        stats["avg_score"] = sum(scores) / len(scores) if scores else 0.0
        
        # Top opportunities (by score)
        sorted_opps = sorted(pipeline.opportunities, key=lambda o: o.score, reverse=True)
        stats["top_opportunities"] = [
            {
                "id": opp.opportunity_id,
                "client": opp.client_name,
                "service": opp.service_title,
                "score": opp.score,
                "stage": opp.stage.value,
            }
            for opp in sorted_opps[:5]
        ]
        
        return stats

    def export_pipeline(self, pipeline_id: str, output_path: str) -> None:
        """Export a pipeline to a file."""
        pipeline = self.get(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        with open(output_path, "w") as f:
            f.write(pipeline.to_json())

    def import_pipeline(self, input_path: str) -> OpportunityPipeline:
        """Import a pipeline from a file."""
        with open(input_path, "r") as f:
            pipeline = OpportunityPipeline.from_json(f.read())
        self.save(pipeline)
        return pipeline
