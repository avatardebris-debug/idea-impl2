"""CLI integration tests for the Audiobook Script Pipeline."""

import os
import subprocess
import sys
import tempfile

import pytest


@pytest.fixture
def cli_script():
    """Path to the CLI script."""
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "audiobook_script_pipeline",
        "cli.py",
    )


@pytest.fixture
def sample_manuscript():
    """Create a temporary manuscript file for testing."""
    content = "# Chapter One\n\nHello world. This is a test.\n\n# Chapter Two\n\nAnother chapter."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        f.flush()
        tmp_path = f.name
    try:
        yield tmp_path
    finally:
        os.unlink(tmp_path)


@pytest.fixture
def output_file():
    """Create a temporary output file path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.flush()
        tmp_path = f.name
    try:
        yield tmp_path
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def run_cli(*extra_args, cli_script=None):
    """Helper to run the CLI and return the result."""
    if cli_script is None:
        cli_script = os.path.join(
            os.path.dirname(__file__),
            "..",
            "audiobook_script_pipeline",
            "cli.py",
        )
    cmd = [sys.executable, cli_script] + list(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


# --- CLI tests ---

def test_cli_valid_manuscript_prints_output(cli_script, sample_manuscript):
    """Test running the CLI with a valid manuscript file prints output."""
    result = run_cli(sample_manuscript, cli_script=cli_script)
    assert result.returncode == 0
    assert "Chapter One" in result.stdout
    assert "Chapter Two" in result.stdout


def test_cli_output_contains_pacing_markers(cli_script, sample_manuscript):
    """Test that CLI output contains pacing markers."""
    result = run_cli(sample_manuscript, cli_script=cli_script)
    assert result.returncode == 0
    assert "[SLOW]" in result.stdout
    assert "[PAUSE:" in result.stdout
    assert "[FAST]" in result.stdout


def test_cli_output_flag_writes_file(cli_script, sample_manuscript, output_file):
    """Test that --output flag writes the output to a file."""
    result = run_cli(sample_manuscript, "-o", output_file, cli_script=cli_script)
    assert result.returncode == 0
    assert "Audio script written to:" in result.stdout
    assert os.path.isfile(output_file)
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Chapter One" in content
    assert "[SLOW]" in content


def test_cli_pause_flag(cli_script, sample_manuscript):
    """Test that --pause flag sets the pause duration."""
    result = run_cli(sample_manuscript, "--pause", "3.0", cli_script=cli_script)
    assert result.returncode == 0
    assert "[PAUSE: 3.0s]" in result.stdout


def test_cli_nonexistent_file_exits_with_error(cli_script):
    """Test that running with a non-existent file exits with code 1."""
    result = run_cli("/nonexistent/file.txt", cli_script=cli_script)
    assert result.returncode == 1
    assert "Error: File not found" in result.stderr


def test_cli_help_prints_usage(cli_script):
    """Test that --help prints usage information."""
    result = run_cli("--help", cli_script=cli_script)
    assert result.returncode == 0
    assert "Convert a manuscript text file" in result.stdout
    assert "manuscript" in result.stdout
    assert "--output" in result.stdout
    assert "--pause" in result.stdout


def test_cli_empty_file_exits_with_error(cli_script):
    """Test that running with an empty file exits with code 1."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("")
        f.flush()
        tmp_path = f.name
    try:
        result = run_cli(tmp_path, cli_script=cli_script)
        assert result.returncode == 1
        assert "Error: Manuscript is empty" in result.stderr
    finally:
        os.unlink(tmp_path)


def test_cli_blank_file_exits_with_error(cli_script):
    """Test that running with a blank file exits with code 1."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("   \n\n  ")
        f.flush()
        tmp_path = f.name
    try:
        result = run_cli(tmp_path, cli_script=cli_script)
        assert result.returncode == 1
        assert "Error: Manuscript is empty" in result.stderr
    finally:
        os.unlink(tmp_path)


def test_cli_output_overwrites_existing_file(cli_script, sample_manuscript, output_file):
    """Test that --output overwrites an existing file."""
    # Create an existing file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Old content")

    result = run_cli(sample_manuscript, "-o", output_file, cli_script=cli_script)
    assert result.returncode == 0
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Chapter One" in content
    assert "Old content" not in content
