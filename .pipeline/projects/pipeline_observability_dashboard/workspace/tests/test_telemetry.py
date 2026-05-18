"""Tests for Telemetry Parser."""
import json
from pathlib import Path
from pipeline_observability_dashboard.telemetry import TelemetryParser

def test_telemetry_parser(tmp_path):
    project_dir = tmp_path / "test_project"
    workspace_dir = project_dir / "workspace"
    workspace_dir.mkdir(parents=True)
    
    # Create a mock execution log
    log_data = [
        {
            "status": "success",
            "duration": 2.5,
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "model": "gpt-4"
        },
        {
            "status": "error",
            "error": "Timeout",
            "duration": 5.0,
            "tokens_in": 100,
            "tokens_out": 0,
            "model": "claude-3-haiku"
        }
    ]
    
    (workspace_dir / "execution_log.json").write_text(json.dumps(log_data))
    
    parser = TelemetryParser(project_dir)
    cost, error_rate, avg_duration = parser.parse_metrics()
    
    # Calculate expected cost:
    # GPT-4: (1000/1000 * 0.03) + (500/1000 * 0.06) = 0.03 + 0.03 = 0.06
    # Haiku: (100/1000 * 0.00025) + 0 = 0.000025
    # Total = 0.060025
    assert round(cost, 6) == 0.060025
    assert error_rate == 0.5  # 1 error out of 2 steps
    assert avg_duration == 3.75  # (2.5 + 5.0) / 2
