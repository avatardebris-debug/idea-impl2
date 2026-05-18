"""Tests for scanner and extractor."""
import json
from pathlib import Path
from pipeline_observability_dashboard.scanner import PipelineScanner, StateExtractor

def test_state_extractor(tmp_path):
    project_dir = tmp_path / "test_project"
    state_dir = project_dir / "state"
    state_dir.mkdir(parents=True)
    
    (state_dir / "current_idea.json").write_text(json.dumps({"title": "My Great Idea"}))
    (state_dir / "current_phase.json").write_text(json.dumps({"phase": "phase_2"}))
    (state_dir / "phase_retries.json").write_text(json.dumps({
        "phase_1": {"retries": 1, "max_retries": 3, "status": "completed"},
        "phase_2": {"retries": 0, "max_retries": 3, "status": "running"}
    }))
    
    extractor = StateExtractor(project_dir)
    state = extractor.extract("test_project")
    
    assert state.project_name == "test_project"
    assert state.idea_name == "My Great Idea"
    assert state.current_phase == "phase_2"
    assert len(state.phases) == 2
    
    p1 = next(p for p in state.phases if p.name == "phase_1")
    assert p1.status == "completed"
    assert p1.retries == 1

def test_pipeline_scanner(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    
    p1 = projects_dir / "project_a"
    (p1 / "state").mkdir(parents=True)
    
    p2 = projects_dir / "project_b"
    (p2 / "state").mkdir(parents=True)
    
    scanner = PipelineScanner(tmp_path)
    projects = scanner.discover_projects()
    
    assert len(projects) == 2
    names = {p.name for p in projects}
    assert names == {"project_a", "project_b"}

def test_pipeline_scanner_get_all(tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    
    p1 = projects_dir / "project_a"
    (p1 / "state").mkdir(parents=True)
    (p1 / "state" / "current_phase.json").write_text(json.dumps({"phase": "phase_1"}))
    
    scanner = PipelineScanner(tmp_path)
    states = scanner.get_all_projects_state()
    
    assert len(states) == 1
    assert states[0].project_name == "project_a"
    assert states[0].current_phase == "phase_1"
