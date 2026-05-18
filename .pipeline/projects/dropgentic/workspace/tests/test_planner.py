"""tests for dropgentic."""
from unittest.mock import patch
from dropgentic.planner import _fallback_workflows, orchestrate_workflows, format_markdown

def test_fallback_workflows():
    res = _fallback_workflows("some plan")
    assert "Sourcing Agent" in res["workflows"][0]["agent_role"]

def test_orchestrate_workflows_fallback_on_failure():
    with patch("dropgentic.planner._call_ollama", return_value="invalid json"):
        res = orchestrate_workflows("plan")
    assert "workflows" in res

def test_format_markdown():
    data = _fallback_workflows("plan")
    md = format_markdown(data)
    assert "# 🤖 DropGentic Plan" in md
    assert "- [ ]" in md
