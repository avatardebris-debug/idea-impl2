"""Tests for resume_builder.orchestrator — batch job application pipeline."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from resume_builder.orchestrator import (
    _slugify,
    _tokenize,
    generate_application,
    load_jobs_from_json,
    load_jobs_from_jsonl,
    run_batch,
    score_job,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

PROFILE = """
Alice Johnson — Senior Software Engineer
Email: alice@example.com | Phone: 555-1234

Skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes, REST APIs, CI/CD, AWS

Experience:
  Senior Engineer, Acme Corp (2020–Present)
    - Led API redesign reducing latency by 40%
    - Built CI/CD pipelines with GitHub Actions and Docker

  Engineer, Beta Ltd (2017–2020)
    - Built Python microservices for e-commerce platform

Education: B.S. Computer Science, State University, 2017
"""

JOB_PYTHON_ENGINEER = {
    "title": "Python Backend Engineer",
    "company": "TechCorp",
    "location": "Remote",
    "url": "https://jobs.example.com/123",
    "description": "We are looking for a Python engineer to build REST APIs.",
    "requirements": "3+ years Python, FastAPI or Flask, PostgreSQL, Docker",
}

JOB_MARKETING = {
    "title": "Marketing Manager",
    "company": "BrandCo",
    "location": "New York",
    "url": "https://jobs.example.com/456",
    "description": "Drive brand awareness campaigns across social media.",
    "requirements": "5 years marketing experience, SEO, SEM, content strategy",
}

JOB_DEVOPS = {
    "title": "DevOps Engineer",
    "company": "CloudCo",
    "location": "Remote",
    "url": "https://jobs.example.com/789",
    "description": "Manage Kubernetes clusters and CI/CD pipelines on AWS.",
    "requirements": "Kubernetes, Docker, AWS, CI/CD, Python scripting",
}


# ---------------------------------------------------------------------------
# _tokenize
# ---------------------------------------------------------------------------

class TestTokenize:
    def test_lowercases_tokens(self):
        tokens = _tokenize("Python Django FastAPI")
        assert "python" in tokens
        assert "django" in tokens

    def test_removes_stop_words(self):
        tokens = _tokenize("the and for with this")
        assert len(tokens) == 0

    def test_strips_punctuation(self):
        tokens = _tokenize("python, django. flask!")
        assert "python" in tokens
        assert "django" in tokens
        assert "flask" in tokens

    def test_filters_short_tokens(self):
        """Tokens <= 2 chars should be excluded."""
        tokens = _tokenize("AI ML DL is a ok")
        # "is", "a", "ok" should all be excluded
        assert "is" not in tokens
        assert "a" not in tokens
        assert "ok" not in tokens

    def test_returns_set(self):
        result = _tokenize("python python python")
        assert isinstance(result, set)
        assert len(result) == 1

    def test_empty_string(self):
        assert _tokenize("") == set()


# ---------------------------------------------------------------------------
# score_job
# ---------------------------------------------------------------------------

class TestScoreJob:
    def test_returns_dict_with_required_keys(self):
        result = score_job(PROFILE, JOB_PYTHON_ENGINEER)
        for key in ("score", "matched_keywords", "missing_keywords", "recommendation"):
            assert key in result

    def test_score_is_float_between_0_and_1(self):
        result = score_job(PROFILE, JOB_PYTHON_ENGINEER)
        assert 0.0 <= result["score"] <= 1.0

    def test_relevant_job_scores_higher_than_irrelevant(self):
        tech_score = score_job(PROFILE, JOB_PYTHON_ENGINEER)["score"]
        marketing_score = score_job(PROFILE, JOB_MARKETING)["score"]
        assert tech_score > marketing_score

    def test_strong_match_recommendation_for_good_fit(self):
        result = score_job(PROFILE, JOB_PYTHON_ENGINEER)
        assert result["recommendation"] in ("strong_match", "possible_match")

    def test_weak_match_for_unrelated_job(self):
        result = score_job(PROFILE, JOB_MARKETING)
        assert result["recommendation"] == "weak_match"

    def test_matched_keywords_subset_of_profile(self):
        result = score_job(PROFILE, JOB_PYTHON_ENGINEER)
        profile_tokens = _tokenize(PROFILE)
        for kw in result["matched_keywords"]:
            assert kw in profile_tokens

    def test_matched_keywords_capped_at_30(self):
        result = score_job(PROFILE, JOB_PYTHON_ENGINEER)
        assert len(result["matched_keywords"]) <= 30

    def test_missing_keywords_capped_at_20(self):
        result = score_job(PROFILE, JOB_MARKETING)
        assert len(result["missing_keywords"]) <= 20

    def test_empty_job_gives_zero_score(self):
        result = score_job(PROFILE, {})
        assert result["score"] == 0.0

    def test_score_is_rounded_to_4_decimals(self):
        result = score_job(PROFILE, JOB_PYTHON_ENGINEER)
        assert result["score"] == round(result["score"], 4)


# ---------------------------------------------------------------------------
# _slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert _slugify("TechCorp_Python Engineer") == "techcorp_python_engineer"

    def test_strips_leading_trailing_underscores(self):
        slug = _slugify("  hello  ")
        assert not slug.startswith("_")
        assert not slug.endswith("_")

    def test_max_length(self):
        long = "a" * 200
        assert len(_slugify(long)) <= 60

    def test_special_chars_replaced(self):
        slug = _slugify("Hello & World!")
        assert "&" not in slug
        assert "!" not in slug


# ---------------------------------------------------------------------------
# load_jobs_from_jsonl / load_jobs_from_json
# ---------------------------------------------------------------------------

class TestLoadJobs:
    def test_load_jsonl(self, tmp_path):
        f = tmp_path / "jobs.jsonl"
        f.write_text(
            json.dumps(JOB_PYTHON_ENGINEER) + "\n" +
            json.dumps(JOB_DEVOPS) + "\n",
            encoding="utf-8"
        )
        jobs = load_jobs_from_jsonl(f)
        assert len(jobs) == 2
        assert jobs[0]["title"] == "Python Backend Engineer"

    def test_load_jsonl_skips_blank_lines(self, tmp_path):
        f = tmp_path / "jobs.jsonl"
        f.write_text(
            json.dumps(JOB_PYTHON_ENGINEER) + "\n\n" +
            json.dumps(JOB_DEVOPS) + "\n",
            encoding="utf-8"
        )
        jobs = load_jobs_from_jsonl(f)
        assert len(jobs) == 2

    def test_load_json_array(self, tmp_path):
        f = tmp_path / "jobs.json"
        f.write_text(json.dumps([JOB_PYTHON_ENGINEER, JOB_DEVOPS]), encoding="utf-8")
        jobs = load_jobs_from_json(f)
        assert len(jobs) == 2

    def test_load_json_wrapped_object(self, tmp_path):
        f = tmp_path / "jobs.json"
        f.write_text(json.dumps({"jobs": [JOB_PYTHON_ENGINEER]}), encoding="utf-8")
        jobs = load_jobs_from_json(f)
        assert len(jobs) == 1

    def test_load_json_raises_on_bad_format(self, tmp_path):
        f = tmp_path / "jobs.json"
        f.write_text(json.dumps({"other": "data"}), encoding="utf-8")
        with pytest.raises(ValueError):
            load_jobs_from_json(f)


# ---------------------------------------------------------------------------
# generate_application
# ---------------------------------------------------------------------------

class TestGenerateApplication:
    def _mock_tailor(self, *args, **kwargs):
        return {
            "name": "Alice Johnson",
            "summary": "Experienced Python engineer.",
            "skills": ["Python", "FastAPI"],
            "experience": [{"title": "Senior Engineer", "company": "Acme", "highlights": ["Built APIs"]}],
            "cover_letter": "Dear Hiring Manager,\n\nI am excited to apply.\n\nSincerely,\nAlice",
            "metadata": {"model": "mock", "generated_at": "2024-01-01T00:00:00+00:00"},
        }

    def test_returns_required_keys(self):
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            result = generate_application(PROFILE, JOB_PYTHON_ENGINEER)
        for key in ("job_title", "company", "url", "scoring", "resume_data", "markdown", "generated_at"):
            assert key in result

    def test_job_title_and_company_populated(self):
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            result = generate_application(PROFILE, JOB_PYTHON_ENGINEER)
        assert result["job_title"] == "Python Backend Engineer"
        assert result["company"] == "TechCorp"

    def test_url_preserved(self):
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            result = generate_application(PROFILE, JOB_PYTHON_ENGINEER)
        assert result["url"] == JOB_PYTHON_ENGINEER["url"]

    def test_scoring_included(self):
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            result = generate_application(PROFILE, JOB_PYTHON_ENGINEER)
        assert "score" in result["scoring"]

    def test_markdown_is_string(self):
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            result = generate_application(PROFILE, JOB_PYTHON_ENGINEER)
        assert isinstance(result["markdown"], str)
        assert len(result["markdown"]) > 0


# ---------------------------------------------------------------------------
# run_batch
# ---------------------------------------------------------------------------

class TestRunBatch:
    JOBS = [JOB_PYTHON_ENGINEER, JOB_DEVOPS, JOB_MARKETING]

    def _mock_tailor(self, *args, **kwargs):
        return {
            "name": "Alice", "summary": "Summary", "skills": ["Python"],
            "experience": [{"title": "Eng", "company": "Co", "highlights": ["Did stuff"]}],
            "cover_letter": "Dear HM,\n\nApplying.\n\nAlice",
            "metadata": {"model": "mock", "generated_at": "2024-01-01T00:00:00+00:00"},
        }

    def test_creates_output_dir(self, tmp_path):
        out = tmp_path / "applications"
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            run_batch(PROFILE, self.JOBS, out)
        assert out.exists()

    def test_summary_written_to_disk(self, tmp_path):
        out = tmp_path / "apps"
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            run_batch(PROFILE, self.JOBS, out)
        summary_file = out / "_summary.json"
        assert summary_file.exists()

    def test_returns_summary_dict(self, tmp_path):
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            summary = run_batch(PROFILE, self.JOBS, tmp_path / "apps")
        assert isinstance(summary, dict)
        assert "total_jobs" in summary
        assert summary["total_jobs"] == 3

    def test_low_score_jobs_skipped(self, tmp_path):
        """Marketing job should be skipped since score < default min_score."""
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            summary = run_batch(PROFILE, self.JOBS, tmp_path / "apps", min_score=0.20)
        assert summary["skipped_low_score"] >= 1

    def test_max_applications_cap(self, tmp_path):
        jobs = [JOB_PYTHON_ENGINEER, JOB_DEVOPS]
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            summary = run_batch(PROFILE, jobs, tmp_path / "apps", max_applications=1)
        assert summary["generated"] <= 1

    def test_json_and_md_files_created(self, tmp_path):
        out = tmp_path / "apps"
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            summary = run_batch(PROFILE, [JOB_PYTHON_ENGINEER], out)
        for app in summary["applications"]:
            assert Path(app["json_file"]).exists()
            assert Path(app["md_file"]).exists()

    def test_empty_jobs_list(self, tmp_path):
        summary = run_batch(PROFILE, [], tmp_path / "apps")
        assert summary["generated"] == 0
        assert summary["total_jobs"] == 0

    def test_error_captured_not_raised(self, tmp_path):
        """If tailor_application throws, the error should be recorded, not crash."""
        def explode(*a, **kw):
            raise RuntimeError("LLM offline")
        with patch("resume_builder.orchestrator.tailor_application", side_effect=explode):
            summary = run_batch(PROFILE, [JOB_PYTHON_ENGINEER], tmp_path / "apps", min_score=0.0)
        assert len(summary["errors"]) == 1
        assert "LLM offline" in summary["errors"][0]["error"]

    def test_applications_list_has_expected_keys(self, tmp_path):
        with patch("resume_builder.orchestrator.tailor_application", side_effect=self._mock_tailor):
            summary = run_batch(PROFILE, [JOB_PYTHON_ENGINEER], tmp_path / "apps")
        if summary["applications"]:
            app = summary["applications"][0]
            for key in ("slug", "title", "company", "score", "recommendation"):
                assert key in app
