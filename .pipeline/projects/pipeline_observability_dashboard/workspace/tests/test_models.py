"""Tests for core data models."""
from pipeline_observability_dashboard.models import PhaseStatus, ProjectState, GlobalMetrics

def test_phase_status_initialization():
    phase = PhaseStatus(name="phase_1", status="running", retries=2, max_retries=5)
    assert phase.name == "phase_1"
    assert phase.status == "running"
    assert phase.retries == 2
    assert phase.max_retries == 5

def test_phase_status_defaults():
    phase = PhaseStatus(name="phase_2")
    assert phase.status == "unknown"
    assert phase.retries == 0

def test_project_state_initialization():
    project = ProjectState(
        project_name="test_project",
        idea_name="Test Idea",
        current_phase="phase_1",
        phases=[PhaseStatus(name="phase_1")]
    )
    assert project.project_name == "test_project"
    assert project.idea_name == "Test Idea"
    assert project.current_phase == "phase_1"
    assert len(project.phases) == 1
    assert project.cost_estimate == 0.0

def test_global_metrics_defaults():
    metrics = GlobalMetrics()
    assert metrics.total_projects == 0
    assert metrics.total_cost_estimate == 0.0
