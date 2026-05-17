"""Tests for AgentFlow exceptions."""

import pytest
from agentflow_drophip.exceptions import (
    AgentFlowError,
    AgentError,
    OrchestratorError,
    ParserError,
    WorkflowError,
)


class TestAgentFlowError:
    def test_base_error_message(self):
        error = AgentFlowError("Test error")
        assert str(error) == "Test error"

    def test_base_error_with_details(self):
        error = AgentFlowError("Test error", details={"key": "value"})
        assert "Test error" in str(error)
        assert "key" in str(error)

    def test_base_error_attributes(self):
        error = AgentFlowError("Test error", details={"key": "value"})
        assert error.message == "Test error"
        assert error.details == {"key": "value"}


class TestAgentError:
    def test_agent_error_message(self):
        error = AgentError("Agent failed", agent_name="test_agent")
        assert str(error) == "Agent failed"
        assert error.agent_name == "test_agent"


class TestOrchestratorError:
    def test_orchestrator_error_message(self):
        error = OrchestratorError("Orchestrator failed", action="workflow")
        assert str(error) == "Orchestrator failed"
        assert error.action == "workflow"


class TestParserError:
    def test_parser_error_message(self):
        error = ParserError("Parse failed", description="test input")
        assert str(error) == "Parse failed"
        assert error.description == "test input"


class TestWorkflowError:
    def test_workflow_error_message(self):
        error = WorkflowError("Workflow failed", task_id="task_1")
        assert str(error) == "Workflow failed"
        assert error.task_id == "task_1"
