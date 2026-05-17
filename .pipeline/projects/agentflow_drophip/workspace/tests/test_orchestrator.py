"""Tests for AgentFlow orchestrator."""

import pytest
from agentflow_drophip.orchestrator import Orchestrator
from agentflow_drophip.models.business_spec import BusinessSpec


class TestOrchestrator:
    def setup_method(self):
        self.orchestrator = Orchestrator()

    def test_setup_business(self):
        description = "I want to start a dropshipping business selling electronics on Shopify"
        spec = self.orchestrator.setup_business(description)

        assert isinstance(spec, BusinessSpec)
        assert spec.niche == "electronics"
        assert spec.storefront_type.name == "SHOPIFY"

    def test_run_full_workflow(self):
        description = "I want to start a dropshipping business selling electronics on Shopify"
        spec = self.orchestrator.setup_business(description)

        result = self.orchestrator.run_full_workflow(spec)

        assert result.is_success
        assert "sourcing" in result.data
        assert "listing" in result.data
        assert "fulfillment" in result.data

    def test_run_full_workflow_with_error(self):
        # This test simulates a workflow failure
        description = "I want to start a dropshipping business selling electronics on Shopify"
        spec = self.orchestrator.setup_business(description)

        # Mock the workflow execution to fail
        original_execute = self.orchestrator.workflow_engine.execute

        def mock_execute(task_handlers):
            return type('obj', (object,), {
                'is_success': False,
                'error': 'Workflow failed'
            })()

        self.orchestrator.workflow_engine.execute = mock_execute

        result = self.orchestrator.run_full_workflow(spec)

        assert result.is_failure
        assert "Workflow failed" in result.error

        # Restore original method
        self.orchestrator.workflow_engine.execute = original_execute

    def test_get_status(self):
        status = self.orchestrator.get_status()

        assert "workflow_id" in status
        assert "spec" in status
        assert "status" in status

    def test_reset(self):
        description = "I want to start a dropshipping business selling electronics on Shopify"
        self.orchestrator.setup_business(description)

        self.orchestrator.reset()

        status = self.orchestrator.get_status()
        assert status["status"] == "idle"
