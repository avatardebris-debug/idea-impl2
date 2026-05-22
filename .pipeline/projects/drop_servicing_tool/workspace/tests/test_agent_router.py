"""Tests for Agent Router and Cost Tracking."""

import pytest
from drop_servicing_tool.agent_router import (
    AgentRouter,
    LLMClientRouter,
    ExecutionCost,
    StepCost,
)


class TestStepCost:
    """Tests for StepCost model."""

    def test_step_cost_creation(self):
        """Test creating a StepCost."""
        cost = StepCost(
            step_name="test_step",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.001
        )
        assert cost.step_name == "test_step"
        assert cost.input_tokens == 100
        assert cost.output_tokens == 50
        assert cost.total_tokens == 150
        assert cost.cost_usd == 0.001

    def test_step_cost_defaults(self):
        """Test StepCost default values."""
        cost = StepCost(step_name="test_step")
        assert cost.input_tokens == 0
        assert cost.output_tokens == 0
        assert cost.total_tokens == 0
        assert cost.cost_usd == 0.0

    def test_step_cost_total_calculation(self):
        """Test that total_tokens is calculated correctly."""
        cost = StepCost(
            step_name="test_step",
            input_tokens=100,
            output_tokens=50
        )
        assert cost.total_tokens == 150


class TestExecutionCost:
    """Tests for ExecutionCost model."""

    def test_execution_cost_creation(self):
        """Test creating an ExecutionCost."""
        cost = ExecutionCost(
            total_input_tokens=1000,
            total_output_tokens=500,
            total_tokens=1500,
            total_cost_usd=0.015
        )
        assert cost.total_input_tokens == 1000
        assert cost.total_output_tokens == 500
        assert cost.total_tokens == 1500
        assert cost.total_cost_usd == 0.015

    def test_execution_cost_with_steps(self):
        """Test ExecutionCost with step costs."""
        step_costs = [
            StepCost(step_name="step1", input_tokens=100, output_tokens=50, cost_usd=0.001),
            StepCost(step_name="step2", input_tokens=200, output_tokens=100, cost_usd=0.002)
        ]
        cost = ExecutionCost(
            total_input_tokens=300,
            total_output_tokens=150,
            total_tokens=450,
            total_cost_usd=0.003,
            step_costs=step_costs
        )
        assert len(cost.step_costs) == 2
        assert cost.step_costs[0].step_name == "step1"

    def test_execution_cost_defaults(self):
        """Test ExecutionCost default values."""
        cost = ExecutionCost()
        assert cost.total_input_tokens == 0
        assert cost.total_output_tokens == 0
        assert cost.total_tokens == 0
        assert cost.total_cost_usd == 0.0
        assert cost.step_costs == []


class TestAgentRouter:
    """Tests for AgentRouter class."""

    def test_router_initialization(self):
        """Test router initialization."""
        router = AgentRouter()
        assert router is not None

    def test_router_default_mode(self):
        """Test router default mode."""
        router = AgentRouter()
        assert router.mode == "auto"

    def test_router_set_mode(self):
        """Test setting router mode."""
        router = AgentRouter()
        router.set_mode("step")
        assert router.mode == "step"

        router.set_mode("freeform")
        assert router.mode == "freeform"

    def test_router_invalid_mode(self):
        """Test setting invalid mode."""
        router = AgentRouter()
        with pytest.raises(ValueError, match="Invalid mode"):
            router.set_mode("invalid_mode")


class TestLLMClientRouter:
    """Tests for LLMClientRouter class."""

    def test_router_initialization(self):
        """Test LLMClientRouter initialization."""
        router = LLMClientRouter()
        assert router is not None

    def test_router_default_mode(self):
        """Test LLMClientRouter default mode."""
        router = LLMClientRouter()
        assert router.mode == "auto"

    def test_router_set_mode(self):
        """Test setting LLMClientRouter mode."""
        router = LLMClientRouter()
        router.set_mode("step")
        assert router.mode == "step"

    def test_router_mode_validation(self):
        """Test LLMClientRouter mode validation."""
        router = LLMClientRouter()
        with pytest.raises(ValueError, match="Invalid mode"):
            router.set_mode("invalid_mode")


class TestCostTracking:
    """Tests for cost tracking functionality."""

    def test_cost_accumulation(self):
        """Test accumulating costs across steps."""
        step_costs = [
            StepCost(step_name="step1", input_tokens=100, output_tokens=50, cost_usd=0.001),
            StepCost(step_name="step2", input_tokens=200, output_tokens=100, cost_usd=0.002),
            StepCost(step_name="step3", input_tokens=300, output_tokens=150, cost_usd=0.003)
        ]

        total_input = sum(c.input_tokens for c in step_costs)
        total_output = sum(c.output_tokens for c in step_costs)
        total_cost = sum(c.cost_usd for c in step_costs)

        assert total_input == 600
        assert total_output == 300
        assert total_cost == 0.006

    def test_cost_calculation(self):
        """Test cost calculation from tokens."""
        # Assuming $0.00001 per token for testing
        input_tokens = 1000
        output_tokens = 500
        cost_per_token = 0.00001

        expected_cost = (input_tokens + output_tokens) * cost_per_token

        cost = ExecutionCost(
            total_input_tokens=input_tokens,
            total_output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            total_cost_usd=expected_cost
        )

        assert cost.total_cost_usd == expected_cost


class TestRouterIntegration:
    """Integration tests for router functionality."""

    def test_router_with_cost_tracking(self):
        """Test router with cost tracking."""
        router = AgentRouter()
        router.set_mode("step")

        # Simulate step costs
        step_costs = [
            StepCost(step_name="step1", input_tokens=100, output_tokens=50, cost_usd=0.001),
            StepCost(step_name="step2", input_tokens=200, output_tokens=100, cost_usd=0.002)
        ]

        total_input = sum(c.input_tokens for c in step_costs)
        total_output = sum(c.output_tokens for c in step_costs)
        total_cost = sum(c.cost_usd for c in step_costs)

        execution_cost = ExecutionCost(
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_input + total_output,
            total_cost_usd=total_cost,
            step_costs=step_costs
        )

        assert execution_cost.total_cost_usd == 0.003
        assert len(execution_cost.step_costs) == 2

    def test_router_mode_persistence(self):
        """Test that router mode persists."""
        router = AgentRouter()
        router.set_mode("step")

        # Mode should persist
        assert router.mode == "step"

        router.set_mode("freeform")
        assert router.mode == "freeform"
