"""
extractor.py — Core contract clause extraction logic.
"""
from __future__ import annotations
import json
import re
import textwrap
import urllib.request
from datetime import datetime, timezone
from typing import Any

_OLLAMA_HOST = "http://localhost:11434"


def _call_ollama(prompt: str, model: str = "qwen3:6b", timeout: int = 180) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 16384},
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


def _fallback_extract(text: str) -> dict:
    """Regex-based fallback extraction."""
    clauses = []
    
    # Simple keyword heuristics
    if "terminat" in text.lower():
        clauses.append({"type": "Termination", "text": "Termination clause found but full context requires LLM.", "risk": "Medium"})
    if "confidential" in text.lower() or "nda" in text.lower():
        clauses.append({"type": "Confidentiality", "text": "Confidentiality/NDA terms detected.", "risk": "Low"})
    if "liab" in text.lower():
        clauses.append({"type": "Liability", "text": "Limitation of liability mentioned.", "risk": "High"})

    return {
        "title": "Contract (Fallback Analysis)",
        "clauses": clauses,
        "metadata": {
            "model": "fallback",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }


def extract_clauses(text: str, model: str = "qwen3:6b") -> dict[str, Any]:
    prompt = textwrap.dedent(f"""
        You are a legal AI assistant. Read the following contract text and extract key clauses.
        Focus on: Termination, Liability, Confidentiality, Governing Law, and Payment Terms.

        Return ONLY a valid JSON object matching this schema:
        {{
          "title": "Document Title or 'Untitled Contract'",
          "clauses": [
            {{
              "type": "Clause Type (e.g. Termination)",
              "text": "Direct quote or 1-sentence summary of the clause",
              "risk": "High/Medium/Low based on standard legal risk"
            }}
          ]
        }}

        CONTRACT TEXT:
        {text[:16000]}
    """).strip()

    response = _call_ollama(prompt, model=model)
    result = _parse_json(response)

    if not result or "clauses" not in result:
        return _fallback_extract(text)

    result["metadata"] = {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


def format_markdown(data: dict) -> str:
    lines = [
        f"# 📜 Contract Analysis: {data.get('title', 'Untitled')}", "",
        f"> **Generated:** {data.get('metadata', {}).get('generated_at', '')[:10]}", "",
        "## Key Clauses", ""
    ]
    
    for c in data.get("clauses", []):
        risk = c.get("risk", "Low").lower()
        icon = "🔴" if risk == "high" else "🟡" if risk == "medium" else "🟢"
        lines.append(f"### {icon} {c.get('type', 'Clause')}")
        lines.append(f"**Risk Level:** {risk.title()}")
        lines.append(f"> {c.get('text', '')}")
        lines.append("")
        
    return "\n".join(lines)
