"""tests for observability_dashboard."""
import json
from observability_dashboard.dashboard import parse_logs, format_dashboard

_LOGS = [
    json.dumps({"agent": "extractor", "project": "pdf_schema", "tokens": 1000, "model": "gpt-4", "duration_ms": 500, "error": False}),
    json.dumps({"agent": "summarizer", "project": "pdf_schema", "tokens": 500, "model": "gpt-3.5-turbo", "duration_ms": 200, "error": False}),
    json.dumps({"agent": "extractor", "project": "unweb", "tokens": 2000, "model": "qwen3:6b", "duration_ms": 1000, "error": True}),
    "invalid json line here",
    ""
]

def test_parse_logs_totals():
    stats = parse_logs(_LOGS)
    assert stats.total_executions == 3
    assert stats.global_errors == 1
    # 1000 tokens gpt-4 ($0.03/1k) = $0.03
    # 500 tokens gpt-3.5 ($0.002/1k) = $0.001
    assert abs(stats.global_cost - 0.031) < 0.0001

def test_parse_logs_agent_aggregation():
    stats = parse_logs(_LOGS)
    m = stats.agent_metrics["extractor"]
    assert m.total_calls == 2
    assert m.total_tokens == 3000
    assert m.errors == 1

def test_parse_logs_project_aggregation():
    stats = parse_logs(_LOGS)
    m = stats.project_metrics["pdf_schema"]
    assert m.total_calls == 2
    assert m.total_tokens == 1500
    assert m.errors == 0

def test_format_dashboard():
    stats = parse_logs(_LOGS)
    report = format_dashboard(stats)
    assert "PIPELINE OBSERVABILITY DASHBOARD" in report
    assert "pdf_schema" in report
    assert "extractor" in report
