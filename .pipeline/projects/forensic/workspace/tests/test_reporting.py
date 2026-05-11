"""Tests for reporting module."""

import json
import os
import tempfile
import pytest
from forensic.reporting import (
    generate_report,
    generate_full_report,
    report_to_json,
    report_to_markdown,
    report_to_summary,
    report_to_dict,
    save_report,
)
from forensic.models import RedFlag, Recommendation, RedFlagSeverity


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------

def test_generate_report():
    report = generate_report(
        ticker="TEST",
        cik="123456",
        filing_date="2023-12-31",
        risk_score=75.5,
        overall_risk="high",
        red_flags=[
            RedFlag(
                category="Revenue Recognition",
                severity=RedFlagSeverity.HIGH,
                description="Suspicious revenue growth",
                evidence="Revenue grew 50% while receivables grew 100%",
            )
        ],
        recommendations=[
            Recommendation(
                category="Revenue Recognition",
                description="Review revenue recognition policies",
                priority="HIGH",
            )
        ],
    )
    assert report.ticker == "TEST"
    assert report.cik == "123456"
    assert report.filing_date == "2023-12-31"
    assert report.risk_score == 75.5
    assert report.overall_risk == "high"
    assert len(report.red_flags) == 1
    assert len(report.recommendations) == 1


# ---------------------------------------------------------------------------
# report_to_json
# ---------------------------------------------------------------------------

def test_report_to_json():
    report = generate_report(
        ticker="TEST",
        cik="123456",
        filing_date="2023-12-31",
        risk_score=75.5,
        overall_risk="high",
        red_flags=[],
        recommendations=[],
    )
    json_str = report_to_json(report)
    parsed = json.loads(json_str)
    assert parsed["ticker"] == "TEST"
    assert parsed["cik"] == "123456"
    assert parsed["risk_score"] == 75.5


# ---------------------------------------------------------------------------
# report_to_dict
# ---------------------------------------------------------------------------

def test_report_to_dict():
    report = generate_report(
        ticker="TEST",
        cik="123456",
        filing_date="2023-12-31",
        risk_score=75.5,
        overall_risk="high",
        red_flags=[],
        recommendations=[],
    )
    d = report_to_dict(report)
    assert d["ticker"] == "TEST"
    assert d["cik"] == "123456"
    assert d["risk_score"] == 75.5


# ---------------------------------------------------------------------------
# save_report
# ---------------------------------------------------------------------------

def test_save_report():
    report = generate_report(
        ticker="TEST",
        cik="123456",
        filing_date="2023-12-31",
        risk_score=75.5,
        overall_risk="high",
        red_flags=[],
        recommendations=[],
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        filepath = f.name
    try:
        save_report(report, filepath)
        with open(filepath) as f:
            parsed = json.load(f)
        assert parsed["ticker"] == "TEST"
    finally:
        os.unlink(filepath)


# ---------------------------------------------------------------------------
# report_to_markdown
# ---------------------------------------------------------------------------

def test_report_to_markdown():
    report = generate_report(
        ticker="TEST",
        cik="123456",
        filing_date="2023-12-31",
        risk_score=75.5,
        overall_risk="high",
        red_flags=[
            RedFlag(
                category="Revenue Recognition",
                severity=RedFlagSeverity.HIGH,
                description="Suspicious revenue growth",
                evidence="Revenue grew 50%",
            )
        ],
        recommendations=[
            Recommendation(
                category="Revenue Recognition",
                description="Review policies",
                priority="HIGH",
            )
        ],
    )
    md = report_to_markdown(report)
    assert "# Fraud Risk Report: TEST" in md
    assert "**CIK:** 123456" in md
    assert "**Risk Score:** 75.5/100" in md
    assert "**Overall Risk:** HIGH" in md
    assert "## Red Flags" in md
    assert "## Recommendations" in md
    assert "Revenue Recognition" in md


def test_report_to_markdown_no_flags():
    report = generate_report(
        ticker="TEST",
        cik="123456",
        filing_date="2023-12-31",
        risk_score=10.0,
        overall_risk="low",
        red_flags=[],
        recommendations=[],
    )
    md = report_to_markdown(report)
    assert "No red flags detected." in md
    assert "No specific recommendations" in md


# ---------------------------------------------------------------------------
# report_to_summary
# ---------------------------------------------------------------------------

def test_report_to_summary():
    report = generate_report(
        ticker="TEST",
        cik="123456",
        filing_date="2023-12-31",
        risk_score=75.5,
        overall_risk="high",
        red_flags=[
            RedFlag(
                category="Revenue Recognition",
                severity=RedFlagSeverity.HIGH,
                description="Suspicious revenue growth",
                evidence="Revenue grew 50%",
            )
        ],
        recommendations=[
            Recommendation(
                category="Revenue Recognition",
                description="Review policies",
                priority="HIGH",
            )
        ],
    )
    summary = report_to_summary(report)
    assert "Fraud Risk Report: TEST" in summary
    assert "CIK: 123456" in summary
    assert "Risk Score: 75.5/100" in summary
    assert "Overall Risk: HIGH" in summary
    assert "Revenue Recognition" in summary


# ---------------------------------------------------------------------------
# generate_full_report
# ---------------------------------------------------------------------------

def test_generate_full_report():
    report = generate_full_report(
        ticker="TEST",
        cik="123456",
        filing_date="2023-12-31",
        risk_score=75.5,
        overall_risk="high",
        red_flags=[],
        recommendations=[],
    )
    assert report.ticker == "TEST"


def test_generate_full_report_with_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        report = generate_full_report(
            ticker="TEST",
            cik="123456",
            filing_date="2023-12-31",
            risk_score=75.5,
            overall_risk="high",
            red_flags=[],
            recommendations=[],
            output_dir=tmpdir,
        )
        assert report.ticker == "TEST"
        # Check that files were created
        assert os.path.exists(os.path.join(tmpdir, "TEST_2023-12-31.json"))
        assert os.path.exists(os.path.join(tmpdir, "TEST_2023-12-31.md"))
        assert os.path.exists(os.path.join(tmpdir, "TEST_2023-12-31.txt"))
