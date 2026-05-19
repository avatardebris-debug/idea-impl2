"""
test_cli.py — Unit tests for CLI argument parsing and validation.

Covers: format choices, output file writing, stdin input simulation,
        and error handling for invalid inputs.
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

WORKSPACE = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
CLI = WORKSPACE / "extraction" / "cli.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_cli(*extra_args: str, stdin_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess and return the CompletedProcess."""
    cmd = [PYTHON, str(CLI)] + list(extra_args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=stdin_text,
        timeout=30,
    )


def run_cli_module(*extra_args: str, stdin_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run `python -m extraction` as a subprocess."""
    cmd = [PYTHON, "-m", "extraction"] + list(extra_args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        input=stdin_text,
        timeout=30,
        cwd=str(WORKSPACE),
    )


# ---------------------------------------------------------------------------
# Test: format choices
# ---------------------------------------------------------------------------

class TestFormatChoices:
    @pytest.mark.parametrize("fmt", ["recipe", "steps", "sop"])
    def test_valid_format_choices(self, fmt):
        """All three format choices should be accepted."""
        tmp = WORKSPACE / "tests" / f"_tmp_{fmt}.txt"
        tmp.write_text("Do step one. Then step two.", encoding="utf-8")
        try:
            result = run_cli_module(str(tmp), "--format", fmt, "--no-llm")
            assert result.returncode == 0, f"stderr: {result.stderr}"
            output = json.loads(result.stdout)
            assert output["format"] == fmt
        finally:
            tmp.unlink(missing_ok=True)

    def test_invalid_format_rejected(self):
        """An invalid format should be rejected by argparse."""
        tmp = WORKSPACE / "tests" / "_tmp_invalid_fmt.txt"
        tmp.write_text("test", encoding="utf-8")
        try:
            result = run_cli_module(str(tmp), "--format", "invalid")
            assert result.returncode != 0
        finally:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test: output file creation
# ---------------------------------------------------------------------------

class TestOutputFile:
    def test_output_file_created(self):
        """--output should write JSON to the specified file."""
        tmp_input = WORKSPACE / "tests" / "_tmp_out_input.txt"
        tmp_input.write_text("Step one. Step two.", encoding="utf-8")
        tmp_output = WORKSPACE / "tests" / "_tmp_out.json"
        try:
            result = run_cli_module(str(tmp_input), "--output", str(tmp_output), "--no-llm")
            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert tmp_output.exists()
            data = json.loads(tmp_output.read_text(encoding="utf-8"))
            assert "steps" in data
        finally:
            tmp_input.unlink(missing_ok=True)
            tmp_output.unlink(missing_ok=True)

    def test_output_file_nested_dir(self):
        """--output should create parent directories if needed."""
        tmp_input = WORKSPACE / "tests" / "_tmp_nested_input.txt"
        tmp_input.write_text("Do it.", encoding="utf-8")
        tmp_output = WORKSPACE / "tests" / "subdir" / "nested" / "out.json"
        try:
            result = run_cli_module(str(tmp_input), "--output", str(tmp_output), "--no-llm")
            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert tmp_output.exists()
        finally:
            tmp_input.unlink(missing_ok=True)
            tmp_output.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test: stdin input simulation
# ---------------------------------------------------------------------------

class TestStdinInput:
    def test_stdin_dash_input(self):
        """Passing '-' as input should read from stdin."""
        result = run_cli_module("-", "--no-llm", stdin_text="First do A. Then do B.")
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = json.loads(result.stdout)
        assert len(output["steps"]) >= 1

    def test_empty_stdin_rejected(self):
        """Empty stdin should produce an error."""
        result = run_cli_module("-", "--no-llm", stdin_text="")
        assert result.returncode != 0
        assert "empty input" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Test: error handling for invalid inputs
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_missing_file(self):
        """Non-existent file should produce an error."""
        result = run_cli_module("/nonexistent/path/file.txt", "--no-llm")
        assert result.returncode != 0
        assert "not found" in result.stderr.lower()

    def test_missing_file_via_cli_module(self):
        """Non-existent file should produce an error (via cli module)."""
        result = run_cli_module("/nonexistent/path/file.txt", "--no-llm")
        assert result.returncode != 0
        assert "not found" in result.stderr.lower()

    def test_valid_input_exits_zero(self):
        """Valid input should exit with code 0."""
        tmp = WORKSPACE / "tests" / "_tmp_valid.txt"
        tmp.write_text("Step 1. Step 2. Step 3.", encoding="utf-8")
        try:
            result = run_cli_module(str(tmp), "--no-llm")
            assert result.returncode == 0
        finally:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test: pretty-print option
# ---------------------------------------------------------------------------

class TestPrettyPrint:
    def test_pretty_print_produces_multiline(self):
        """--pretty should produce indented (multiline) JSON."""
        tmp = WORKSPACE / "tests" / "_tmp_pretty.txt"
        tmp.write_text("Do it.", encoding="utf-8")
        try:
            result = run_cli_module(str(tmp), "--no-llm", "--pretty")
            assert result.returncode == 0
            # Pretty-printed JSON should have newlines
            assert "\n" in result.stdout
        finally:
            tmp.unlink(missing_ok=True)

    def test_no_pretty_produces_single_line(self):
        """Without --pretty, JSON should be a single line."""
        tmp = WORKSPACE / "tests" / "_tmp_nopretty.txt"
        tmp.write_text("Do it.", encoding="utf-8")
        try:
            result = run_cli_module(str(tmp), "--no-llm")
            assert result.returncode == 0
            # Should be a single line (strip trailing newline)
            lines = result.stdout.strip().splitlines()
            assert len(lines) == 1
        finally:
            tmp.unlink(missing_ok=True)
