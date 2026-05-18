"""tests for saas_pricing."""
from unittest.mock import patch
from saas_pricing.analyzer import _fallback_pricing, analyze_pricing, format_markdown

def test_fallback_pricing():
    res = _fallback_pricing("AcmeSaaS", "desc")
    assert res["product_name"] == "AcmeSaaS"
    assert len(res["tiers"]) == 3

def test_analyze_pricing_fallback_on_failure():
    with patch("saas_pricing.analyzer._call_ollama", return_value="invalid json"):
        res = analyze_pricing("TestSaaS", "test")
    assert res["product_name"] == "TestSaaS"
    assert res["tiers"][0]["name"] == "Starter"

def test_format_markdown():
    data = _fallback_pricing("AcmeSaaS", "desc")
    md = format_markdown(data)
    assert "# 🏷️ SaaS Pricing Strategy: AcmeSaaS" in md
    assert "### Pro — $49/mo" in md
