"""
scanner.py — Core compliance scanning engine.
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


def _fallback_checklist(company_name: str, description: str) -> dict:
    """Static fallback checklist when LLM is unavailable."""
    return {
        "company_name": company_name,
        "summary": "Fallback standard compliance checklist.",
        "frameworks": ["SOC2", "GDPR"],
        "checklist": [
            {"category": "Access Control", "task": "Enforce MFA for all employee accounts", "framework": "SOC2/GDPR", "priority": "High", "effort": "Low"},
            {"category": "Data Encryption", "task": "Encrypt databases at rest (AES-256)", "framework": "SOC2/GDPR", "priority": "High", "effort": "Medium"},
            {"category": "Privacy", "task": "Publish a GDPR-compliant Privacy Policy", "framework": "GDPR", "priority": "High", "effort": "Low"},
            {"category": "Monitoring", "task": "Enable AWS CloudTrail or equivalent logging", "framework": "SOC2", "priority": "Medium", "effort": "Low"},
        ],
        "metadata": {
            "model": "fallback",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    }


def generate_checklist(company_name: str, description: str, model: str = "qwen3:6b") -> dict[str, Any]:
    prompt = textwrap.dedent(f"""
        You are a seasoned compliance expert (SOC2 and GDPR).
        Generate a highly specific, actionable compliance checklist for the following startup.

        Company Name: {company_name}
        Description: {description}

        Return ONLY a valid JSON object with this schema:
        {{
          "company_name": "{company_name}",
          "summary": "2-sentence summary of their primary compliance risks",
          "frameworks": ["SOC2", "GDPR"],
          "checklist": [
            {{
              "category": "e.g. Access Control, Data Privacy, CI/CD",
              "task": "specific actionable task",
              "framework": "SOC2, GDPR, or Both",
              "priority": "High, Medium, or Low",
              "effort": "Low, Medium, or High"
            }}
          ]
        }}
    """).strip()

    response = _call_ollama(prompt, model=model)
    result = _parse_json(response)

    if not result or "checklist" not in result:
        return _fallback_checklist(company_name, description)

    result["metadata"] = {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


def format_markdown(data: dict) -> str:
    lines = [
        f"# 🛡️ Compliance Checklist: {data.get('company_name', 'Startup')}", "",
        f"> **Generated:** {data.get('metadata', {}).get('generated_at', '')[:10]}",
        f"> **Frameworks:** {', '.join(data.get('frameworks', []))}", "",
        "## Summary", "", data.get("summary", ""), "",
        "## Checklist", ""
    ]

    by_cat = {}
    for item in data.get("checklist", []):
        by_cat.setdefault(item.get("category", "General"), []).append(item)

    for cat, items in by_cat.items():
        lines.extend([f"### {cat}", ""])
        for item in items:
            task = item.get('task', '')
            fw = item.get('framework', '')
            pri = item.get('priority', '')
            eff = item.get('effort', '')
            lines.append(f"- [ ] **{task}** *(Framework: {fw} | Priority: {pri} | Effort: {eff})*")
        lines.append("")

    return "\n".join(lines)
