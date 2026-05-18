"""
builder.py — Core resume tailoring logic.
"""
from __future__ import annotations
import json
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


def _fallback_resume(profile: str, job_desc: str) -> dict:
    """Static fallback when LLM fails."""
    return {
        "name": "Candidate",
        "summary": "Experienced professional applying for this role.",
        "skills": ["General Skills"],
        "experience": [
            {"title": "Previous Role", "company": "Previous Company", "highlights": ["Relevant accomplishment 1"]}
        ],
        "cover_letter": "Dear Hiring Manager,\n\nI am writing to express my interest in this position.\n\nSincerely,\nCandidate",
        "metadata": {
            "model": "fallback",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }


def tailor_application(profile: str, job_desc: str, model: str = "qwen3:6b") -> dict[str, Any]:
    prompt = textwrap.dedent(f"""
        You are an expert career coach and resume writer.
        Given the candidate's profile and the target job description, rewrite the candidate's
        resume to highlight the most relevant skills and experience. Also, write a tailored cover letter.

        Return ONLY a valid JSON object matching this schema:
        {{
          "name": "Candidate Name",
          "summary": "A strong, tailored 2-sentence professional summary",
          "skills": ["Matched Skill 1", "Matched Skill 2"],
          "experience": [
            {{
              "title": "Job Title",
              "company": "Company Name",
              "highlights": ["Tailored bullet point 1", "Tailored bullet point 2"]
            }}
          ],
          "cover_letter": "Full text of the tailored cover letter (use \\n for newlines)"
        }}

        CANDIDATE PROFILE:
        {profile[:4000]}

        TARGET JOB DESCRIPTION:
        {job_desc[:4000]}
    """).strip()

    response = _call_ollama(prompt, model=model)
    result = _parse_json(response)

    if not result or "experience" not in result:
        return _fallback_resume(profile, job_desc)

    result["metadata"] = {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    return result


def format_markdown(data: dict) -> str:
    lines = [
        f"# {data.get('name', 'Candidate Name')}", "",
        "## Professional Summary", "",
        data.get("summary", ""), "",
        "## Skills", "",
        ", ".join(data.get("skills", [])), "",
        "## Experience", ""
    ]
    
    for exp in data.get("experience", []):
        lines.append(f"### {exp.get('title', 'Role')} at {exp.get('company', 'Company')}")
        for h in exp.get("highlights", []):
            lines.append(f"- {h}")
        lines.append("")
        
    lines.extend([
        "---", "",
        "# Cover Letter", "",
        data.get("cover_letter", "")
    ])
    
    return "\n".join(lines)
