"""
tests/test_cli_integration.py
End-to-end integration tests for the csv-pipeline CLI.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

import pytest

WORKSPACE = pathlib.Path(__file__).resolve().parent
FIXTURES = WORKSPACE / "fixtures"
PROJECT_ROOT = WORKSPACE.parent.parent.parent  # workspace/


def run_cli(*args, cwd=None):
    """Run the csv-pipeline CLI and return (returncode, stdout, stderr)."""
    cmd = [sys.executable, "-m", "csv_data_pipeline_builder.cli"] + list(args)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or str(FIXTURES),
        timeout=30,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


class TestCLIRun:
    """Test the 'run' subcommand end-to-end."""

    def test_run_pipeline_creates_output(self):
        """Running a pipeline YAML should create the output CSV file."""
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            for item in FIXTURES.iterdir():
                if item.is_file():
                    shutil.copy(item, tmpdir)
            out_path = pathlib.Path(tmpdir) / "output.csv"
            pipeline_yaml = FIXTURES / "simple_pipeline.yaml"
            # Update the sink path in the YAML to use tmpdir
            yaml_content = pipeline_yaml.read_text()
            yaml_content = yaml_content.replace("/tmp/test_pipeline_output.csv", str(out_path))
            pipeline_path = pathlib.Path(tmpdir) / "pipeline.yaml"
            pipeline_path.write_text(yaml_content)

            rc, stdout, stderr = run_cli("run", str(pipeline_path), cwd=str(tmpdir))
            assert rc == 0, f"CLI failed: {stderr}"
            assert out_path.exists(), "Output CSV file was not created"

            # Verify the output has correct data
            import csv
            with open(out_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            # Should have 5 rows (2024 sales) grouped by region
            assert len(rows) == 4  # North, South, East, West
            # North should have revenue 100+50=150
            north = [r for r in rows if r["region"] == "North"][0]
            assert float(north["revenue"]) == 150.0

    def test_run_pipeline_with_show_sample(self):
        """--show-sample should print first 3 output rows."""
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            for item in FIXTURES.iterdir():
                if item.is_file():
                    shutil.copy(item, tmpdir)
            out_path = pathlib.Path(tmpdir) / "output.csv"
            pipeline_yaml = FIXTURES / "simple_pipeline.yaml"
            yaml_content = pipeline_yaml.read_text()
            yaml_content = yaml_content.replace("/tmp/test_pipeline_output.csv", str(out_path))
            pipeline_path = pathlib.Path(tmpdir) / "pipeline.yaml"
            pipeline_path.write_text(yaml_content)

            rc, stdout, stderr = run_cli("run", str(pipeline_path), "--show-sample", cwd=str(tmpdir))
            assert rc == 0, f"CLI failed: {stderr}"
            assert "Sample output" in stdout
            assert "Region" in stdout or "region" in stdout

    def test_run_pipeline_invalid_yaml(self):
        """Running with an invalid YAML should fail gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_yaml = pathlib.Path(tmpdir) / "bad.yaml"
            bad_yaml.write_text("steps:\n  - id: x\n    type: nonexistent_type\n")
            rc, stdout, stderr = run_cli("run", str(bad_yaml), cwd=str(tmpdir))
            assert rc != 0  # Should fail

    def test_run_pipeline_missing_source(self):
        """Running with a missing source file should fail gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_yaml = pathlib.Path(tmpdir) / "bad.yaml"
            bad_yaml.write_text(
                "sources:\n  main: nonexistent.csv\n"
                "steps:\n  - id: f\n    type: filter\n"
                "sinks:\n  - type: csv\n    path: out.csv\n"
            )
            rc, stdout, stderr = run_cli("run", str(bad_yaml), cwd=str(tmpdir))
            assert rc != 0  # Should fail


class TestCLIValidate:
    """Test the 'validate' subcommand."""

    def test_validate_valid_pipeline(self):
        """Validating a correct pipeline should succeed."""
        rc, stdout, stderr = run_cli("validate", str(FIXTURES / "simple_pipeline.yaml"))
        assert rc == 0, f"Validation failed: {stderr}"
        assert "Valid" in stdout

    def test_validate_invalid_pipeline(self):
        """Validating an invalid pipeline should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_yaml = pathlib.Path(tmpdir) / "bad.yaml"
            bad_yaml.write_text("steps:\n  - id: x\n    type: nonexistent_type\n")
            rc, stdout, stderr = run_cli("validate", str(bad_yaml), cwd=str(tmpdir))
            assert rc != 0


class TestCLIDryRun:
    """Test the 'dry-run' subcommand."""

    def test_dry_run_schema(self):
        """Dry-run should output the inferred schema."""
        rc, stdout, stderr = run_cli("dry-run", str(FIXTURES / "simple_pipeline.yaml"))
        assert rc == 0, f"Dry-run failed: {stderr}"
        assert "Output schema" in stdout or "schema" in stdout.lower()

    def test_dry_run_invalid_pipeline(self):
        """Dry-run with invalid pipeline should fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_yaml = pathlib.Path(tmpdir) / "bad.yaml"
            bad_yaml.write_text("steps:\n  - id: x\n    type: nonexistent_type\n")
            rc, stdout, stderr = run_cli("dry-run", str(bad_yaml), cwd=str(tmpdir))
            assert rc != 0


class TestCLIInit:
    """Test the 'init' subcommand."""

    def test_init_creates_file(self):
        """Init should create a starter pipeline.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir) / "pipeline.yaml"
            rc, stdout, stderr = run_cli("init", str(target))
            assert rc == 0, f"Init failed: {stderr}"
            assert target.exists()
            content = target.read_text()
            assert "sources:" in content
            assert "steps:" in content
            assert "sinks:" in content

    def test_init_overwrite_fails(self):
        """Init should fail if file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir) / "pipeline.yaml"
            target.write_text("existing")
            rc, stdout, stderr = run_cli("init", str(target))
            assert rc != 0


class TestCLIReport:
    """Test the 'report' subcommand."""

    def test_report_no_previous_run(self):
        """Report with no previous run should indicate no report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, stdout, stderr = run_cli("report", cwd=str(tmpdir))
            assert rc == 0
            assert "No previous run report" in stdout

    def test_report_with_previous_run(self):
        """Report with a previous run file should show the report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_file = pathlib.Path(tmpdir) / ".pipeline_last_run.json"
            report_data = {
                "timestamp": "2024-01-01T00:00:00",
                "file": "test.yaml",
                "output_rows": 10,
                "reports": [
                    {"node_id": "filter", "input_rows": 100, "output_rows": 50, "duration_ms": 5.2},
                    {"node_id": "aggregate", "input_rows": 50, "output_rows": 4, "duration_ms": 3.1},
                ],
            }
            report_file.write_text(json.dumps(report_data))
            rc, stdout, stderr = run_cli("report", cwd=str(tmpdir))
            assert rc == 0
            assert "2024-01-01" in stdout
            assert "test.yaml" in stdout
            assert "10" in stdout


class TestCLIPipelineChain:
    """Test a multi-step pipeline chain via CLI."""

    def test_full_chain_pipeline(self):
        """A pipeline with filter -> select -> aggregate -> pivot should work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a long-format source
            long_csv = pathlib.Path(tmpdir) / "long_data.csv"
            long_csv.write_text(
                "id,category,metric,value\n"
                "1,A,price,10\n"
                "1,A,quantity,5\n"
                "1,B,price,20\n"
                "2,A,price,30\n"
                "2,B,quantity,15\n"
            )

            pipeline_yaml = pathlib.Path(tmpdir) / "pipeline.yaml"
            pipeline_yaml.write_text(
                f"sources:\n"
                f"  main: long_data.csv\n"
                f"steps:\n"
                f"  - id: select\n"
                f"    type: select\n"
                f"    columns: [id, category, metric, value]\n"
                f"  - id: pivot\n"
                f"    type: pivot\n"
                f"    index: [id, category]\n"
                f"    columns: metric\n"
                f"    values: value\n"
                f"    agg: first\n"
                f"sinks:\n"
                f"  - type: csv\n"
                f"    path: {tmpdir}/output.csv\n"
            )

            rc, stdout, stderr = run_cli("run", str(pipeline_yaml), cwd=str(tmpdir))
            assert rc == 0, f"Pipeline failed: {stderr}"

            out_path = pathlib.Path(tmpdir) / "output.csv"
            assert out_path.exists()
            import csv
            with open(out_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert len(rows) > 0
            # Should have columns: id, category, price, quantity
            assert "price" in rows[0] or "quantity" in rows[0]


class TestCLISinkTypes:
    """Test different sink types via CLI."""

    def test_csv_sink(self):
        """CSV sink should create a valid CSV file."""
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            for item in FIXTURES.iterdir():
                if item.is_file():
                    shutil.copy(item, tmpdir)
            out_path = pathlib.Path(tmpdir) / "output.csv"
            pipeline_yaml = FIXTURES / "simple_pipeline.yaml"
            yaml_content = pipeline_yaml.read_text()
            yaml_content = yaml_content.replace("/tmp/test_pipeline_output.csv", str(out_path))
            pipeline_path = pathlib.Path(tmpdir) / "pipeline.yaml"
            pipeline_path.write_text(yaml_content)

            rc, stdout, stderr = run_cli("run", str(pipeline_path), cwd=str(tmpdir))
            assert rc == 0
            assert out_path.exists()

    def test_json_sink(self):
        """JSON sink should create a valid JSON file."""
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            for item in FIXTURES.iterdir():
                if item.is_file():
                    shutil.copy(item, tmpdir)
            out_path = pathlib.Path(tmpdir) / "output.json"
            pipeline_yaml = FIXTURES / "simple_pipeline.yaml"
            yaml_content = pipeline_yaml.read_text()
            yaml_content = yaml_content.replace("/tmp/test_pipeline_output.csv", str(out_path))
            yaml_content = yaml_content.replace(
                "  - type: csv\n    path:",
                "  - type: json\n    path:"
            )
            pipeline_path = pathlib.Path(tmpdir) / "pipeline.yaml"
            pipeline_path.write_text(yaml_content)

            rc, stdout, stderr = run_cli("run", str(pipeline_path), cwd=str(tmpdir))
            assert rc == 0
            assert out_path.exists()
            data = json.loads(out_path.read_text())
            assert isinstance(data, list)
            assert len(data) > 0

    def test_sqlite_sink(self):
        """SQLite sink should create a valid database."""
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            for item in FIXTURES.iterdir():
                if item.is_file():
                    shutil.copy(item, tmpdir)
            out_path = pathlib.Path(tmpdir) / "output.db"
            pipeline_yaml = FIXTURES / "simple_pipeline.yaml"
            yaml_content = pipeline_yaml.read_text()
            yaml_content = yaml_content.replace("/tmp/test_pipeline_output.csv", str(out_path))
            yaml_content = yaml_content.replace(
                "  - type: csv\n    path:",
                "  - type: sqlite\n    path:"
            )
            pipeline_path = pathlib.Path(tmpdir) / "pipeline.yaml"
            pipeline_path.write_text(yaml_content)

            rc, stdout, stderr = run_cli("run", str(pipeline_path), cwd=str(tmpdir))
            assert rc == 0
            assert out_path.exists()

            # Verify the database has data
            import sqlite3
            conn = sqlite3.connect(str(out_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM output")
            count = cursor.fetchone()[0]
            conn.close()
            assert count > 0
