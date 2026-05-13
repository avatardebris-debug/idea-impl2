"""Test fixtures for Chronovision2."""

import pytest


@pytest.fixture
def sample_state():
    """Sample world state for testing."""
    return {"x": 10.0, "y": 20.0, "z": 30.0}


@pytest.fixture
def sample_hypothesis():
    """Sample hypothesis for testing."""
    return {
        "id": "test_hypothesis",
        "config": {
            "hypothesis_id": "test",
            "rules": {
                "growth": {"type": "growth", "growth_rate": 0.1}
            }
        },
        "weight": 1.0,
    }


@pytest.fixture
def sample_predictions():
    """Sample predictions for testing."""
    return [
        {"x": 10.0, "y": 20.0},
        {"x": 12.0, "y": 22.0},
        {"x": 11.0, "y": 21.0},
    ]
