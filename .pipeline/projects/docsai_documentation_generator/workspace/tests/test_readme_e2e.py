"""End-to-end tests for the docsai readme command."""

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
OUTPUT_FILE = _ws / "tests" / "docsai_output" / "readme.md"


@pytest.fixture(autouse=True)
def clean_output():
    """Remove previous output files before each test."""
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()
    yield
    # Cleanup after test
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()


def _run_docsai_readme() -> subprocess.CompletedProcess:
    """Run the docsai readme command and return the result."""
    result = subprocess.run(
        [sys.executable, "-c",
         f"""
import sys
sys.path.insert(0, "{_ws.parent.as_posix()}")
from docsai.cli.readme import readme
readme("{SAMPLE_PROJECT_DIR.as_posix()}", output="{OUTPUT_FILE.as_posix()}")
"""],
        capture_output=True,
        text=True,
        cwd=str(_ws),
    )
    return result


class TestDocsaiReadmeE2E:
    """End-to-end tests for the docsai readme command."""

    def test_readme_command_succeeds(self):
        """The docsai readme command should exit with code 0."""
        result = _run_docsai_readme()
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_readme_output_file_created(self):
        """The output file should be created."""
        _run_docsai_readme()
        assert OUTPUT_FILE.exists(), "Output README.md file was not created."

    def test_readme_contains_project_name(self):
        """The README should contain the project name."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert "sample_project" in content, "Project name 'sample_project' not found in README"

    def test_readme_contains_python_symbols(self):
        """The README should contain symbols from the Python sample file."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert "greet" in content, "Python 'greet' function not found in README"
        assert "Calculator" in content, "Python 'Calculator' class not found in README"

    def test_readme_contains_typescript_symbols(self):
        """The README should contain symbols from the TypeScript sample file."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert "greet" in content, "TypeScript 'greet' function not found in README"
        assert "Calculator" in content, "TypeScript 'Calculator' class not found in README"

    def test_readme_contains_markdown_formatting(self):
        """The README should contain valid markdown formatting."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        # Should have at least one heading
        assert "# " in content, "README should contain markdown headings"
        # Should have at least one code block
        assert "```" in content, "README should contain markdown code blocks"

    def test_readme_contains_usage_examples(self):
        """The README should contain usage examples."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert "Usage" in content or "usage" in content, "README should contain usage examples"

    def test_readme_contains_architecture_notes(self):
        """The README should contain architecture notes."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert "Architecture" in content or "architecture" in content, "README should contain architecture notes"

    def test_readme_contains_project_description(self):
        """The README should contain a project description."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert "Description" in content or "description" in content, "README should contain a project description"

    def test_readme_contains_metadata(self):
        """The README should contain metadata about the project."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        # Should contain file count or symbol count
        assert "file" in content.lower() or "symbol" in content.lower(), "README should contain metadata about files or symbols"

    def test_readme_contains_language_info(self):
        """The README should contain language information."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert "python" in content.lower() or "typescript" in content.lower(), "README should contain language information"

    def test_readme_is_not_empty(self):
        """The README should not be empty."""
        _run_docsai_readme()
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        assert len(content) > 0, "README should not be empty"
        assert len(content) > 100, "README should have substantial content"
