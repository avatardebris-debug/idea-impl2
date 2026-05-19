"""
resume_job_applicant_cli.py
CLI front-end for the resume-to-job-applicant automator.

Combines drop_servicing_tool with fiverr/job scraping to:
  1. Parse a job listing (URL or paste)
  2. Load a candidate profile (JSON or interactive)
  3. Generate a tailored resume + cover letter via LLM
  4. Optionally submit / export

Usage:
    python resume_job_applicant_cli.py apply --job-url https://...  --profile profile.json
    python resume_job_applicant_cli.py apply --job-text job.txt     --profile profile.json
    python resume_job_applicant_cli.py batch  --jobs jobs.jsonl     --profile profile.json --out ./applications/
    python resume_job_applicant_cli.py init-profile
    python resume_job_applicant_cli.py preview --job-url https://...  --profile profile.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from typing import Any

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class CandidateProfile:
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    location: str = ""
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    experience: list[dict] = field(default_factory=list)   # [{title, company, dates, bullets}]
    education: list[dict] = field(default_factory=list)    # [{degree, school, year}]
    certifications: list[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: str | pathlib.Path) -> "CandidateProfile":
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        return cls(**data)

    def to_json(self, path: str | pathlib.Path) -> None:
        pathlib.Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")


@dataclass
class JobListing:
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    requirements: list[str] = field(default_factory=list)
    url: str = ""


# ---------------------------------------------------------------------------
# Job parser
# ---------------------------------------------------------------------------

def parse_job_url(url: str) -> JobListing:
    """Fetch a job posting URL and extract key fields (basic HTML strip)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise RuntimeError(f"Could not fetch job URL: {e}")

    import re
    # Strip tags
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return JobListing(url=url, description=text[:8000])


def parse_job_text(text_path: str) -> JobListing:
    content = pathlib.Path(text_path).read_text(encoding="utf-8")
    return JobListing(description=content)


# ---------------------------------------------------------------------------
# LLM call (Ollama or OpenAI)
# ---------------------------------------------------------------------------

def _llm_generate(system: str, prompt: str, provider: str = "ollama",
                  model: str = "qwen3:6b") -> str:
    """Call the configured LLM and return the text response."""
    if provider == "ollama":
        import json as _j, urllib.request as _u
        payload = _j.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            "stream": False,
        }).encode()
        req = _u.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with _u.urlopen(req, timeout=300) as resp:
            data = _j.loads(resp.read())
        return data.get("message", {}).get("content", "")

    elif provider == "openai":
        import os
        from openai import OpenAI  # type: ignore[import]
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""

    else:
        raise ValueError(f"Unknown provider '{provider}'")


# ---------------------------------------------------------------------------
# Document generators
# ---------------------------------------------------------------------------

_RESUME_SYSTEM = """You are an expert resume writer. Given a job description and
candidate profile, produce a tailored, ATS-optimised resume in Markdown format.
Mirror keywords from the job description. Be concise and achievement-oriented.
Output ONLY the resume Markdown, no preamble."""

_COVER_SYSTEM = """You are an expert cover letter writer. Given a job description
and candidate profile, produce a compelling, personalised cover letter in plain text.
3 paragraphs: hook, value proposition, call to action. Output ONLY the letter."""


def generate_resume(job: JobListing, profile: CandidateProfile,
                    provider: str, model: str) -> str:
    prompt = f"""
Job Title: {job.title or '(see description)'}
Company: {job.company or '(see description)'}

Job Description:
{job.description[:3000]}

Candidate Profile:
{json.dumps(asdict(profile), indent=2)[:3000]}

Generate a tailored resume in Markdown.
"""
    return _llm_generate(_RESUME_SYSTEM, prompt, provider, model)


def generate_cover_letter(job: JobListing, profile: CandidateProfile,
                          provider: str, model: str) -> str:
    prompt = f"""
Job Title: {job.title or '(see description)'}
Company: {job.company or '(see description)'}

Job Description:
{job.description[:2000]}

Candidate: {profile.name}
Summary: {profile.summary}
Top Skills: {', '.join(profile.skills[:10])}

Generate a tailored cover letter.
"""
    return _llm_generate(_COVER_SYSTEM, prompt, provider, model)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _cmd_init_profile(args: argparse.Namespace) -> None:
    """Interactively build a candidate profile JSON."""
    out = pathlib.Path(args.out or "profile.json")
    print("Building candidate profile (press Enter to skip fields)\n")
    profile = CandidateProfile(
        name=input("Full name: ").strip(),
        email=input("Email: ").strip(),
        phone=input("Phone: ").strip(),
        linkedin=input("LinkedIn URL: ").strip(),
        github=input("GitHub URL: ").strip(),
        location=input("Location (City, State): ").strip(),
        summary=input("Professional summary (1-2 sentences): ").strip(),
    )
    skills_raw = input("Top skills (comma-separated): ").strip()
    profile.skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

    n_jobs = int(input("Number of past jobs to add (0-5): ").strip() or "0")
    for i in range(n_jobs):
        print(f"\n  Job {i+1}:")
        profile.experience.append({
            "title": input("  Title: ").strip(),
            "company": input("  Company: ").strip(),
            "dates": input("  Dates (e.g. Jan 2021 – Mar 2023): ").strip(),
            "bullets": [b.strip() for b in
                        input("  Key achievements (semicolon-separated): ").split(";") if b.strip()],
        })

    profile.to_json(out)
    print(f"\n  ✓ Profile saved to {out}")


def _cmd_apply(args: argparse.Namespace) -> None:
    """Generate a tailored resume + cover letter for a single job."""
    profile = CandidateProfile.from_json(args.profile)

    if args.job_url:
        print(f"  Fetching job listing from {args.job_url}...")
        job = parse_job_url(args.job_url)
    elif args.job_text:
        job = parse_job_text(args.job_text)
    else:
        print("ERROR: provide --job-url or --job-text")
        sys.exit(1)

    out_dir = pathlib.Path(args.out or ".")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("  Generating resume...")
    resume_md = generate_resume(job, profile, args.provider, args.model)
    resume_path = out_dir / "resume.md"
    resume_path.write_text(resume_md, encoding="utf-8")

    print("  Generating cover letter...")
    cover_txt = generate_cover_letter(job, profile, args.provider, args.model)
    cover_path = out_dir / "cover_letter.txt"
    cover_path.write_text(cover_txt, encoding="utf-8")

    print(f"\n  ✓ Resume       → {resume_path}")
    print(f"  ✓ Cover letter → {cover_path}")


def _cmd_batch(args: argparse.Namespace) -> None:
    """Process multiple jobs from a JSONL file."""
    profile = CandidateProfile.from_json(args.profile)
    jobs_path = pathlib.Path(args.jobs)
    out_root = pathlib.Path(args.out or "./applications")
    out_root.mkdir(parents=True, exist_ok=True)

    lines = [l for l in jobs_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"  Processing {len(lines)} jobs from {jobs_path.name}...\n")

    for i, line in enumerate(lines, 1):
        try:
            spec = json.loads(line)
        except json.JSONDecodeError:
            print(f"  [{i}] Skipping invalid JSON line")
            continue

        slug = spec.get("slug") or f"job_{i:03d}"
        out_dir = out_root / slug
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"  [{i}/{len(lines)}] {slug}...")
        try:
            if "url" in spec:
                job = parse_job_url(spec["url"])
                job.title = spec.get("title", "")
                job.company = spec.get("company", "")
            elif "description" in spec:
                job = JobListing(
                    title=spec.get("title", ""),
                    company=spec.get("company", ""),
                    description=spec["description"],
                )
            else:
                print(f"    Skipping — no 'url' or 'description' in spec")
                continue

            resume_md = generate_resume(job, profile, args.provider, args.model)
            (out_dir / "resume.md").write_text(resume_md, encoding="utf-8")

            cover_txt = generate_cover_letter(job, profile, args.provider, args.model)
            (out_dir / "cover_letter.txt").write_text(cover_txt, encoding="utf-8")
            print(f"    ✓ Written to {out_dir}")

        except Exception as e:
            print(f"    ✗ Failed: {e}")

    print(f"\n  Batch complete → {out_root}")


def _cmd_preview(args: argparse.Namespace) -> None:
    """Preview job parsing without generating documents."""
    if args.job_url:
        job = parse_job_url(args.job_url)
    else:
        print("ERROR: --job-url required for preview")
        sys.exit(1)
    print(f"\n  Parsed job preview (first 800 chars):\n")
    print(job.description[:800])
    print(f"\n  Total description length: {len(job.description)} chars")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resume-to-Job-Applicant Automator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python resume_job_applicant_cli.py init-profile --out profile.json
              python resume_job_applicant_cli.py apply --job-url https://... --profile profile.json --out ./app/
              python resume_job_applicant_cli.py batch --jobs jobs.jsonl --profile profile.json --out ./apps/
              python resume_job_applicant_cli.py preview --job-url https://...
        """),
    )
    parser.add_argument("--provider", default="ollama",
                        choices=["ollama", "openai"], help="LLM provider")
    parser.add_argument("--model", default="qwen3:6b",
                        help="LLM model name")

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-profile", help="Interactively build a candidate profile JSON")
    p_init.add_argument("--out", default="profile.json", help="Output path (default: profile.json)")

    p_apply = sub.add_parser("apply", help="Generate resume + cover letter for one job")
    p_apply.add_argument("--job-url",  default=None)
    p_apply.add_argument("--job-text", default=None, help="Path to a text file with the job description")
    p_apply.add_argument("--profile",  required=True, help="Path to candidate profile JSON")
    p_apply.add_argument("--out",      default=".", help="Output directory")

    p_batch = sub.add_parser("batch", help="Process multiple jobs from a JSONL file")
    p_batch.add_argument("--jobs",    required=True, help="Path to jobs.jsonl")
    p_batch.add_argument("--profile", required=True)
    p_batch.add_argument("--out",     default="./applications")

    p_prev = sub.add_parser("preview", help="Preview parsed job listing")
    p_prev.add_argument("--job-url", required=True)

    args = parser.parse_args()
    {
        "init-profile": _cmd_init_profile,
        "apply":        _cmd_apply,
        "batch":        _cmd_batch,
        "preview":      _cmd_preview,
    }[args.command](args)


if __name__ == "__main__":
    main()
