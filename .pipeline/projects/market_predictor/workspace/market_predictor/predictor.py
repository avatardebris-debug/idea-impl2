"""
predictor.py — Market simulation and prediction core.

Uses simulated OHLCV data to generate forecasts and sentiment analysis.
"""
from __future__ import annotations
import json
import random
import textwrap
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

_OLLAMA_HOST = "http://localhost:11434"


def _generate_mock_prices(ticker: str, days: int) -> list[dict]:
    """Generate deterministic mock historical price data for a ticker."""
    random.seed(sum(ord(c) for c in ticker))
    base_price = 150.0 if ticker != "BTC-USD" else 60000.0
    volatility = 0.02 if ticker != "BTC-USD" else 0.05
    
    data = []
    now = datetime.now(timezone.utc)
    current_price = base_price
    
    for i in range(days, -1, -1):
        date = now - timedelta(days=i)
        change = current_price * random.uniform(-volatility, volatility)
        current_price += change
        
        data.append({
            "date": date.isoformat()[:10],
            "price": round(current_price, 2),
            "volume": int(random.uniform(1e6, 1e7))
        })
    return data


def _call_ollama(prompt: str, model: str = "qwen3:6b", timeout: int = 120) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 4096},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{_OLLAMA_HOST}/api/generate",
            data=data, headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")).get("response", "").strip()
    except Exception:
        return ""


def _parse_json(text: str) -> dict:
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


def _fallback_forecast(ticker: str, prices: list[dict]) -> dict:
    """Rule-based forecast if LLM fails."""
    if not prices:
        return {}
    
    last_price = prices[-1]["price"]
    start_price = prices[0]["price"]
    trend = "Bullish" if last_price > start_price else "Bearish"
    
    return {
        "ticker": ticker,
        "current_price": last_price,
        "forecast": trend,
        "confidence": 0.65,
        "target_price": round(last_price * (1.05 if trend == "Bullish" else 0.95), 2),
        "catalysts": ["Historical momentum", "Simulated support/resistance"],
        "metadata": {
            "model": "fallback",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }


def forecast_asset(ticker: str, days: int = 30, model: str = "qwen3:6b") -> dict[str, Any]:
    prices = _generate_mock_prices(ticker, days)
    price_str = "\n".join([f"{p['date']}: ${p['price']} (Vol: {p['volume']})" for p in prices[-10:]])
    
    prompt = textwrap.dedent(f"""
        You are a quantitative financial analyst. Analyze the following price history for {ticker}.
        Provide a short-term forecast and sentiment analysis.
        
        Recent Price History:
        {price_str}

        Return ONLY a valid JSON object matching this schema:
        {{
          "ticker": "{ticker}",
          "current_price": <number>,
          "forecast": "Bullish, Bearish, or Neutral",
          "confidence": <number between 0.0 and 1.0>,
          "target_price": <number>,
          "catalysts": ["Reason 1", "Reason 2"]
        }}
    """).strip()

    response = _call_ollama(prompt, model=model)
    result = _parse_json(response)

    if not result or "forecast" not in result:
        return _fallback_forecast(ticker, prices)

    result["metadata"] = {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


def format_markdown(data: dict) -> str:
    lines = [
        f"# 📈 Market Forecast: {data.get('ticker', 'Unknown')}", "",
        f"**Current Price:** ${data.get('current_price', 0.0):,.2f}",
        f"**Forecast:** {data.get('forecast', 'Neutral')} (Confidence: {data.get('confidence', 0.0):.0%})",
        f"**Target Price:** ${data.get('target_price', 0.0):,.2f}", "",
        "## Key Catalysts", ""
    ]
    
    for cat in data.get("catalysts", []):
        lines.append(f"- {cat}")
        
    return "\n".join(lines)
