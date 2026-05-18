"""Directory Scanner and State Extractor for Pipeline Observability Dashboard."""
import json
import os
from pathlib import Path
from typing import List, Optional

from pipeline_observability_dashboard.models import ProjectState, PhaseStatus

class StateExtractor:
    """Extracts project state from a project's state/ directory."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.state_dir = project_path / "state"
        
    def _read_json(self, filename: str) -> dict:
        path = self.state_dir / filename
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
            
    def get_idea_name(self) -> Optional[str]:
        data = self._read_json("current_idea.json")
        return data.get("title") or data.get("name")
        
    def get_current_phase(self) -> Optional[str]:
        data = self._read_json("current_phase.json")
        return data.get("phase")
        
    def get_phases(self) -> List[PhaseStatus]:
        retries_data = self._read_json("phase_retries.json")
        phases = []
        for phase_name, retry_info in retries_data.items():
            if isinstance(retry_info, dict):
                phases.append(PhaseStatus(
                    name=phase_name,
                    retries=retry_info.get("retries", 0),
                    max_retries=retry_info.get("max_retries", 0),
                    status=retry_info.get("status", "unknown")
                ))
            elif isinstance(retry_info, int):
                phases.append(PhaseStatus(
                    name=phase_name,
                    retries=retry_info,
                    status="unknown"
                ))
        return phases
        
    def extract(self, project_name: str) -> ProjectState:
        from pipeline_observability_dashboard.telemetry import TelemetryParser
        
        # Parse metrics if available
        parser = TelemetryParser(self.project_path)
        cost, error_rate, avg_duration = parser.parse_metrics()
        
        return ProjectState(
            project_name=project_name,
            idea_name=self.get_idea_name(),
            current_phase=self.get_current_phase(),
            phases=self.get_phases(),
            cost_estimate=cost,
            error_rate=error_rate,
            avg_step_duration=avg_duration
        )

class PipelineScanner:
    """Scans the pipeline root directory for projects."""
    
    def __init__(self, pipeline_root: Path):
        self.pipeline_root = Path(pipeline_root)
        self.projects_dir = self.pipeline_root / "projects"
        
    def discover_projects(self) -> List[Path]:
        """Return a list of project directories."""
        if not self.projects_dir.exists():
            return []
            
        projects = []
        for item in self.projects_dir.iterdir():
            if item.is_dir() and (item / "state").exists():
                projects.append(item)
        return projects
        
    def get_all_projects_state(self) -> List[ProjectState]:
        """Discover all projects and extract their state."""
        states = []
        for project_dir in self.discover_projects():
            extractor = StateExtractor(project_dir)
            states.append(extractor.extract(project_dir.name))
        return states
