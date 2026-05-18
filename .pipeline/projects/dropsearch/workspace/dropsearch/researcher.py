"""
researcher.py — Core dropship market analysis engine.
"""
from __future__ import annotations
import json
import random
import textwrap
import urllib.request
from datetime import datetime, timezone
from typing import Any

_OLLAMA_HOST = "http://localhost:11434"

def _mock_competitor_data(niche: str) -> list[dict]:
    """Generate offline mocked competitor data based on the niche."""
    random.seed(sum(ord(c) for c in niche))
    
    competitors = []
    for i in range(1, random.randint(3, 5) + 1):
        competitors.append({
            "name": f"Competitor {i} - {niche.split()[0]} Co.",
            "estimated_price": round(random.uniform(20.0, 150.0), 2),
            "ad_strategy": random.choice(["Facebook Video Ads", "TikTok Influencers", "Google Search Intent", "Instagram Carousel"]),
            "weakness": random.choice(["Slow shipping", "Poor website design", "No email marketing flow", "Low quality product images"])
        })
    return competitors


def _call_ollama(prompt: str, model: str = "qwen3:6b", timeout: int = 180) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.4, "num_ctx": 4096},
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


def _fallback_plan(niche: str, competitors: list[dict]) -> dict:
    return {
        "niche": niche,
        "competitor_summary": "Simulated competitors found.",
        "marketing_angle": "Focus on the weaknesses of competitors.",
        "target_audience": "General online buyers interested in this niche.",
        "pricing_strategy": "Match competitor averages but offer bundles.",
        "operational_gameplan": "1. Source product. 2. Build Shopify store. 3. Launch ads.",
        "metadata": {"model": "fallback", "generated_at": datetime.now(timezone.utc).isoformat()}
    }


def analyze_niche(niche: str, model: str = "qwen3:6b") -> dict[str, Any]:
    competitors = _mock_competitor_data(niche)
    
    comp_text = json.dumps(competitors, indent=2)
    
    prompt = textwrap.dedent(f"""
        You are an elite e-commerce and dropshipping strategist.
        Analyze the following niche and competitor data. Create a comprehensive
        business gameplan in full English describing the entire operation.

        Return ONLY a valid JSON object matching this schema:
        {{
          "niche": "{niche}",
          "competitor_summary": "1-2 sentences summarizing the competition",
          "marketing_angle": "The unique angle or hook to use in ads",
          "target_audience": "Who to target (demographics/interests)",
          "pricing_strategy": "How to price the product competitively",
          "operational_gameplan": "Step by step execution plan"
        }}

        NICHE: {niche}
        COMPETITORS: {comp_text}
    """).strip()

    response = _call_ollama(prompt, model=model)
    result = _parse_json(response)

    if not result or "operational_gameplan" not in result:
        return _fallback_plan(niche, competitors)

    result["metadata"] = {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


def format_markdown(data: dict) -> str:
    return textwrap.dedent(f"""
        # 🕵️ DropSearch Gameplan: {data.get('niche', 'Unknown')}
        
        ## Competitor Summary
        {data.get('competitor_summary', '')}
        
        ## Target Audience
        {data.get('target_audience', '')}
        
        ## Marketing Angle
        {data.get('marketing_angle', '')}
        
        ## Pricing Strategy
        {data.get('pricing_strategy', '')}
        
        ## Operational Gameplan
        {data.get('operational_gameplan', '')}
        
        ---
        *Generated at: {data.get('metadata', {}).get('generated_at', '')[:10]}*
    """).strip()
