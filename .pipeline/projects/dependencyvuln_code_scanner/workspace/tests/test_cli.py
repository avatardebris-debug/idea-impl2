"""Tests for CLI."""
import json
import os
import tempfile
import pytest
from click.testing import CliRunner
from depvuln.cli import cli


class TestCli:
    """Test suite for CLI commands."""

    def setup_method(self):
        """Create a temporary directory with sample files for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_cli_version(self):
        """Test that --version works."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_scan_no_findings(self):
        """Test scanning a file with no vulnerabilities."""
        # Create a simple requirements.txt with no known vulns
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("requests==99.99.99\n")  # Non-existent version, should not crash
        
        result = self.runner.invoke(cli, ["scan", req_file, "--format", "text"])
        # Should not crash; exit code depends on findings
        assert result.exit_code in (0, 1)

    def test_scan_json_output(self):
        """Test JSON output format."""
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("requests==99.99.99\n")
        
        result = self.runner.invoke(cli, ["scan", req_file, "--format", "json"])
        assert result.exit_code in (0, 1)
        # Should be valid JSON
        try:
            data = json.loads(result.output)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_scan_html_output(self):
        """Test HTML output format."""
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("requests==99.99.99\n")
        
        result = self.runner.invoke(cli, ["scan", req_file, "--format", "html"])
        assert result.exit_code in (0, 1)
        assert "<html" in result.output.lower() or "<!doctype" in result.output.lower() or "<div" in result.output.lower()

    def test_scan_with_output_file(self):
        """Test scanning with output to a file."""
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        out_file = os.path.join(self.temp_dir, "output.txt")
        with open(req_file, "w") as f:
            f.write("requests==99.99.99\n")
        
        result = self.runner.invoke(cli, ["scan", req_file, "--output", out_file])
        assert result.exit_code in (0, 1)
        assert os.path.exists(out_file)

    def test_scan_directory(self):
        """Test scanning a directory."""
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("requests==99.99.99\n")
        
        result = self.runner.invoke(cli, ["scan", self.temp_dir])
        assert result.exit_code in (0, 1)

    def test_config_show(self):
        """Test config show command."""
        result = self.runner.invoke(cli, ["config-show"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert "output_format" in data

    def test_config_set(self):
        """Test config set command."""
        result = self.runner.invoke(cli, ["config-set", "--key", "output_format", "--value", "json"])
        assert result.exit_code == 0
        assert "Set output_format" in result.output

    def test_scan_with_threshold(self):
        """Test scanning with severity threshold."""
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("requests==99.99.99\n")
        
        result = self.runner.invoke(cli, ["scan", req_file, "--threshold", "HIGH"])
        assert result.exit_code in (0, 1)

    def test_scan_with_cache(self):
        """Test scanning with cache enabled."""
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("requests==99.99.99\n")
        
        result = self.runner.invoke(cli, ["scan", req_file, "--cache"])
        assert result.exit_code in (0, 1)

    def test_scan_with_no_cache(self):
        """Test scanning with cache disabled."""
        req_file = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_file, "w") as f:
            f.write("requests==99.99.99\n")
        
        result = self.runner.invoke(cli, ["scan", req_file, "--no-cache"])
        assert result.exit_code in (0, 1)

    def test_scan_nonexistent_file(self):
        """Test scanning a nonexistent file."""
        result = self.runner.invoke(cli, ["scan", "/nonexistent/path"])
        assert result.exit_code == 0

    def test_scan_package_lock_json(self):
        """Test scanning package-lock.json."""
        pkg_file = os.path.join(self.temp_dir, "package-lock.json")
        with open(pkg_file, "w") as f:
            f.write('{"name": "test", "lockfileVersion": 2, "dependencies": {}}\n')
        
        result = self.runner.invoke(cli, ["scan", pkg_file])
        assert result.exit_code in (0, 1)

    def test_scan_pom_xml(self):
        """Test scanning pom.xml."""
        pom_file = os.path.join(self.temp_dir, "pom.xml")
        with open(pom_file, "w") as f:
            f.write('<?xml version="1.0"?><project><modelVersion>4.0.0</modelVersion></project>\n')
        
        result = self.runner.invoke(cli, ["scan", pom_file])
        assert result.exit_code in (0, 1)

    def test_scan_cargo_toml(self):
        """Test scanning Cargo.toml."""
        cargo_file = os.path.join(self.temp_dir, "Cargo.toml")
        with open(cargo_file, "w") as f:
            f.write('[package]\nname = "test"\nversion = "0.1.0"\n')
        
        result = self.runner.invoke(cli, ["scan", cargo_file])
        assert result.exit_code in (0, 1)

    def test_scan_go_mod(self):
        """Test scanning go.mod."""
        go_file = os.path.join(self.temp_dir, "go.mod")
        with open(go_file, "w") as f:
            f.write('module example.com/test\n\ngo 1.21\n')
        
        result = self.runner.invoke(cli, ["scan", go_file])
        assert result.exit_code in (0, 1)
