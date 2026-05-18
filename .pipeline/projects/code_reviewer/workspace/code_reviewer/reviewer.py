"""
reviewer.py — Core diff analysis engine.
"""
from __future__ import annotations
import json
import re
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


def _fallback_review(diff_text: str) -> dict:
    """Regex-based fallback diff analysis."""
    files_changed = []
    for m in re.finditer(r"^diff --git a/(.*?) b/(.*?)$", diff_text, re.MULTILINE):
        files_changed.append(m.group(2))
    
    return {
        "summary": "Fallback local analysis. LLM offline.",
        "files": [{"filename": f, "changes": "Modified file"} for f in list(set(files_changed))],
        "issues": [{"severity": "info", "description": "Unable to perform deep analysis without LLM."}],
        "metadata": {
            "model": "fallback",
            "diff_length": len(diff_text),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }


def analyze_diff(diff_text: str, model: str = "qwen3:6b") -> dict[str, Any]:
    prompt = textwrap.dedent(f"""
        You are an expert senior software engineer performing a code review.
        Analyze the following git diff. Summarize the changes by file, 
        and flag any potential bugs, security issues, or performance regressions.

        Return ONLY a valid JSON object matching this schema:
        {{
          "summary": "1-2 sentence high-level summary of the entire patch",
          "files": [
            {{"filename": "path/to/file", "changes": "Summary of what changed in this file"}}
          ],
          "issues": [
            {{"severity": "high/medium/low", "description": "Description of the potential issue"}}
          ]
        }}

        DIFF CONTENT:
        {diff_text[:16000]}
    """).strip()

    response = _call_ollama(prompt, model=model)
    result = _parse_json(response)

    if not result or "files" not in result:
        return _fallback_review(diff_text)

    result["metadata"] = {
        "model": model,
        "diff_length": len(diff_text),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


def format_markdown(data: dict) -> str:
    lines = [
        "# 🔎 Code Review Summary", "",
        f"> **Generated:** {data.get('metadata', {}).get('generated_at', '')[:10]}", "",
        "## Overview", "", data.get("summary", ""), "",
        "## Files Changed", ""
    ]
    
    for f in data.get("files", []):
        lines.append(f"- **{f.get('filename', 'Unknown')}**: {f.get('changes', '')}")
    lines.append("")

    issues = data.get("issues", [])
    if issues:
        lines.extend(["## Potential Issues", ""])
        for issue in issues:
            sev = issue.get("severity", "low").lower()
            icon = "🔴" if sev == "high" else "🟡" if sev == "medium" else "🔵"
            lines.append(f"- {icon} **{sev.upper()}**: {issue.get('description', '')}")
    else:
        lines.extend(["## Potential Issues", "", "✅ No obvious issues detected."])
        
    return "\n".join(lines)
