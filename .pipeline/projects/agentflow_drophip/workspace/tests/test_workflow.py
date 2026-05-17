"""Tests for AgentFlow workflow engine."""

import pytest
from agentflow_drophip.workflow.dsl import standard_dropshipping_workflow
from agentflow_drophip.workflow.engine import TaskResult, TaskStatus, WorkflowEngine
from agentflow_drophip.models.business_spec import BusinessSpec


class TestWorkflowEngine:
    def setup_method(self):
        self.spec = BusinessSpec(niche="electronics")

    def test_create_workflow(self):
        dag = standard_dropshipping_workflow(self.spec)
        engine = WorkflowEngine(dag)

        assert engine.workflow_id is not None
        assert len(engine.tasks) > 0

    def test_execute_workflow(self):
        dag = standard_dropshipping_workflow(self.spec)
        engine = WorkflowEngine(dag)

        task_handlers = {
            "sourcing": lambda t: type('obj', (object,), {
                'success': True,
                'data': {'products': [{'id': 'prod_1', 'name': 'Test Product', 'price': 10.0}]}
            })(),
            "listing": lambda t: type('obj', (object,), {
                'success': True,
                'data': {'listings': [{'id': 'list_1', 'product_id': 'prod_1'}]}
            })(),
            "fulfillment": lambda t: type('obj', (object,), {
                'success': True,
                'data': {'orders_processed': 0}
            })(),
        }

        result = engine.execute(task_handlers=task_handlers)

        assert result.is_success
        assert len(result.data) > 0

    def test_execute_workflow_with_failure(self):
        dag = standard_dropshipping_workflow(self.spec)
        engine = WorkflowEngine(dag)

        task_handlers = {
            "sourcing": lambda t: type('obj', (object,), {
                'success': False,
                'error': 'Sourcing failed'
            })(),
            "listing": lambda t: type('obj', (object,), {
                'success': True,
                'data': {}
            })(),
            "fulfillment": lambda t: type('obj', (object,), {
                'success': True,
                'data': {}
            })(),
        }

        result = engine.execute(task_handlers=task_handlers)

        assert result.is_failure
        assert "Sourcing failed" in result.error

    def test_get_status(self):
        dag = standard_dropshipping_workflow(self.spec)
        engine = WorkflowEngine(dag)

        status = engine.get_status()

        assert "workflow_id" in status
        assert "tasks" in status
        assert len(status["tasks"]) > 0

    def test_reset(self):
        dag = standard_dropshipping_workflow(self.spec)
        engine = WorkflowEngine(dag)

        engine.reset()

        status = engine.get_status()
        assert status["status"] == "idle"
