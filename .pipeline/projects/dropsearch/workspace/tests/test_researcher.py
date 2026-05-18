"""tests for dropsearch."""
from unittest.mock import patch
from dropsearch.researcher import _mock_competitor_data, _fallback_plan, analyze_niche, format_markdown

def test_mock_competitors():
    comp = _mock_competitor_data("Dog Toys")
    assert len(comp) > 0
    assert "Dog" in comp[0]["name"]

def test_fallback_plan():
    res = _fallback_plan("Cats", [])
    assert res["niche"] == "Cats"
    assert "operational_gameplan" in res

def test_analyze_niche_fallback_on_failure():
    with patch("dropsearch.researcher._call_ollama", return_value="invalid json"):
        res = analyze_niche("LED Lights")
    assert res["niche"] == "LED Lights"

def test_format_markdown():
    data = _fallback_plan("Test", [])
    md = format_markdown(data)
    assert "# 🕵️ DropSearch Gameplan: Test" in md
