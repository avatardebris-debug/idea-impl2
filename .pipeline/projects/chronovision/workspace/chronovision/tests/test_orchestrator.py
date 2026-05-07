"""Tests for the orchestrator layer."""

import pytest
from unittest.mock import MagicMock, patch

from chronovision.src.orchestrator.workflow import Workflow, WorkflowStatus, Step
from chronovision.src.orchestrator.runner import Runner


class TestWorkflow:
    """Tests for Workflow."""
    
    def test_init(self):
        """Test initialization."""
        workflow = Workflow(name="Test")
        assert workflow.name == "Test"
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.steps == []
        assert workflow.context == {}
    
    def test_add_step(self):
        """Test adding a step."""
        workflow = Workflow(name="Test")
        workflow.add_step("step1", lambda: "result")
        
        assert len(workflow.steps) == 1
        assert workflow.steps[0].name == "step1"
    
    def test_run_success(self):
        """Test successful workflow run."""
        workflow = Workflow(name="Test")
        workflow.add_step("step1", lambda: "result1")
        workflow.add_step("step2", lambda: "result2")
        
        results = workflow.run()
        
        assert workflow.status == WorkflowStatus.COMPLETED
        assert results["status"] == "completed"
        assert results["step1"] == "result1"
        assert results["step2"] == "result2"
    
    def test_run_failure(self):
        """Test workflow run with failure."""
        def failing_func():
            raise ValueError("Test error")
        
        workflow = Workflow(name="Test")
        workflow.add_step("step1", lambda: "result1")
        workflow.add_step("step2", failing_func)
        
        results = workflow.run()
        
        assert workflow.status == WorkflowStatus.FAILED
        assert results["status"] == "failed"
        assert "error" in results
    
    def test_get_status(self):
        """Test getting workflow status."""
        workflow = Workflow(name="Test")
        workflow.add_step("step1", lambda: "result")
        
        status = workflow.get_status()
        
        assert status["name"] == "Test"
        assert status["status"] == "pending"
        assert len(status["steps"]) == 1
    
    def test_reset(self):
        """Test resetting workflow."""
        workflow = Workflow(name="Test")
        workflow.add_step("step1", lambda: "result")
        workflow.run()
        
        workflow.reset()
        
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.context == {}
        assert workflow.steps[0].status == "pending"


class TestRunner:
    """Tests for Runner."""
    
    def test_init(self):
        """Test initialization."""
        runner = Runner(db_url="sqlite:///test.db")
        assert runner.data_loader is not None
        assert runner.sec_importer is not None
        assert runner.state_space is not None
        assert runner.graph_builder is not None
        assert runner.updater is not None
        assert runner.predictor is not None
    
    def test_build_workflow(self):
        """Test building workflow."""
        runner = Runner()
        workflow = runner.build_workflow(["AAPL"])
        
        assert workflow is not None
        assert len(workflow.steps) > 0
        assert workflow.name == "Chronovision"
    
    def test_run_workflow(self):
        """Test running workflow."""
        runner = Runner()
        workflow = runner.build_workflow(["AAPL"])
        
        # Mock the steps to avoid actual execution
        with patch.object(runner, '_prepare_training_data', return_value={"X": None, "y": None}):
            with patch.object(runner, '_train_predictor', return_value={"error": "No data"}):
                results = runner.run(["AAPL"])
                
                assert results is not None
    
    def test_get_world_state(self):
        """Test getting world state."""
        runner = Runner()
        state = runner.get_world_state()
        
        assert "entities" in state
        assert "edges" in state
    
    def test_get_predictions_empty(self):
        """Test getting predictions when none available."""
        runner = Runner()
        predictions = runner.get_predictions()
        
        assert predictions == {}
