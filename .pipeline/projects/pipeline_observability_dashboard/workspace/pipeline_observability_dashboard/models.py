"""Core data models for Pipeline Observability Dashboard."""
from typing import List, Optional
from pydantic import BaseModel, Field

class PhaseStatus(BaseModel):
    """Represents the status of a specific phase."""
    name: str
    status: str = "unknown"
    retries: int = 0
    max_retries: int = 0

class ProjectState(BaseModel):
    """Represents the complete state of a project pipeline."""
    project_name: str
    idea_name: Optional[str] = None
    current_phase: Optional[str] = None
    phases: List[PhaseStatus] = Field(default_factory=list)
    
    # Phase 2 additions
    cost_estimate: float = 0.0
    error_rate: float = 0.0
    avg_step_duration: float = 0.0

class GlobalMetrics(BaseModel):
    """Global aggregation of all pipeline metrics."""
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    blocked_projects: int = 0
    total_cost_estimate: float = 0.0
