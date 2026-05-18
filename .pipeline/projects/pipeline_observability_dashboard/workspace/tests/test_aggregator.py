"""Tests for Aggregation Service."""
import json
from pathlib import Path
from pipeline_observability_dashboard.aggregator import AggregationService

def test_aggregation_service(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    
    # Project 1: Active
    p1 = projects_dir / "project_a"
    (p1 / "state").mkdir(parents=True)
    (p1 / "state" / "current_phase.json").write_text(json.dumps({"phase": "phase_1"}))
    (p1 / "state" / "phase_retries.json").write_text(json.dumps({
        "phase_1": {"retries": 1, "max_retries": 3, "status": "running"}
    }))
    
    # Project 2: Blocked
    p2 = projects_dir / "project_b"
    (p2 / "state").mkdir(parents=True)
    (p2 / "state" / "current_phase.json").write_text(json.dumps({"phase": "phase_2"}))
    (p2 / "state" / "phase_retries.json").write_text(json.dumps({
        "phase_2": {"retries": 3, "max_retries": 3, "status": "blocked"}
    }))
    
    # Project 3: Completed
    p3 = projects_dir / "project_c"
    (p3 / "state").mkdir(parents=True)
    (p3 / "state" / "current_phase.json").write_text(json.dumps({"phase": "phase_1"}))
    (p3 / "state" / "phase_retries.json").write_text(json.dumps({
        "phase_1": {"retries": 0, "max_retries": 3, "status": "completed"}
    }))
    
    service = AggregationService(tmp_path)
    states = service.get_all_projects_status()
    assert len(states) == 3
    
    metrics = service.get_global_metrics()
    assert metrics.total_projects == 3
    assert metrics.active_projects == 1
    assert metrics.blocked_projects == 1
    assert metrics.completed_projects == 1
