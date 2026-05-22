"""Tests for Email Tool configuration.

This module contains comprehensive tests for configuration loading,
validation, and environment variable handling.
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from email_tool.config import (
    EmailToolConfig,
    ConfigValidationError,
    load_config,
    validate_rule_config,
    validate_rule_config_file,
    load_rules_from_dict,
    load_rules_from_yaml,
    _parse_rule
)
from email_tool.models import Rule, RuleType


class TestEmailToolConfig:
    """Tests for EmailToolConfig class."""
    
    def test_config_default_values(self):
        """Test configuration with default values."""
        config = EmailToolConfig()
        
        assert config.get_log_level() == "INFO"
        assert config.get_log_file() is None
        assert config.get_output_format() == "eml"
        assert config.get_collision_strategy() == "rename"
        assert config.get_dashboard_enabled() is False
        assert config.get_dashboard_port() == 8000
        assert config.get_sync_enabled() is False
        assert config.get_sync_interval() == 3600
        assert config.get_sync_sources() == []
    
    def test_config_from_file(self, tmp_path):
        """Test configuration loading from file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "log_level": "DEBUG",
            "log_file": str(tmp_path / "test.log"),
            "base_path": str(tmp_path / "emails"),
            "output_format": "msg",
            "collision_strategy": "overwrite",
            "dashboard": {
                "enabled": True,
                "port": 9000
            },
            "sync": {
                "enabled": True,
                "interval": 1800,
                "sources": ["source1", "source2"]
            },
            "rules": {
                "path": str(tmp_path / "rules.yaml")
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = EmailToolConfig(config_file)
        
        assert config.get_log_level() == "DEBUG"
        assert config.get_log_file() == str(tmp_path / "test.log")
        assert config.get_base_path() == str(tmp_path / "emails")
        assert config.get_output_format() == "msg"
        assert config.get_collision_strategy() == "overwrite"
        assert config.get_dashboard_enabled() is True
        assert config.get_dashboard_port() == 9000
        assert config.get_sync_enabled() is True
        assert config.get_sync_interval() == 1800
        assert config.get_sync_sources() == ["source1", "source2"]
        assert config.get_rules_path() == str(tmp_path / "rules.yaml")
    
    def test_config_from_env_variables(self, monkeypatch):
        """Test configuration loading from environment variables."""
        monkeypatch.setenv('EMAIL_TOOL_LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('EMAIL_TOOL_LOG_FILE', '/tmp/test.log')
        monkeypatch.setenv('EMAIL_TOOL_BASE_PATH', '/tmp/emails')
        monkeypatch.setenv('EMAIL_TOOL_OUTPUT_FORMAT', 'msg')
        monkeypatch.setenv('EMAIL_TOOL_DASHBOARD_ENABLED', 'true')
        monkeypatch.setenv('EMAIL_TOOL_DASHBOARD_PORT', '9000')
        monkeypatch.setenv('EMAIL_TOOL_SYNC_ENABLED', 'true')
        monkeypatch.setenv('EMAIL_TOOL_SYNC_INTERVAL', '1800')
        monkeypatch.setenv('EMAIL_TOOL_SYNC_SOURCES', 'source1,source2')
        
        config = EmailToolConfig()
        
        assert config.get_log_level() == "DEBUG"
        assert config.get_log_file() == "/tmp/test.log"
        assert config.get_base_path() == "/tmp/emails"
        assert config.get_output_format() == "msg"
        assert config.get_dashboard_enabled() is True
        assert config.get_dashboard_port() == 9000
        assert config.get_sync_enabled() is True
        assert config.get_sync_interval() == 1800
    
    def test_config_file_overrides_env(self, monkeypatch, tmp_path):
        """Test that file configuration overrides environment variables."""
        # Set environment variables
        monkeypatch.setenv('EMAIL_TOOL_LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('EMAIL_TOOL_BASE_PATH', '/tmp/env_emails')
        
        # Create config file with different values
        config_file = tmp_path / "config.yaml"
        config_data = {
            "log_level": "INFO",
            "base_path": str(tmp_path / "file_emails")
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = EmailToolConfig(config_file)
        
        # File values should take precedence
        assert config.get_log_level() == "INFO"
        assert config.get_base_path() == str(tmp_path / "file_emails")
    
    def test_config_get_nested_key(self):
        """Test getting nested configuration values."""
        config = EmailToolConfig()
        
        assert config.get('dashboard.enabled') is False
        assert config.get('dashboard.port') == 8000
        assert config.get('sync.enabled') is False
        assert config.get('sync.interval') == 3600
    
    def test_config_get_nonexistent_key(self):
        """Test getting non-existent configuration key."""
        config = EmailToolConfig()
        
        assert config.get('nonexistent.key') is None
        assert config.get('nonexistent.key', 'default') == 'default'
    
    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        config = EmailToolConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'log_level' in config_dict
        assert 'dashboard' in config_dict
        assert 'sync' in config_dict
    
    def test_config_save(self, tmp_path):
        """Test configuration saving to file."""
        config = EmailToolConfig()
        config_file = tmp_path / "config.yaml"
        
        config.save(config_file)
        
        assert config_file.exists()
        
        # Verify saved content
        with open(config_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data['log_level'] == 'INFO'
        assert saved_data['dashboard']['enabled'] is False
    
    def test_config_validation_error(self):
        """Test ConfigValidationError."""
        error = ConfigValidationError(
            message="Invalid configuration",
            file="config.yaml",
            line=10
        )
        
        assert str(error) == "Invalid configuration | file: config.yaml | line 10"
        assert error.file == "config.yaml"
        assert error.line == 10


class TestValidateRuleConfig:
    """Tests for validate_rule_config function."""
    
    def test_validate_rule_valid(self):
        """Test validation of valid rule."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_exact",
            "pattern": "test@example.com",
            "priority": 75,
            "category": "testing"
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 0
    
    def test_validate_rule_missing_name(self):
        """Test validation of rule without name."""
        rule_data = {
            "type": "from_exact"
        }
        
        errors = validate_rule_config(rule_data, "unnamed_rule")
        
        assert len(errors) == 1
        assert "missing required field 'name'" in errors[0]
    
    def test_validate_rule_empty_name(self):
        """Test validation of rule with empty name."""
        rule_data = {
            "name": "",
            "type": "from_exact"
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 1
        assert "name cannot be empty" in errors[0]
    
    def test_validate_rule_missing_type(self):
        """Test validation of rule without type."""
        rule_data = {
            "name": "Test Rule"
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 1
        assert "missing required field 'type'" in errors[0]
    
    def test_validate_rule_invalid_type(self):
        """Test validation of rule with invalid type."""
        rule_data = {
            "name": "Test Rule",
            "type": "invalid_type"
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 1
        assert "invalid rule type" in errors[0]
    
    def test_validate_rule_missing_pattern(self):
        """Test validation of pattern-based rule without pattern."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_pattern"
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 1
        assert "missing required field 'pattern'" in errors[0]
    
    def test_validate_rule_invalid_regex(self):
        """Test validation of rule with invalid regex pattern."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_pattern",
            "pattern": "[invalid(regex"
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 1
        assert "invalid regex pattern" in errors[0]
    
    def test_validate_rule_invalid_priority_not_int(self):
        """Test validation of rule with non-integer priority."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_exact",
            "priority": "high"
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 1
        assert "priority must be an integer" in errors[0]
    
    def test_validate_rule_priority_too_low(self):
        """Test validation of rule with priority below minimum."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_exact",
            "priority": -1
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 1
        assert "priority must be between 0 and 100" in errors[0]
    
    def test_validate_rule_priority_too_high(self):
        """Test validation of rule with priority above maximum."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_exact",
            "priority": 101
        }
        
        errors = validate_rule_config(rule_data, "Test Rule")
        
        assert len(errors) == 1
        assert "priority must be between 0 and 100" in errors[0]
    
    def test_validate_rule_valid_with_all_fields(self):
        """Test validation of rule with all fields."""
        rule_data = {
            "name": "Complete Rule",
            "type": "subject_pattern",
            "pattern": ".*test.*",
            "priority": 50,
            "category": "testing",
            "description": "A complete test rule"
        }
        
        errors = validate_rule_config(rule_data, "Complete Rule")
        
        assert len(errors) == 0


class TestLoadRulesFromDict:
    """Tests for load_rules_from_dict function."""
    
    def test_load_rules_from_dict_valid(self):
        """Test loading valid rules from dictionary."""
        rules_dict = {
            "rules": [
                {
                    "name": "Rule 1",
                    "type": "from_exact",
                    "pattern": "test@example.com",
                    "priority": 75
                },
                {
                    "name": "Rule 2",
                    "type": "subject_contains",
                    "pattern": "test",
                    "priority": 50
                }
            ]
        }
        
        rules = load_rules_from_dict(rules_dict)
        
        assert len(rules) == 2
        assert rules[0].name == "Rule 1"
        assert rules[0].rule_type == RuleType.FROM_EXACT
        assert rules[1].name == "Rule 2"
        assert rules[1].rule_type == RuleType.SUBJECT_CONTAINS
    
    def test_load_rules_from_dict_empty(self):
        """Test loading rules from empty dictionary."""
        rules_dict = {}
        
        rules = load_rules_from_dict(rules_dict)
        
        assert len(rules) == 0
    
    def test_load_rules_from_dict_missing_rules_key(self):
        """Test loading rules from dictionary without rules key."""
        rules_dict = {
            "other_key": "value"
        }
        
        rules = load_rules_from_dict(rules_dict)
        
        assert len(rules) == 0
    
    def test_load_rules_from_dict_with_errors(self, capsys):
        """Test loading rules with validation errors."""
        rules_dict = {
            "rules": [
                {
                    "name": "Invalid Rule",
                    "type": "invalid_type"
                }
            ]
        }
        
        rules = load_rules_from_dict(rules_dict)
        
        assert len(rules) == 0
        captured = capsys.readouterr()
        assert "Validation error" in captured.err


class TestLoadRulesFromYaml:
    """Tests for load_rules_from_yaml function."""
    
    def test_load_rules_from_yaml_valid(self, tmp_path):
        """Test loading rules from valid YAML file."""
        rules_file = tmp_path / "rules.yaml"
        rules_data = {
            "rules": [
                {
                    "name": "Rule 1",
                    "type": "from_exact",
                    "pattern": "test@example.com",
                    "priority": 75
                }
            ]
        }
        
        with open(rules_file, 'w') as f:
            yaml.dump(rules_data, f)
        
        rules = load_rules_from_yaml(rules_file)
        
        assert len(rules) == 1
        assert rules[0].name == "Rule 1"
    
    def test_load_rules_from_yaml_file_not_found(self, tmp_path):
        """Test loading rules from non-existent file."""
        rules_file = tmp_path / "nonexistent.yaml"
        
        rules = load_rules_from_yaml(rules_file)
        
        assert len(rules) == 0
    
    def test_load_rules_from_yaml_invalid_yaml(self, tmp_path):
        """Test loading rules from invalid YAML file."""
        rules_file = tmp_path / "invalid.yaml"
        rules_file.write_text("invalid: yaml: content: [")
        
        rules = load_rules_from_yaml(rules_file)
        
        assert len(rules) == 0


class TestParseRule:
    """Tests for _parse_rule helper function."""
    
    def test_parse_rule_from_exact(self):
        """Test parsing FROM_EXACT rule."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_exact",
            "pattern": "test@example.com"
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.FROM_EXACT
        assert rule.pattern == "test@example.com"
    
    def test_parse_rule_from_pattern(self):
        """Test parsing FROM_PATTERN rule."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_pattern",
            "pattern": ".*@example\\.com"
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.FROM_PATTERN
        assert rule.pattern == ".*@example\\.com"
    
    def test_parse_rule_subject_contains(self):
        """Test parsing SUBJECT_CONTAINS rule."""
        rule_data = {
            "name": "Test Rule",
            "type": "subject_contains",
            "pattern": "test"
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.SUBJECT_CONTAINS
        assert rule.pattern == "test"
    
    def test_parse_rule_subject_pattern(self):
        """Test parsing SUBJECT_PATTERN rule."""
        rule_data = {
            "name": "Test Rule",
            "type": "subject_pattern",
            "pattern": ".*test.*"
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.SUBJECT_PATTERN
        assert rule.pattern == ".*test.*"
    
    def test_parse_rule_body_contains(self):
        """Test parsing BODY_CONTAINS rule."""
        rule_data = {
            "name": "Test Rule",
            "type": "body_contains",
            "pattern": "test"
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.BODY_CONTAINS
        assert rule.pattern == "test"
    
    def test_parse_rule_body_pattern(self):
        """Test parsing BODY_PATTERN rule."""
        rule_data = {
            "name": "Test Rule",
            "type": "body_pattern",
            "pattern": ".*test.*"
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.BODY_PATTERN
        assert rule.pattern == ".*test.*"
    
    def test_parse_rule_with_optional_fields(self):
        """Test parsing rule with optional fields."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_exact",
            "pattern": "test@example.com",
            "priority": 75,
            "category": "testing",
            "description": "A test rule"
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.name == "Test Rule"
        assert rule.priority == 75
        assert rule.category == "testing"
        assert rule.description == "A test rule"
    
    def test_parse_rule_with_labels(self):
        """Test parsing rule with labels."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_exact",
            "pattern": "test@example.com",
            "labels": ["label1", "label2"]
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.labels == ["label1", "label2"]
    
    def test_parse_rule_with_enabled_false(self):
        """Test parsing rule with enabled=false."""
        rule_data = {
            "name": "Test Rule",
            "type": "from_exact",
            "pattern": "test@example.com",
            "enabled": False
        }
        
        rule = _parse_rule(rule_data, "Test Rule")
        
        assert rule.enabled is False
    
    def test_parse_rule_invalid_type(self):
        """Test parsing rule with invalid type."""
        rule_data = {
            "name": "Test Rule",
            "type": "invalid_type"
        }
        
        with pytest.raises(ValueError, match="invalid rule type"):
            _parse_rule(rule_data, "Test Rule")


class TestValidateRuleConfigFile:
    """Tests for validate_rule_config_file function."""
    
    def test_validate_rule_config_file_valid(self, tmp_path):
        """Test validation of valid rules file."""
        rules_file = tmp_path / "rules.yaml"
        rules_data = {
            "rules": [
                {
                    "name": "Rule 1",
                    "type": "from_exact",
                    "pattern": "test@example.com",
                    "priority": 75
                }
            ]
        }
        
        with open(rules_file, 'w') as f:
            yaml.dump(rules_data, f)
        
        errors = validate_rule_config_file(rules_file)
        
        assert len(errors) == 0
    
    def test_validate_rule_config_file_invalid(self, tmp_path):
        """Test validation of invalid rules file."""
        rules_file = tmp_path / "rules.yaml"
        rules_data = {
            "rules": [
                {
                    "name": "Invalid Rule",
                    "type": "invalid_type"
                }
            ]
        }
        
        with open(rules_file, 'w') as f:
            yaml.dump(rules_data, f)
        
        errors = validate_rule_config_file(rules_file)
        
        assert len(errors) == 1
        assert "Validation error" in errors[0]
    
    def test_validate_rule_config_file_file_not_found(self, tmp_path):
        """Test validation of non-existent rules file."""
        rules_file = tmp_path / "nonexistent.yaml"
        
        errors = validate_rule_config_file(rules_file)
        
        assert len(errors) == 1
        assert "File not found" in errors[0]


class TestLoadConfig:
    """Tests for load_config function."""
    
    def test_load_config_from_file(self, tmp_path):
        """Test loading configuration from file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "log_level": "DEBUG",
            "output_format": "msg"
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        
        assert isinstance(config, EmailToolConfig)
        assert config.get_log_level() == "DEBUG"
        assert config.get_output_format() == "msg"
    
    def test_load_config_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv('EMAIL_TOOL_LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('EMAIL_TOOL_OUTPUT_FORMAT', 'msg')
        
        config = load_config()
        
        assert isinstance(config, EmailToolConfig)
        assert config.get_log_level() == "DEBUG"
        assert config.get_output_format() == "msg"
    
    def test_load_config_file_overrides_env(self, monkeypatch, tmp_path):
        """Test that file configuration overrides environment variables."""
        # Set environment variables
        monkeypatch.setenv('EMAIL_TOOL_LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('EMAIL_TOOL_OUTPUT_FORMAT', 'msg')
        
        # Create config file with different values
        config_file = tmp_path / "config.yaml"
        config_data = {
            "log_level": "INFO",
            "output_format": "eml"
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        
        # File values should take precedence
        assert config.get_log_level() == "INFO"
        assert config.get_output_format() == "eml"
    
    def test_load_config_no_file_no_env(self, monkeypatch):
        """Test loading configuration with no file and no environment variables."""
        # Clear environment variables
        monkeypatch.delenv('EMAIL_TOOL_LOG_LEVEL', raising=False)
        monkeypatch.delenv('EMAIL_TOOL_OUTPUT_FORMAT', raising=False)
        
        config = load_config()
        
        assert isinstance(config, EmailToolConfig)
        assert config.get_log_level() == "INFO"
        assert config.get_output_format() == "eml"