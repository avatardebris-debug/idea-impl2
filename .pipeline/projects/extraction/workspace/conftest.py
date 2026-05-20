"""
conftest.py — Shared pytest fixtures for the extraction project.

Fixtures:
    sample_text: A short recipe-like text for testing.
    sample_sop: A short SOP-like text for testing.
    sample_steps: A short numbered-steps text for testing.
    sample_empty: Empty string (edge case).
    sample_malformed_json: Text that looks like it could be JSON but isn't.
    mock_ollama_response: A valid JSON response dict mimicking Ollama output.
    mock_ollama_empty: An empty string response (triggers fallback).
    mock_ollama_malformed: A string with invalid JSON (triggers fallback).
"""
import sys
import pathlib
import json
import pytest

# Inject workspace into sys.path so `import extraction` works in tests
_ws = pathlib.Path(__file__).resolve().parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))


# ---------------------------------------------------------------------------
# Sample input texts
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_text():
    """A cooking-recipe-style text."""
    return (
        "How to Make Pancakes\n\n"
        "First, mix 1 cup of flour with 2 eggs and a pinch of salt.\n"
        "Then, add 3/4 cup of milk and stir until smooth.\n"
        "Next, heat a pan over medium heat and pour in the batter.\n"
        "Cook for 3 minutes on each side until golden brown.\n"
        "Serve with maple syrup and fresh berries.\n"
    )


@pytest.fixture
def sample_sop():
    """A standard-operating-procedure-style text."""
    return (
        "SOP: Server Restart\n\n"
        "1. Log in to the server via SSH.\n"
        "2. Run 'systemctl stop nginx' to stop the web server.\n"
        "3. Verify the process has stopped with 'ps aux | grep nginx'.\n"
        "4. Run 'systemctl start nginx' to restart the web server.\n"
        "5. Check the logs at /var/log/nginx/error.log for any issues.\n"
    )


@pytest.fixture
def sample_steps():
    """A numbered-steps-style text."""
    return (
        "Steps to Reset a Router:\n\n"
        "1. Locate the reset button on the back of the router.\n"
        "2. Press and hold the reset button for 10 seconds.\n"
        "3. Wait for the router to reboot (about 2 minutes).\n"
        "4. Reconnect to the default Wi-Fi network.\n"
        "5. Open a browser and navigate to the admin panel.\n"
    )


@pytest.fixture
def sample_empty():
    """Empty string for edge-case testing."""
    return ""


@pytest.fixture
def sample_malformed_json():
    """Text that looks like JSON but is not valid."""
    return '{"title": "test", "steps": [1, 2, 3'


# ---------------------------------------------------------------------------
# Mock Ollama responses
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ollama_response():
    """A valid JSON response dict mimicking Ollama output."""
    return {
        "title": "Test Pancakes",
        "topic": "cooking",
        "format": "recipe",
        "description": "A simple pancake recipe",
        "components": [
            {"name": "flour", "quantity": "1", "unit": "cup", "notes": ""},
            {"name": "eggs", "quantity": "2", "unit": "", "notes": ""},
            {"name": "milk", "quantity": "3/4", "unit": "cup", "notes": ""},
        ],
        "steps": [
            {"action": "Mix dry ingredients", "detail": "Combine flour and salt"},
            {"action": "Add wet ingredients", "detail": "Pour in milk and eggs"},
            {"action": "Cook", "detail": "Heat pan and pour batter"},
        ],
        "tips": ["Use fresh eggs for best results"],
    }


@pytest.fixture
def mock_ollama_response_json_str(mock_ollama_response):
    """The mock response as a JSON string (what Ollama would return)."""
    return json.dumps(mock_ollama_response)


@pytest.fixture
def mock_ollama_empty():
    """An empty string response — triggers fallback."""
    return ""


@pytest.fixture
def mock_ollama_malformed():
    """A string with invalid JSON — triggers fallback."""
    return "not valid json at all {{{"


@pytest.fixture
def mock_ollama_no_steps():
    """Valid JSON but missing the 'steps' key — triggers fallback."""
    return json.dumps({"title": "No Steps", "topic": "test"})
