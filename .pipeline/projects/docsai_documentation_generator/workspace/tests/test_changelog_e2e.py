"""End-to-end tests for the docsai changelog command."""

import json
import pathlib
import subprocess
import sys

import pytest

# Ensure the workspace root is on the path
_ws = pathlib.Path(__file__).parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))


SAMPLE_PROJECT_DIR = _ws / "tests" / "sample_project"
CHANGELOG_OUTPUT = _ws / "tests" / "docsai_output" / "CHANGELOG.md"


@pytest.fixture(autouse=True)
def clean_output():
    """Remove previous output files before each test."""
    if CHANGELOG_OUTPUT.exists():
        CHANGELOG_OUTPUT.unlink()
    yield
    # Cleanup after test
    if CHANGELOG_OUTPUT.exists():
        CHANGELOG_OUTPUT.unlink()


def _run_docsai_changelog(extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run the docsai changelog command and return the result."""
    cmd = [
        sys.executable, "-m", "docsai.cli", "changelog",
        "--input-dir", str(SAMPLE_PROJECT_DIR),
        "--output", str(CHANGELOG_OUTPUT),
    ]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_ws),
    )
    return result


class TestDocsaiChangelogE2E:
    """End-to-end tests for the docsai changelog command."""

    def test_changelog_command_succeeds(self):
        """The docsai changelog command should exit with code 0."""
        result = _run_docsai_changelog()
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_changelog_output_file_created(self):
        """The output file should be created."""
        _run_docsai_changelog()
        assert CHANGELOG_OUTPUT.exists(), "Output CHANGELOG.md file was not created."

    def test_changelog_contains_version(self):
        """The changelog should contain a version number."""
        _run_docsai_changelog()
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        assert "##" in content, "Changelog should contain version headings"

    def test_changelog_contains_categories(self):
        """The changelog should contain categorized entries."""
        _run_docsai_changelog()
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        # Should have at least one category heading
        assert "###" in content, "Changelog should contain category headings"

    def test_changelog_contains_bullet_points(self):
        """The changelog should contain bullet points for entries."""
        _run_docsai_changelog()
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        assert "- " in content, "Changelog should contain bullet points"

    def test_changelog_contains_date(self):
        """The changelog should contain a date."""
        _run_docsai_changelog()
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        # Should have a date in YYYY-MM-DD format
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", content), "Changelog should contain a date"

    def test_changelog_is_not_empty(self):
        """The changelog should not be empty."""
        _run_docsai_changelog()
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        assert len(content) > 0, "Changelog should not be empty"
        assert len(content) > 50, "Changelog should have substantial content"

    def test_changelog_help_works(self):
        """Test that the changelog subcommand help works."""
        result = subprocess.run(
            [sys.executable, "-m", "docsai.cli", "changelog", "--help"],
            capture_output=True,
            text=True,
            cwd=str(_ws),
        )
        assert result.returncode == 0
        assert "Generate changelog from git history" in result.stdout

    def test_changelog_with_custom_version(self):
        """Test the changelog command with a custom version."""
        result = _run_docsai_changelog(extra_args=["--version", "1.2.3"])
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        assert "1.2.3" in content, "Changelog should contain the custom version"

    def test_changelog_with_custom_commit_count(self):
        """Test the changelog command with a custom commit count."""
        result = _run_docsai_changelog(extra_args=["--commit-count", "5"])
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert CHANGELOG_OUTPUT.exists(), "Output file should be created"

    def test_changelog_with_llm_options(self):
        """Test the changelog command with LLM options."""
        result = _run_docsai_changelog(extra_args=[
            "--llm-provider", "openai",
            "--llm-model", "gpt-4o-mini",
            "--llm-temperature", "0.5",
        ])
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert CHANGELOG_OUTPUT.exists(), "Output file should be created"

    def test_changelog_with_custom_template_dir(self):
        """Test the changelog command with a custom template directory."""
        result = _run_docsai_changelog(extra_args=[
            "--template-dir", str(_ws / "docsai" / "templates"),
        ])
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert CHANGELOG_OUTPUT.exists(), "Output file should be created"

    def test_changelog_with_custom_template(self):
        """Test the changelog command with a custom template filename."""
        result = _run_docsai_changelog(extra_args=[
            "--template", "changelog_default.md",
        ])
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert CHANGELOG_OUTPUT.exists(), "Output file should be created"

    def test_changelog_output_format_is_markdown(self):
        """The changelog output should be valid markdown."""
        _run_docsai_changelog()
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        # Should have markdown headings
        assert content.startswith("#") or "##" in content, "Output should be markdown"

    def test_changelog_output_is_readable(self):
        """The changelog output should be readable by humans."""
        _run_docsai_changelog()
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        # Should not contain raw JSON or code
        assert "```" not in content or "```" in content[:100], "Output should be mostly readable text"

    def test_changelog_integration_with_sample_project(self):
        """Test that the changelog works with the sample project structure."""
        result = _run_docsai_changelog()
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        content = CHANGELOG_OUTPUT.read_text(encoding="utf-8")
        # The sample project has specific files, so the changelog should reference them
        assert len(content) > 100, "Changelog should have substantial content from sample project"
