"""Tests for skillify.cli — command-line interface."""
import json
import pathlib
import subprocess
import sys
import tempfile

import pytest

# Ensure workspace is on path
_ws = pathlib.Path(__file__).resolve().parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))


class TestCLIBasic:
    """Test CLI via subprocess (python -m skillify)."""

    def _write_extraction(self, tmpdir):
        data = {
            "title": "CLI Test Skill",
            "description": "Test via CLI",
            "tags": ["test"],
            "steps": [{"title": "Step 1", "description": "First step"}],
        }
        path = tmpdir / "extraction.json"
        path.write_text(json.dumps(data, indent=2))
        return path

    def test_cli_default_output(self, tmp_path):
        extraction = self._write_extraction(tmp_path)
        result = subprocess.run(
            [sys.executable, "-m", "skillify", str(extraction)],
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Default output is skill.json in cwd
        assert (tmp_path / "skill.json").exists()

    def test_cli_output_flag(self, tmp_path):
        extraction = self._write_extraction(tmp_path)
        out = tmp_path / "custom_output.json"
        result = subprocess.run(
            [sys.executable, "-m", "skillify", str(extraction), "--output", str(out)],
            capture_output=True, text=True, cwd=str(_ws)
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["skill_id"] == "cli_test_skill"

    def test_cli_id_flag(self, tmp_path):
        extraction = self._write_extraction(tmp_path)
        out = tmp_path / "skill.json"
        result = subprocess.run(
            [sys.executable, "-m", "skillify", str(extraction), "--id", "my_custom_id", "--output", str(out)],
            capture_output=True, text=True, cwd=str(_ws)
        )
        assert result.returncode == 0
        data = json.loads(out.read_text())
        assert data["skill_id"] == "my_custom_id"

    def test_cli_pretty_flag(self, tmp_path):
        extraction = self._write_extraction(tmp_path)
        out = tmp_path / "skill.json"
        result = subprocess.run(
            [sys.executable, "-m", "skillify", str(extraction), "--output", str(out), "--pretty"],
            capture_output=True, text=True, cwd=str(_ws)
        )
        assert result.returncode == 0
        data = json.loads(out.read_text())
        assert data["skill_id"] == "cli_test_skill"

    def test_cli_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "skillify", "--help"],
            capture_output=True, text=True, cwd=str(_ws)
        )
        assert result.returncode == 0
        assert "Convert an extraction JSON" in result.stdout

    def test_cli_missing_file(self):
        result = subprocess.run(
            [sys.executable, "-m", "skillify", "/nonexistent/file.json"],
            capture_output=True, text=True, cwd=str(_ws)
        )
        assert result.returncode != 0
