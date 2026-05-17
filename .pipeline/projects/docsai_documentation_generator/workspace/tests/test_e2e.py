"""End-to-end test for the docsai spec command."""

import json
import pathlib
import subprocess
import sys

import pytest

# Ensure the workspace is on the path
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))
# Also add the parent workspace directory so docsai package is importable
_parent = _ws.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))


SAMPLE_PROJECT_DIR = _ws / "sample_project"
OUTPUT_FILE = _ws / "docsai_output" / "api_spec.yaml"
OUTPUT_FILE_JSON = _ws / "docsai_output" / "api_spec.json"


@pytest.fixture(autouse=True)
def clean_output():
    """Remove previous output files before each test."""
    for f in [OUTPUT_FILE, OUTPUT_FILE_JSON]:
        if f.exists():
            f.unlink()
    yield
    # Cleanup after test
    for f in [OUTPUT_FILE, OUTPUT_FILE_JSON]:
        if f.exists():
            f.unlink()


def _run_docsai_spec(output_format: str = "yaml") -> subprocess.CompletedProcess:
    """Run the docsai spec command and return the result."""
    output_path = str(OUTPUT_FILE_JSON) if output_format == "json" else str(OUTPUT_FILE)
    result = subprocess.run(
        [sys.executable, "-c",
         f"""
import sys
sys.path.insert(0, "{_ws}")
sys.path.insert(0, "{_ws.parent}")
from docsai.cli.spec import spec
spec("{SAMPLE_PROJECT_DIR}", output="{output_path}", format="{output_format}")
"""],
        capture_output=True,
        text=True,
        cwd=str(_ws),
    )
    return result


class TestDocsaiSpecE2E:
    """End-to-end tests for the docsai spec command."""

    def test_spec_command_succeeds(self):
        """The docsai spec command should exit with code 0."""
        result = _run_docsai_spec("yaml")
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_spec_output_file_created(self):
        """The output file should be created."""
        _run_docsai_spec("yaml")
        assert OUTPUT_FILE.exists(), "Output YAML file was not created."

    def test_spec_output_file_created_json(self):
        """The output file should be created in JSON format."""
        _run_docsai_spec("json")
        assert OUTPUT_FILE_JSON.exists(), "Output JSON file was not created."

    def test_spec_contains_at_least_3_symbols(self):
        """The spec should contain at least 3 symbols."""
        _run_docsai_spec("yaml")
        import yaml
        with open(OUTPUT_FILE, "r") as f:
            spec = yaml.safe_load(f)
        symbols = spec.get("symbols", [])
        assert len(symbols) >= 3, f"Expected at least 3 symbols, got {len(symbols)}"

    def test_spec_symbols_have_required_fields(self):
        """Each symbol should have name, kind, params, return_type, and docstring."""
        _run_docsai_spec("yaml")
        import yaml
        with open(OUTPUT_FILE, "r") as f:
            spec = yaml.safe_load(f)
        symbols = spec.get("symbols", [])
        required_fields = {"name", "kind", "params", "return_type", "docstring"}
        for sym in symbols:
            for field in required_fields:
                assert field in sym, f"Symbol '{sym.get('name', 'unknown')}' missing field '{field}'"

    def test_spec_contains_python_symbols(self):
        """The spec should contain symbols from the Python sample file."""
        _run_docsai_spec("yaml")
        import yaml
        with open(OUTPUT_FILE, "r") as f:
            spec = yaml.safe_load(f)
        symbols = spec.get("symbols", [])
        names = {s["name"] for s in symbols}
        # Check for symbols from sample_python.py
        assert "greet" in names, "Python 'greet' function not found in spec"
        assert "Calculator" in names, "Python 'Calculator' class not found in spec"

    def test_spec_contains_typescript_symbols(self):
        """The spec should contain symbols from the TypeScript sample file."""
        _run_docsai_spec("yaml")
        import yaml
        with open(OUTPUT_FILE, "r") as f:
            spec = yaml.safe_load(f)
        symbols = spec.get("symbols", [])
        names = {s["name"] for s in symbols}
        # Check for symbols from sample_typescript.ts
        assert "greet" in names, "TypeScript 'greet' function not found in spec"
        assert "Calculator" in names, "TypeScript 'Calculator' class not found in spec"

    def test_spec_json_format(self):
        """The spec output should be valid JSON when format=json is requested."""
        _run_docsai_spec("json")
        with open(OUTPUT_FILE_JSON, "r") as f:
            spec = json.load(f)
        assert "project_name" in spec
        assert "symbols" in spec
        assert "metadata" in spec
        assert len(spec["symbols"]) >= 3

    def test_spec_metadata(self):
        """The spec metadata should contain file_count and total_symbols."""
        _run_docsai_spec("yaml")
        import yaml
        with open(OUTPUT_FILE, "r") as f:
            spec = yaml.safe_load(f)
        metadata = spec.get("metadata", {})
        assert "file_count" in metadata, "metadata missing 'file_count'"
        assert "total_symbols" in metadata, "metadata missing 'total_symbols'"
        assert metadata["total_symbols"] >= 3

    def test_spec_project_name(self):
        """The spec should contain the project name."""
        _run_docsai_spec("yaml")
        import yaml
        with open(OUTPUT_FILE, "r") as f:
            spec = yaml.safe_load(f)
        assert spec.get("project_name") == "sample_project", f"Expected project_name 'sample_project', got {spec.get('project_name')}"
