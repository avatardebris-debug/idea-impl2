"""Tests for Email Tool CLI commands."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from email_tool.cli import EmailToolCLI, main


class TestCLI:
    """Tests for CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cli_version(self):
        """Test version command."""
        cli = EmailToolCLI()
        result = cli.run(['version'])
        
        assert result == 0
    
    def test_cli_help(self):
        """Test help output."""
        cli = EmailToolCLI()
        try:
            cli.run(['--help'])
        except SystemExit as e:
            assert e.code == 0
    
    def test_cli_init_command(self):
        """Test init command."""
        cli = EmailToolCLI()
        result = cli.run(['init', '--config-dir', self.temp_dir])
        
        assert result == 0
        
        # Verify config file was created
        config_file = Path(self.temp_dir) / "config.yaml"
        assert config_file.exists()
    
    def test_cli_init_command_existing_path(self):
        """Test init command on existing path."""
        cli = EmailToolCLI()
        
        # First init
        result1 = cli.run(['init', '--config-dir', self.temp_dir])
        assert result1 == 0
        
        # Second init without force
        result2 = cli.run(['init', '--config-dir', self.temp_dir])
        assert result2 == 1
        
        # Second init with force
        result3 = cli.run(['init', '--config-dir', self.temp_dir, '--force'])
        assert result3 == 0
    
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
        
        cli = EmailToolCLI()
        result = cli.run(['scan', str(self.temp_dir)])
        
        assert result == 0
    
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
    type: from_exact
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        cli = EmailToolCLI()
        result = cli.run(['scan', str(self.temp_dir), '--rules', str(rules_path)])
        
        assert result == 0
    
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
        
        cli = EmailToolCLI()
        result = cli.run(['organize', str(self.temp_dir), '--output', str(output_dir), '--dry-run'])
        
        assert result == 0
    
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
    type: from_exact
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        # Create output directory
        output_dir = Path(self.temp_dir) / "output"
        output_dir.mkdir()
        
        cli = EmailToolCLI()
        result = cli.run(['organize', str(self.temp_dir), '--rules', str(rules_path), '--output', str(output_dir), '--dry-run'])
        
        assert result == 0
    
    def test_cli_sync_command(self):
        """Test sync command."""
        cli = EmailToolCLI()
        result = cli.run(['sync', '--once'])
        
        # Sync might fail if not configured, but should not crash
        assert result in [0, 1]
    
    def test_cli_sync_command_with_interval(self):
        """Test sync command with interval."""
        cli = EmailToolCLI()
        result = cli.run(['sync', '--interval', '300', '--once'])
        
        # Sync might fail if not configured, but should not crash
        assert result in [0, 1]
    
    def test_cli_rules_list(self):
        """Test rules list command."""
        # Create rules file
        rules_content = """rules:
  - name: test_rule
    type: from_exact
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        # Patch DEFAULT_RULES_FILE so the CLI finds the test rules
        import email_tool.cli
        original_default = email_tool.cli.DEFAULT_RULES_FILE
        email_tool.cli.DEFAULT_RULES_FILE = rules_path
        try:
            cli = EmailToolCLI()
            result = cli.run(['rules', '--list'])
            assert result == 0
        finally:
            email_tool.cli.DEFAULT_RULES_FILE = original_default
    
    def test_cli_rules_validate(self):
        """Test rules validate command."""
        # Create valid rules file
        rules_content = """rules:
  - name: test_rule
    type: from_exact
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        cli = EmailToolCLI()
        result = cli.run(['rules', '--validate', str(rules_path)])
        
        assert result == 0
    
    def test_cli_rules_validate_invalid(self):
        """Test rules validate command with invalid file."""
        # Create invalid rules file
        rules_content = """rules:
  - name: test_rule
    invalid_field: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        cli = EmailToolCLI()
        result = cli.run(['rules', '--validate', str(rules_path)])
        
        assert result == 1
    
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
        
        cli = EmailToolCLI()
        result = cli.run(['summary', str(self.temp_dir)])
        
        assert result == 0
    
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
        
        cli = EmailToolCLI()
        result = cli.run(['dry-run', str(self.temp_dir)])
        
        assert result == 0
    
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
    type: from_exact
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        cli = EmailToolCLI()
        result = cli.run(['dry-run', str(self.temp_dir), '--rules', str(rules_path)])
        
        assert result == 0


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
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
        cli = EmailToolCLI()
        result = cli.run(['init', '--config-dir', self.temp_dir])
        assert result == 0
        
        # Scan
        result = cli.run(['scan', str(self.temp_dir)])
        assert result == 0
        
        # Organize
        output_dir = Path(self.temp_dir) / "output"
        output_dir.mkdir()
        result = cli.run(['organize', str(self.temp_dir), '--output', str(output_dir), '--dry-run'])
        assert result == 0
        
        # Summary
        result = cli.run(['summary', str(output_dir)])
        assert result == 0
    
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
    type: from_exact
    pattern: sender@example.com
    category: test
"""
        rules_path = Path(self.temp_dir) / "rules.yaml"
        rules_path.write_text(rules_content)
        
        # Scan with rules
        cli = EmailToolCLI()
        result = cli.run(['scan', str(self.temp_dir), '--rules', str(rules_path)])
        assert result == 0
        
        # Organize with rules
        output_dir = Path(self.temp_dir) / "output"
        output_dir.mkdir()
        result = cli.run(['organize', str(self.temp_dir), '--rules', str(rules_path), '--output', str(output_dir), '--dry-run'])
        assert result == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
