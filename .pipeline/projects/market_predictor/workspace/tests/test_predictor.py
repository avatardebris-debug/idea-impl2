"""tests for market_predictor."""
from unittest.mock import patch
from market_predictor.predictor import _generate_mock_prices, _fallback_forecast, forecast_asset, format_markdown

def test_generate_mock_prices():
    prices = _generate_mock_prices("AAPL", 10)
    assert len(prices) == 11
    assert "price" in prices[0]

def test_fallback_forecast():
    prices = _generate_mock_prices("AAPL", 5)
    res = _fallback_forecast("AAPL", prices)
    assert res["ticker"] == "AAPL"
    assert res["forecast"] in ["Bullish", "Bearish"]

def test_forecast_asset_fallback_on_failure():
    with patch("market_predictor.predictor._call_ollama", return_value="invalid json"):
        res = forecast_asset("TSLA", 5)
    assert res["ticker"] == "TSLA"

def test_format_markdown():
    prices = _generate_mock_prices("BTC", 2)
    data = _fallback_forecast("BTC", prices)
    md = format_markdown(data)
    assert "# 📈 Market Forecast: BTC" in md
    assert "**Forecast:**" in md
