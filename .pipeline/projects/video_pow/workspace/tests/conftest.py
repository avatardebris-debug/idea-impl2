"""Shared test fixtures for VideoPow tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_video_file():
    """Create a temporary fake video file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video data for testing")
        f.flush()
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_text_file():
    """Create a temporary text file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("test content")
        f.flush()
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for testing."""
    import json
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({"test": "data"}, f)
        f.flush()
        yield f.name
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def sample_video_description():
    """Provide a sample video description for testing."""
    return {
        "scene": "a cat sitting on a windowsill",
        "effect": "grayscale",
        "transition": "fade",
        "duration": 10,
        "subject": "cat",
        "mood": "neutral"
    }


@pytest.fixture
def sample_prompt():
    """Provide a sample prompt for testing."""
    return "Generate a video of a cat sitting on a windowsill with grayscale effect, fade transition, 10 seconds duration, neutral mood"
