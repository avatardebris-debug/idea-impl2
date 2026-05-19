"""
orchestrator.py — Resume-to-Job-Applicant batch automation.

Given a resume profile and a list of job postings (from file, stdin, or a
simple URL list), it:
  1. Scores each job for fit using rule-based keyword matching
  2. Generates a tailored resume + cover letter via the LLM for each match
  3. Saves each application as a structured JSON + Markdown file
  4. Produces a run summary report

No web scraping is performed here — callers supply pre-fetched job dicts.
For live scraping, use the companion `job_fetcher.py` module.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .builder import format_markdown, tailor_application


# ---------------------------------------------------------------------------
# Job scoring (rule-based, no LLM required)
# ---------------------------------------------------------------------------

_STOP_WORDS = {
    "the", "and", "for", "with", "this", "that", "are", "was",
    "you", "will", "our", "your", "have", "from", "not", "all",
}


def _tokenize(text: str) -> set[str]:
    """Lowercase word tokens, strip punctuation, remove stop words."""
    tokens = re.findall(r"[a-z][a-z0-9+#]*", text.lower())
    return {t for t in tokens if t not in _STOP_WORDS and len(t) > 2}


def score_job(profile: str, job: dict[str, Any]) -> dict[str, Any]:
    """Score a job posting against the candidate profile.

    Returns a scoring dict with fields:
      - score (float 0-1)
      - matched_keywords (list)
      - missing_keywords (list)
      - recommendation (str)
    """
    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}"
    profile_tokens = _tokenize(profile)
    job_tokens = _tokenize(job_text)

    matched = sorted(profile_tokens & job_tokens)
    missing = sorted(job_tokens - profile_tokens)

    # Weight: matched / total unique in job posting
    score = len(matched) / max(len(job_tokens), 1)

    if score >= 0.35:
        rec = "strong_match"
    elif score >= 0.20:
        rec = "possible_match"
    else:
        rec = "weak_match"

    return {
        "score": round(score, 4),
        "matched_keywords": matched[:30],
        "missing_keywords": missing[:20],
        "recommendation": rec,
    }


# ---------------------------------------------------------------------------
# Application generator
# ---------------------------------------------------------------------------

def generate_application(
    profile: str,
    job: dict[str, Any],
    model: str = "qwen3:6b",
) -> dict[str, Any]:
    """Generate a full tailored application for a single job posting.

    Returns a dict with:
      - job_title, company, url
      - scoring (from score_job)
      - resume_data (from tailor_application)
      - markdown (rendered Markdown string)
      - generated_at (ISO timestamp)
    """
    job_desc = (
        f"Position: {job.get('title', 'Unknown')}\n"
        f"Company: {job.get('company', 'Unknown')}\n"
        f"Location: {job.get('location', 'Not specified')}\n\n"
        f"{job.get('description', '')}\n\n"
        f"Requirements:\n{job.get('requirements', '')}"
    )

    scoring = score_job(profile, job)
    resume_data = tailor_application(profile, job_desc, model=model)
    markdown = format_markdown(resume_data)

    return {
        "job_title": job.get("title", "Unknown"),
        "company": job.get("company", "Unknown"),
        "url": job.get("url", ""),
        "scoring": scoring,
        "resume_data": resume_data,
        "markdown": markdown,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Batch orchestrator
# ---------------------------------------------------------------------------

def run_batch(
    profile: str,
    jobs: list[dict[str, Any]],
    output_dir: Path,
    model: str = "qwen3:6b",
    min_score: float = 0.20,
    max_applications: int = 50,
) -> dict[str, Any]:
    """Run the full resume-to-applicant pipeline for a list of jobs.

    Args:
        profile:          Candidate profile text (resume, LinkedIn bio, etc.)
        jobs:             List of job dicts with keys: title, company, description,
                          requirements, url, location
        output_dir:       Directory to write application files into
        model:            Ollama model name
        min_score:        Minimum fit score to generate an application (0-1)
        max_applications: Hard cap on number of applications generated

    Returns:
        Summary dict with counts, skipped, and output_dir path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "total_jobs": len(jobs),
        "generated": 0,
        "skipped_low_score": 0,
        "skipped_cap": 0,
        "errors": [],
        "applications": [],
        "output_dir": str(output_dir),
        "run_at": datetime.now(timezone.utc).isoformat(),
    }

    for i, job in enumerate(jobs):
        if summary["generated"] >= max_applications:
            summary["skipped_cap"] += len(jobs) - i
            break

        # Pre-screen
        scoring = score_job(profile, job)
        if scoring["score"] < min_score:
            summary["skipped_low_score"] += 1
            continue

        try:
            app = generate_application(profile, job, model=model)
        except Exception as exc:
            summary["errors"].append({
                "job": job.get("title", f"job_{i}"),
                "company": job.get("company", ""),
                "error": str(exc),
            })
            continue

        # Write JSON
        slug = _slugify(f"{job.get('company', 'co')}_{job.get('title', 'role')}")
        json_path = output_dir / f"{slug}.json"
        md_path = output_dir / f"{slug}.md"

        json_path.write_text(
            json.dumps(app, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        md_path.write_text(app["markdown"], encoding="utf-8")

        summary["generated"] += 1
        summary["applications"].append({
            "slug": slug,
            "title": app["job_title"],
            "company": app["company"],
            "score": scoring["score"],
            "recommendation": scoring["recommendation"],
            "json_file": str(json_path),
            "md_file": str(md_path),
        })

    # Write master summary
    summary_path = output_dir / "_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:max_len]


def load_jobs_from_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load job postings from a JSONL file (one JSON object per line)."""
    jobs = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                jobs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return jobs


def load_jobs_from_json(path: Path) -> list[dict[str, Any]]:
    """Load job postings from a JSON array file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "jobs" in data:
        return data["jobs"]
    raise ValueError(f"Expected a JSON array or {{jobs: [...]}} object in {path}")
