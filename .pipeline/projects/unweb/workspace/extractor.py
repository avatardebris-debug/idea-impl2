"""
extractor.py — LLM-powered entity and connection extractor.

Given article text, identifies:
  - People: name, role, organization, notable connections
  - Organizations: name, type, parent org, known funders, political lean
  - Connections: (entity_a, relationship, entity_b, evidence)

Output schema:
{
  "story_summary": str,
  "people":  [{"name": str, "role": str, "org": str, "connections": [str], "notes": str}],
  "orgs":    [{"name": str, "type": str, "parent": str, "funders": [str], "notes": str}],
  "connections": [{"from": str, "relation": str, "to": str, "evidence": str}],
  "red_flags": [str],   // notable conflicts of interest or unusual relationships
  "metadata": {...}
}
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
    """Rule-based fallback: extract capitalized names as entities."""
    # Find likely proper nouns (two or more capitalized words in sequence)
    names = list(dict.fromkeys(
        re.findall(r'\b[A-Z][a-z]+ (?:[A-Z][a-z]+ ?)+', text)
    ))[:20]

    people = [{"name": n.strip(), "role": "", "org": "", "connections": [], "notes": ""}
              for n in names if len(n.split()) <= 4][:10]
    orgs   = [{"name": n.strip(), "type": "organization", "parent": "", "funders": [], "notes": ""}
              for n in names if len(n.split()) >= 2 and n not in [p["name"] for p in people]][:5]

    return {
        "story_summary": text[:300].strip() + "...",
        "people":      people,
        "orgs":        orgs,
        "connections": [],
        "red_flags":   [],
        "metadata": {
            "model": "fallback",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "text_length": len(text),
        },
    }


def extract_connections(
    text: str,
    model: str = "qwen3:6b",
    source_url: str = "",
) -> dict[str, Any]:
    """Extract people, orgs, and connections from article text.

    Args:
        text:       Article plain text (from fetcher or direct input).
        model:      Ollama model.
        source_url: Original URL (for metadata).

    Returns:
        Connection graph dict matching the module schema.
    """
    prompt = textwrap.dedent(f"""
        You are an investigative journalist AI. Analyse this news article and extract
        all people, organizations, and connections between them.

        Focus on:
        - Who are the people? What are their roles and which organizations do they represent?
        - What organizations are involved? Who funds or controls them?
        - What are the relationships between these entities?
        - Are there any notable conflicts of interest, revolving-door relationships,
          or unusual funding arrangements?

        Return ONLY a valid JSON object with this exact schema:
        {{
          "story_summary": "2-sentence summary of the story",
          "people": [
            {{
              "name": "Full Name",
              "role": "their title or role in this story",
              "org": "their organization",
              "connections": ["connection 1", "connection 2"],
              "notes": "any notable background"
            }}
          ],
          "orgs": [
            {{
              "name": "Organization Name",
              "type": "government | corporation | ngo | think_tank | media | lobbying | other",
              "parent": "parent organization if applicable",
              "funders": ["known funder 1", "known funder 2"],
              "notes": "any notable background"
            }}
          ],
          "connections": [
            {{
              "from": "Entity A name",
              "relation": "funds | employs | lobbies | controls | advises | married_to | sits_on_board | donated_to | other",
              "to": "Entity B name",
              "evidence": "brief evidence or context from the article"
            }}
          ],
          "red_flags": [
            "Notable conflict of interest or unusual relationship #1",
            "..."
          ]
        }}

        ARTICLE TEXT:
        {text[:6000]}

        JSON:
    """).strip()

    response = _call_ollama(prompt, model=model)
    result   = _parse_json(response)

    if not result or "people" not in result:
        result = _fallback_extract(text)
    else:
        # Ensure all keys present
        result.setdefault("story_summary", "")
        result.setdefault("people",      [])
        result.setdefault("orgs",        [])
        result.setdefault("connections", [])
        result.setdefault("red_flags",   [])

    result["metadata"] = {
        "model":        model,
        "source_url":   source_url,
        "text_length":  len(text),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "n_people":     len(result.get("people", [])),
        "n_orgs":       len(result.get("orgs",   [])),
        "n_connections":len(result.get("connections", [])),
    }
    return result
