"""
analyzer.py — SaaS pricing analysis engine.
"""
from __future__ import annotations
import json
import textwrap
import urllib.request
from datetime import datetime, timezone
from typing import Any

_OLLAMA_HOST = "http://localhost:11434"


def _call_ollama(prompt: str, model: str = "qwen3:6b", timeout: int = 120) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 8192},
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


def _fallback_pricing(name: str, desc: str) -> dict:
    """Static fallback pricing tiers when LLM is unavailable."""
    return {
        "product_name": name,
        "summary": "Standard 3-tier SaaS pricing model.",
        "tiers": [
            {"name": "Starter", "price": "$15/mo", "target_audience": "Individuals", "features": ["Core feature 1", "Basic support"]},
            {"name": "Pro", "price": "$49/mo", "target_audience": "Small Teams", "features": ["Everything in Starter", "Advanced analytics", "Priority support"]},
            {"name": "Enterprise", "price": "Custom", "target_audience": "Large Orgs", "features": ["Everything in Pro", "SSO & Compliance", "Dedicated account manager"]},
        ],
        "psychological_hooks": ["Decoy pricing effect between Starter and Pro"],
        "metadata": {
            "model": "fallback",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    }


def analyze_pricing(name: str, description: str, competitors: str = "", model: str = "qwen3:6b") -> dict[str, Any]:
    prompt = textwrap.dedent(f"""
        You are a SaaS Pricing Strategy Expert. Analyze the following product and recommend
        an optimal pricing structure based on value metrics and psychological pricing principles.

        Product: {name}
        Description: {description}
        Known Competitors: {competitors or 'None specified'}

        Return ONLY a valid JSON object with this exact schema:
        {{
          "product_name": "{name}",
          "summary": "2-sentence rationale for this pricing model",
          "value_metric": "What they should charge by (e.g. per user, per API call, flat monthly)",
          "tiers": [
            {{
              "name": "Tier Name (e.g. Free, Pro, Business)",
              "price": "Suggested Price (e.g. $29/mo)",
              "target_audience": "Who this is for",
              "features": ["Key feature 1", "Key feature 2"]
            }}
          ],
          "psychological_hooks": [
            "Actionable psychological pricing tip 1 (e.g. use of 9, decoy effect)"
          ]
        }}
    """).strip()

    response = _call_ollama(prompt, model=model)
    result = _parse_json(response)

    if not result or "tiers" not in result:
        return _fallback_pricing(name, description)

    result["metadata"] = {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


def format_markdown(data: dict) -> str:
    lines = [
        f"# 🏷️ SaaS Pricing Strategy: {data.get('product_name', 'Product')}", "",
        f"> **Value Metric:** {data.get('value_metric', 'Monthly Subscription')}", "",
        "## Summary", "", data.get("summary", ""), "",
        "## Pricing Tiers", ""
    ]

    for t in data.get("tiers", []):
        lines.append(f"### {t.get('name', 'Tier')} — {t.get('price', '$0')}")
        lines.append(f"**Target:** {t.get('target_audience', 'Everyone')}\n")
        for f in t.get("features", []):
            lines.append(f"- {f}")
        lines.append("")

    lines.extend(["## Pricing Psychology & Hooks", ""])
    for h in data.get("psychological_hooks", []):
        lines.append(f"- 🧠 {h}")

    return "\n".join(lines)
