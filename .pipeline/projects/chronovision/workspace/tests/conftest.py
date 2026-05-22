"""Pytest configuration for Chronovision tests."""

import pytest
import numpy as np


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "X": np.random.randn(100, 14),
        "y": np.random.randn(100, 1),
    }


@pytest.fixture
def sample_entity():
    """Sample entity for testing."""
    from chronovision.src.model.entity import Entity
    return Entity(ticker="AAPL", name="Apple Inc.", price=100.0)


@pytest.fixture
def sample_state_space():
    """Sample state space for testing."""
    from chronovision.src.model.state_space import StateSpace
    ss = StateSpace()
    ss.add_entity(Entity(ticker="AAPL", price=100.0))
    ss.add_entity(Entity(ticker="MSFT", price=200.0))
    ss.add_edge("AAPL", "MSFT", "competitor")
    return ss


@pytest.fixture
def sample_predictor():
    """Sample predictor for testing."""
    from chronovision.src.predictor.lstm_predictor import LSTMPredictor
    return LSTMPredictor(hidden_dim=32, epochs=10, lr=0.01)


@pytest.fixture
def sample_workflow():
    """Sample workflow for testing."""
    from chronovision.src.orchestrator.workflow import Workflow
    return Workflow(name="Test", description="Test workflow")
