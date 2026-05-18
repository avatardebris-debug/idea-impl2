"""
analyzer.py — LLM-powered schema discovery and data extraction from PDF text.

Two modes:
  1. --discover: Infer what kind of document this is and what fields it contains
  2. --schema NAME: Extract fields for a known schema type (invoice, contract, form, report, etc.)

Built-in schema templates:
  invoice   → invoice_number, date, vendor, buyer, line_items[], total, tax, due_date
  contract  → parties[], effective_date, termination_date, jurisdiction, key_clauses[]
  resume    → name, email, phone, skills[], experience[], education[]
  medical   → patient, dob, diagnosis[], medications[], provider, date
  report    → title, author, date, sections[], key_findings[], recommendations[]
"""
from __future__ import annotations
import json
import re
import textwrap
import urllib.request
from datetime import datetime, timezone
from typing import Any

_OLLAMA_HOST = "http://localhost:11434"

_SCHEMA_TEMPLATES: dict[str, dict] = {
    "invoice": {
        "invoice_number": "string",
        "date":           "string (YYYY-MM-DD)",
        "vendor":         "string",
        "buyer":          "string",
        "line_items":     "array of {description, quantity, unit_price, total}",
        "subtotal":       "number",
        "tax":            "number",
        "total":          "number",
        "due_date":       "string (YYYY-MM-DD)",
        "payment_terms":  "string",
    },
    "contract": {
        "parties":          "array of {name, role}",
        "effective_date":   "string (YYYY-MM-DD)",
        "termination_date": "string (YYYY-MM-DD)",
        "jurisdiction":     "string",
        "governing_law":    "string",
        "key_obligations":  "array of strings",
        "key_clauses":      "array of {clause_title, summary}",
    },
    "resume": {
        "name":         "string",
        "email":        "string",
        "phone":        "string",
        "summary":      "string",
        "skills":       "array of strings",
        "experience":   "array of {company, title, start_date, end_date, description}",
        "education":    "array of {institution, degree, field, year}",
        "certifications": "array of strings",
    },
    "medical": {
        "patient_name": "string",
        "dob":          "string (YYYY-MM-DD)",
        "provider":     "string",
        "date":         "string (YYYY-MM-DD)",
        "chief_complaint": "string",
        "diagnosis":    "array of strings",
        "medications":  "array of {name, dose, frequency}",
        "notes":        "string",
    },
    "report": {
        "title":           "string",
        "author":          "string or array",
        "date":            "string",
        "executive_summary": "string",
        "sections":        "array of {title, content_summary}",
        "key_findings":    "array of strings",
        "recommendations": "array of strings",
        "conclusion":      "string",
    },
}


def _call_ollama(prompt: str, model: str = "qwen3:6b", timeout: int = 180) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.05, "num_ctx": 16384},
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


def _parse_json(text: str) -> Any:
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    # Try array
    start = text.find("[")
    end   = text.rfind("]") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def discover_schema(text: str, model: str = "qwen3:6b") -> dict[str, Any]:
    """Infer the document type and list all discoverable fields."""
    prompt = textwrap.dedent(f"""
        Analyse this document text and determine:
        1. What type of document is this? (invoice, contract, resume, medical record, report, form, other)
        2. What are all the named fields / sections / data points it contains?
        3. What is the value of each field?

        Return ONLY valid JSON:
        {{
          "document_type": "...",
          "confidence":    0.0-1.0,
          "fields":        {{"field_name": "value or null", ...}},
          "tables":        [{{"name": "table name", "headers": [...], "rows": [[...]]}}],
          "summary":       "1-2 sentence summary"
        }}

        DOCUMENT TEXT (first 8000 chars):
        {text[:8000]}

        JSON:
    """).strip()

    response = _call_ollama(prompt, model=model)
    result   = _parse_json(response)

    if not isinstance(result, dict):
        # Fallback: regex field discovery
        fields = {}
        for m in re.finditer(r"([A-Z][A-Za-z\s]{2,30}):\s*([^\n]{1,100})", text):
            key = m.group(1).strip().lower().replace(" ", "_")
            fields[key] = m.group(2).strip()
        result = {
            "document_type": "unknown",
            "confidence": 0.3,
            "fields": dict(list(fields.items())[:30]),
            "tables": [],
            "summary": text[:200].strip() + "...",
        }

    result.setdefault("document_type", "unknown")
    result.setdefault("confidence", 0.0)
    result.setdefault("fields", {})
    result.setdefault("tables", [])
    result.setdefault("summary", "")
    result["metadata"] = {
        "model": model,
        "text_length": len(text),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


def extract_schema(text: str, schema_name: str, model: str = "qwen3:6b") -> dict[str, Any]:
    """Extract fields for a known schema type from document text."""
    template = _SCHEMA_TEMPLATES.get(schema_name.lower())
    if template is None:
        available = ", ".join(_SCHEMA_TEMPLATES.keys())
        raise ValueError(
            f"Unknown schema '{schema_name}'. Available: {available}. "
            "Use --discover to auto-detect."
        )

    fields_desc = "\n".join(f'  "{k}": {v}' for k, v in template.items())

    prompt = textwrap.dedent(f"""
        Extract all fields from this {schema_name} document.
        Return ONLY a valid JSON object with these exact keys (use null for missing fields):

        {{
        {fields_desc}
        }}

        Also add:
          "_validation": {{
            "missing_required": [...],  // list of key fields that are null or empty
            "completeness_pct": 0-100,  // percentage of fields found
            "warnings": [...]
          }}

        DOCUMENT TEXT (first 8000 chars):
        {text[:8000]}

        JSON:
    """).strip()

    response = _call_ollama(prompt, model=model)
    result   = _parse_json(response)

    if not isinstance(result, dict):
        # Fallback: return null for all fields
        result = {k: None for k in template}
        result["_validation"] = {
            "missing_required": list(template.keys()),
            "completeness_pct": 0,
            "warnings": ["LLM extraction failed — fallback mode"],
        }
    else:
        # Ensure all template keys present
        for k in template:
            result.setdefault(k, None)
        result.setdefault("_validation", {
            "missing_required": [k for k in template if result.get(k) is None],
            "completeness_pct": round(
                100 * sum(1 for k in template if result.get(k) is not None) / len(template)
            ),
            "warnings": [],
        })

    result["_schema"]  = schema_name
    result["metadata"] = {
        "model": model,
        "text_length": len(text),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


def list_schemas() -> list[str]:
    return list(_SCHEMA_TEMPLATES.keys())
