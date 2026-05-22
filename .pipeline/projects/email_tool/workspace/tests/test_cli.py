"""Tests for Email Tool CLI commands."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
from email_tool.cli import EmailToolCLI


class TestCLI:
    """Tests for CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cli_version(self):
        """Test version subcommand."""
        result = self.runner.invoke(EmailToolCLI(), args=['version'])
        
        assert result.exit_code == 0
        assert "email_tool version" in result.output
    
    def test_cli_help(self):
        """Test help output."""
        result = self.runner.invoke(EmailToolCLI(), args=[])
        
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "init" in result.output
        assert "scan" in result.output
        assert "organize" in result.output
        assert "sync" in result.output
        assert "rules" in result.output
        assert "summary" in result.output
        assert "dry-run" in result.output
        assert "version" in result.output
    
    def test_cli_init_command(self):
        """Test init command."""
        result = self.runner.invoke(EmailToolCLI(), args=['init', '--config-dir', self.temp_dir])
        
        assert result.exit_code == 0
        assert "Configuration initialized" in result.output
        
        # Verify config file was created
        config_file = Path(self.temp_dir) / "config.yaml"
        assert config_file.exists()
    
    def test_cli_init_command_existing_path(self):
        """Test init command on existing path."""
        # First init
        result1 = self.runner.invoke(EmailToolCLI(), args=['init', '--config-dir', self.temp_dir])
        assert result1.exit_code == 0
        
        # Second init without force
        result2 = self.runner.invoke(EmailToolCLI(), args=['init', '--config-dir', self.temp_dir])
        assert result2.exit_code == 1
        assert "already exists" in result2.output
        
        # Second init with force
        result3 = self.runner.invoke(EmailToolCLI(), args=['init', '--config-dir', self.temp_dir, '--force'])
        assert result3.exit_code == 0
    
    def test_cli_scan_command(self):
        """Test scan command."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        result = self.runner.invoke(EmailToolCLI(), args=['scan', str(self.temp_dir)])
        
        assert result.exit_code == 0
        assert "Scan Results" in result.output
    
    def test_cli_scan_command_with_rules(self):
        """Test scan command with rules file."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        # Create rules file
        rules_content = """rules:
  - name: test_rule
    rule_type: from
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        result = self.runner.invoke(EmailToolCLI(), args=['scan', str(self.temp_dir), '--rules', str(rules_path)])
        
        assert result.exit_code == 0
        assert "Loaded" in result.output
    
    def test_cli_organize_command(self):
        """Test organize command."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        # Create output directory
        output_dir = Path(self.temp_dir) / "output"
        output_dir.mkdir()
        
        result = self.runner.invoke(EmailToolCLI(), args=['organize', str(self.temp_dir), '--output', str(output_dir), '--dry-run'])
        
        assert result.exit_code == 0
        assert "Organization Results" in result.output
        assert "Dry run" in result.output
    
    def test_cli_organize_command_with_rules(self):
        """Test organize command with rules."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        # Create rules file
        rules_content = """rules:
  - name: test_rule
    rule_type: from
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        # Create output directory
        output_dir = Path(self.temp_dir) / "output"
        output_dir.mkdir()
        
        result = self.runner.invoke(EmailToolCLI(), args=['organize', str(self.temp_dir), '--rules', str(rules_path), '--output', str(output_dir), '--dry-run'])
        
        assert result.exit_code == 0
        assert "Loaded" in result.output
    
    def test_cli_sync_command(self):
        """Test sync command."""
        result = self.runner.invoke(EmailToolCLI(), args=['sync', '--once'])
        
        # Sync might fail if not configured, but should not crash
        assert result.exit_code in [0, 1]
    
    def test_cli_sync_command_with_interval(self):
        """Test sync command with interval."""
        result = self.runner.invoke(EmailToolCLI(), args=['sync', '--interval', '300', '--once'])
        
        # Sync might fail if not configured, but should not crash
        assert result.exit_code in [0, 1]
    
    def test_cli_rules_list(self):
        """Test rules list command."""
        # Create rules file
        rules_content = """rules:
  - name: test_rule
    rule_type: from
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        # Configure rules path
        config_content = f"""log_level: INFO
rules:
  path: {rules_path}
"""
        config_path = Path(self.temp_dir) / "config.yaml"
        config_path.write_text(config_content)
        
        result = self.runner.invoke(EmailToolCLI(), args=['rules', '--list', '--config', str(config_path)])
        
        assert result.exit_code == 0
        assert "Loaded" in result.output
    
    def test_cli_rules_validate(self):
        """Test rules validate command."""
        # Create valid rules file
        rules_content = """rules:
  - name: test_rule
    rule_type: from
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        result = self.runner.invoke(EmailToolCLI(), args=['rules', '--validate', str(rules_path)])
        
        assert result.exit_code == 0
        assert "valid" in result.output
    
    def test_cli_rules_validate_invalid(self):
        """Test rules validate command with invalid file."""
        # Create invalid rules file
        rules_content = """rules:
  - name: test_rule
    invalid_field: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        result = self.runner.invoke(EmailToolCLI(), args=['rules', '--validate', str(rules_path)])
        
        assert result.exit_code == 1
        assert "Validation failed" in result.output
    
    def test_cli_summary_command(self):
        """Test summary command."""
        # Create organized email structure
        category_dir = Path(self.temp_dir) / "inbox"
        category_dir.mkdir()
        
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = category_dir / "test.eml"
        email_path.write_text(email_content)
        
        result = self.runner.invoke(EmailToolCLI(), args=['summary', str(self.temp_dir)])
        
        assert result.exit_code == 0
        assert "Email Organization Summary" in result.output
        assert "Total files" in result.output
    
    def test_cli_dry_run_command(self):
        """Test dry-run command."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        result = self.runner.invoke(EmailToolCLI(), args=['dry-run', str(self.temp_dir)])
        
        assert result.exit_code == 0
        assert "Dry Run Results" in result.output
    
    def test_cli_dry_run_command_with_rules(self):
        """Test dry-run command with rules."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        # Create rules file
        rules_content = """rules:
  - name: test_rule
    rule_type: from
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        result = self.runner.invoke(EmailToolCLI(), args=['dry-run', str(self.temp_dir), '--rules', str(rules_path)])
        
        assert result.exit_code == 0
        assert "Loaded" in result.output


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cli_full_workflow(self):
        """Test full workflow: init, scan, organize, summary."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        # Init
        result = self.runner.invoke(EmailToolCLI(), args=['init', '--config-dir', self.temp_dir])
        assert result.exit_code == 0
        
        # Scan
        result = self.runner.invoke(EmailToolCLI(), args=['scan', str(self.temp_dir)])
        assert result.exit_code == 0
        
        # Organize
        output_dir = Path(self.temp_dir) / "output"
        output_dir.mkdir()
        result = self.runner.invoke(EmailToolCLI(), args=['organize', str(self.temp_dir), '--output', str(output_dir), '--dry-run'])
        assert result.exit_code == 0
        
        # Summary
        result = self.runner.invoke(EmailToolCLI(), args=['summary', str(output_dir)])
        assert result.exit_code == 0
    
    def test_cli_with_rules(self):
        """Test CLI with rules file."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        # Create rules file
        rules_content = """rules:
  - name: test_rule
    rule_type: from
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        # Scan with rules
        result = self.runner.invoke(EmailToolCLI(), args=['scan', str(self.temp_dir), '--rules', str(rules_path)])
        assert result.exit_code == 0
        assert "Loaded" in result.output
        
        # Organize with rules
        output_dir = Path(self.temp_dir) / "output"
        output_dir.mkdir()
        result = self.runner.invoke(EmailToolCLI(), args=['organize', str(self.temp_dir), '--rules', str(rules_path), '--output', str(output_dir), '--dry-run'])
        assert result.exit_code == 0
    
    def test_cli_with_search_and_filter(self):
        """Test CLI with search and filter operations."""
        # Create test emails
        email1_content = """From: sender1@example.com
To: recipient@test.com
Subject: Test Email 1
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the first email.
"""
        email2_content = """From: sender2@example.com
To: recipient@test.com
Subject: Test Email 2
Date: Mon, 15 Mar 2024 11:30:00 +0000

This is the second email.
"""
        email1_path = Path(self.temp_dir) / "test1.eml"
        email1_path.write_text(email1_content)
        email2_path = Path(self.temp_dir) / "test2.eml"
        email2_path.write_text(email2_content)
        
        # Create rules file
        rules_content = """rules:
  - name: sender1_rule
    rule_type: from
    pattern: sender1@example.com
    category: sender1
  - name: sender2_rule
    rule_type: from
    pattern: sender2@example.com
    category: sender2
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        # Scan with rules
        result = self.runner.invoke(EmailToolCLI(), args=['scan', str(self.temp_dir), '--rules', str(rules_path)])
        assert result.exit_code == 0
        assert "Loaded" in result.output


class TestCLIEdgeCases:
    """Edge case tests for CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cli_init_with_special_characters(self):
        """Test init with special characters in path."""
        special_dir = Path(self.temp_dir) / "test-dir_with.special"
        special_dir.mkdir()
        
        result = self.runner.invoke(EmailToolCLI(), args=['init', '--config-dir', str(special_dir)])
        
        assert result.exit_code == 0
        assert "Configuration initialized" in result.output
    
    def test_cli_scan_nonexistent_path(self):
        """Test scan with nonexistent path."""
        result = self.runner.invoke(EmailToolCLI(), args=['scan', '/nonexistent/path'])
        
        # Should handle gracefully
        assert result.exit_code in [0, 1]
    
    def test_cli_organize_nonexistent_path(self):
        """Test organize with nonexistent path."""
        result = self.runner.invoke(EmailToolCLI(), args=['organize', '/nonexistent/path'])
        
        # Should handle gracefully
        assert result.exit_code in [0, 1]
    
    def test_cli_summary_nonexistent_path(self):
        """Test summary with nonexistent path."""
        result = self.runner.invoke(EmailToolCLI(), args=['summary', '/nonexistent/path'])
        
        assert result.exit_code == 1
        assert "not found" in result.output
    
    def test_cli_rules_validate_nonexistent_file(self):
        """Test rules validate with nonexistent file."""
        result = self.runner.invoke(EmailToolCLI(), args=['rules', '--validate', '/nonexistent/rules.yaml'])
        
        assert result.exit_code == 1
        assert "not found" in result.output or "Validation failed" in result.output
    
    def test_cli_multiple_commands(self):
        """Test running multiple commands in sequence."""
        # Init
        result1 = self.runner.invoke(EmailToolCLI(), args=['init', '--config-dir', self.temp_dir])
        assert result1.exit_code == 0
        
        # Scan
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = Path(self.temp_dir) / "test.eml"
        email_path.write_text(email_content)
        
        result2 = self.runner.invoke(EmailToolCLI(), args=['scan', str(self.temp_dir)])
        assert result2.exit_code == 0
        
        # Summary
        result3 = self.runner.invoke(EmailToolCLI(), args=['summary', str(self.temp_dir)])
        assert result3.exit_code == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
