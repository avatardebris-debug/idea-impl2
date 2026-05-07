"""Unit tests for the CLI (typer app)."""

from typer.testing import CliRunner

from json_schema_profiler.cli import app

runner = CliRunner()
FIXTURES = "tests/fixtures"


# ── Task 3: CLI implementation ────────────────────────────────


class TestCLIHelp:
    """Test (15): --help displays usage."""

    def test_app_help(self):
        """Main --help should show the infer subcommand."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "infer" in result.output

    def test_infer_help(self):
        """infer --help should show options."""
        result = runner.invoke(app, ["infer", "--help"])
        assert result.exit_code == 0
        assert "INPUT_FILE" in result.output
        assert "--output" in result.output
        assert "--format" in result.output


class CLICLIValidInput:
    """Test (12): CLI exits 0 on valid input."""

    def test_infer_simple_object(self):
        """Infer on a simple object should exit 0 and print valid JSON."""
        result = runner.invoke(app, ["infer", f"{FIXTURES}/simple.json"])
        assert result.exit_code == 0
        import json
        schema = json.loads(result.output)
        assert schema["type"] == "object"
        assert "name" in schema["properties"]

    def test_infer_array_of_objects(self):
        """Infer on an array of objects should exit 0."""
        result = runner.invoke(app, ["infer", f"{FIXTURES}/array_of_objects.json"])
        assert result.exit_code == 0
        import json
        schema = json.loads(result.output)
        assert schema["type"] == "array"

    def test_infer_nested_object(self):
        """Infer on a nested object should exit 0."""
        result = runner.invoke(app, ["infer", f"{FIXTURES}/nested.json"])
        assert result.exit_code == 0
        import json
        schema = json.loads(result.output)
        assert schema["type"] == "object"
        assert "address" in schema["properties"]

    def test_infer_mixed_types(self):
        """Infer on mixed types should exit 0."""
        result = runner.invoke(app, ["infer", f"{FIXTURES}/mixed_types.json"])
        assert result.exit_code == 0
        import json
        schema = json.loads(result.output)
        assert schema["type"] == "array"

    def test_infer_empty_array(self):
        """Infer on an empty array should exit 0."""
        result = runner.invoke(app, ["infer", f"{FIXTURES}/empty_array.json"])
        assert result.exit_code == 0

    def test_infer_low_cardinality(self):
        """Infer on low cardinality should exit 0."""
        result = runner.invoke(app, ["infer", f"{FIXTURES}/low_cardinality.json"])
        assert result.exit_code == 0

    def test_infer_large_sample(self):
        """Infer on large sample should exit 0."""
        result = runner.invoke(app, ["infer", f"{FIXTURES}/large_sample.json"])
        assert result.exit_code == 0


class TestCLIInvalidInput:
    """Test (13): CLI exits non-zero on invalid input."""

    def test_nonexistent_file(self):
        """A non-existent file should exit non-zero."""
        result = runner.invoke(app, ["infer", "nonexistent.json"])
        assert result.exit_code != 0
        assert "Error" in result.output or "error" in result.output.lower()

    def test_invalid_json(self):
        """Invalid JSON should exit non-zero."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json}")
            f.flush()
            result = runner.invoke(app, ["infer", f.name])
        assert result.exit_code != 0


class TestCLIOutput:
    """Test (14): CLI --output writes to file."""

    def test_output_flag(self, tmp_path):
        """--output should write the schema to the specified file."""
        output_file = tmp_path / "schema.json"
        result = runner.invoke(
            app,
            ["infer", f"{FIXTURES}/simple.json", "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        import json
        with open(output_file) as f:
            schema = json.load(f)
        assert schema["type"] == "object"
        assert "name" in schema["properties"]

    def test_output_format_jsonschema(self, tmp_path):
        """--format jsonschema should work (current and only format)."""
        output_file = tmp_path / "schema.json"
        result = runner.invoke(
            app,
            [
                "infer",
                f"{FIXTURES}/simple.json",
                "--output",
                str(output_file),
                "--format",
                "jsonschema",
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()


class TestCLIFormat:
    """Test --format option."""

    def test_default_format_is_jsonschema(self):
        """Default format should be jsonschema."""
        result = runner.invoke(app, ["infer", f"{FIXTURES}/simple.json"])
        assert result.exit_code == 0
        import json
        schema = json.loads(result.output)
        assert "type" in schema
        assert "properties" in schema
