"""Aggregation Service for Pipeline Observability Dashboard."""
from pathlib import Path
from typing import List

from pipeline_observability_dashboard.models import GlobalMetrics, ProjectState
from pipeline_observability_dashboard.scanner import PipelineScanner

class AggregationService:
    """Aggregates metrics and states across all pipeline projects."""
    
    def __init__(self, pipeline_root: Path):
        self.scanner = PipelineScanner(pipeline_root)
        
    def get_all_projects_status(self) -> List[ProjectState]:
        """Get the state of all discovered projects."""
        return self.scanner.get_all_projects_state()
        
    def get_global_metrics(self) -> GlobalMetrics:
        """Calculate global metrics across the entire pipeline."""
        states = self.get_all_projects_status()
        metrics = GlobalMetrics()
        
        metrics.total_projects = len(states)
        for state in states:
            metrics.total_cost_estimate += state.cost_estimate
            
            # Simple heuristic for active vs completed vs blocked
            if not state.phases:
                continue
                
            # If the current phase has retries exceeding max, it's blocked
            current_phase_obj = next((p for p in state.phases if p.name == state.current_phase), None)
            
            if current_phase_obj:
                if current_phase_obj.status == "blocked" or (current_phase_obj.max_retries > 0 and current_phase_obj.retries >= current_phase_obj.max_retries):
                    metrics.blocked_projects += 1
                elif current_phase_obj.status == "completed":
                    # Check if all phases are completed (this is a simple approximation)
                    all_completed = all(p.status == "completed" for p in state.phases)
                    if all_completed:
                        metrics.completed_projects += 1
                    else:
                        metrics.active_projects += 1
                else:
                    metrics.active_projects += 1
            else:
                metrics.active_projects += 1
                
        return metrics
