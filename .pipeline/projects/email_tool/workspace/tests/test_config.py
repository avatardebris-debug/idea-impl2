"""Unit tests for the configuration module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from email_tool.config import EmailToolConfig, load_config, validate_rule_config, load_rules_from_yaml, load_rules_from_dict


class TestEmailToolConfigInitialization:
    """Tests for EmailToolConfig initialization."""

    def test_config_initialization_default(self):
        """Test EmailToolConfig initialization with default path."""
        config = EmailToolConfig()
        assert config.config_path == config.DEFAULT_CONFIG_FILE
        assert isinstance(config.config, dict)

    def test_config_initialization_custom_path(self):
        """Test EmailToolConfig initialization with custom path."""
        custom_path = Path("/tmp/custom_config.yaml")
        config = EmailToolConfig(config_path=custom_path)
        assert config.config_path == custom_path

    def test_config_initialization_nonexistent_file(self):
        """Test EmailToolConfig initialization with non-existent file."""
        config = EmailToolConfig(config_path=Path("/tmp/nonexistent.yaml"))
        assert config.config_path == Path("/tmp/nonexistent.yaml")
        # Should have default config loaded
        assert 'log_level' in config.config


class TestEmailToolConfigLoading:
    """Tests for configuration loading."""

    def test_load_config_from_file(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
log_level: DEBUG
base_path: /tmp/test_base
output_format: eml
""")
        
        config = EmailToolConfig(config_path=config_file)
        assert config.get('log_level') == 'DEBUG'
        assert config.get('base_path') == '/tmp/test_base'
        assert config.get('output_format') == 'eml'

    def test_load_config_empty_file(self, tmp_path):
        """Test loading configuration from empty YAML file."""
        config_file = tmp_path / "empty_config.yaml"
        config_file.write_text("")
        
        config = EmailToolConfig(config_path=config_file)
        # Should have default values
        assert config.get('log_level') == 'INFO'

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test loading configuration from invalid YAML file."""
        config_file = tmp_path / "invalid_config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with patch('email_tool.config.logger') as mock_logger:
            config = EmailToolConfig(config_path=config_file)
            # Should handle error gracefully
            assert config.get('log_level') == 'INFO'


class TestEmailToolConfigEnvironment:
    """Tests for environment variable configuration."""

    def test_load_from_environment(self, tmp_path, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv('EMAIL_TOOL_LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('EMAIL_TOOL_BASE_PATH', '/tmp/env_base')
        
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get('log_level') == 'DEBUG'
        assert config.get('base_path') == '/tmp/env_base'

    def test_file_config_overrides_environment(self, tmp_path, monkeypatch):
        """Test that file configuration overrides environment variables."""
        monkeypatch.setenv('EMAIL_TOOL_LOG_LEVEL', 'DEBUG')
        
        config_file = tmp_path / "config.yaml"
        config_file.write_text("log_level: INFO")
        
        config = EmailToolConfig(config_path=config_file)
        assert config.get('log_level') == 'INFO'

    def test_dashboard_environment_variables(self, tmp_path, monkeypatch):
        """Test dashboard configuration from environment."""
        monkeypatch.setenv('EMAIL_TOOL_DASHBOARD_ENABLED', 'true')
        monkeypatch.setenv('EMAIL_TOOL_DASHBOARD_PORT', '9000')
        
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get('dashboard.enabled') is True
        assert config.get('dashboard.port') == 9000


class TestEmailToolConfigGetters:
    """Tests for configuration getter methods."""

    def test_get_log_level(self, tmp_path):
        """Test get_log_level method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_log_level() == 'INFO'

    def test_get_log_file(self, tmp_path):
        """Test get_log_file method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_log_file() is None

    def test_get_base_path(self, tmp_path):
        """Test get_base_path method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_base_path() == str(Path.home() / "email_organized")

    def test_get_output_format(self, tmp_path):
        """Test get_output_format method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_output_format() == 'eml'

    def test_get_collision_strategy(self, tmp_path):
        """Test get_collision_strategy method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_collision_strategy() == 'rename'

    def test_get_dashboard_enabled(self, tmp_path):
        """Test get_dashboard_enabled method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_dashboard_enabled() is False

    def test_get_dashboard_port(self, tmp_path):
        """Test get_dashboard_port method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_dashboard_port() == 8000

    def test_get_sync_enabled(self, tmp_path):
        """Test get_sync_enabled method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_sync_enabled() is False

    def test_get_sync_interval(self, tmp_path):
        """Test get_sync_interval method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_sync_interval() == 3600

    def test_get_sync_sources(self, tmp_path):
        """Test get_sync_sources method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_sync_sources() == []

    def test_get_rules_path(self, tmp_path):
        """Test get_rules_path method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get_rules_path() is None


class TestEmailToolConfigDotNotation:
    """Tests for dot notation configuration access."""

    def test_dot_notation_simple(self, tmp_path):
        """Test dot notation for simple keys."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get('log_level') == 'INFO'

    def test_dot_notation_nested(self, tmp_path):
        """Test dot notation for nested keys."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get('dashboard.enabled') is False
        assert config.get('dashboard.port') == 8000

    def test_dot_notation_nonexistent(self, tmp_path):
        """Test dot notation for non-existent keys."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get('nonexistent.key') is None

    def test_dot_notation_with_default(self, tmp_path):
        """Test dot notation with default value."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        assert config.get('nonexistent.key', 'default') == 'default'


class TestEmailToolConfigMethods:
    """Tests for EmailToolConfig methods."""

    def test_to_dict(self, tmp_path):
        """Test to_dict method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert 'log_level' in config_dict

    def test_save_config(self, tmp_path):
        """Test save method."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        config.save()
        
        assert config.config_path.exists()
        assert config.config_path.read_text() != ""

    def test_save_config_custom_path(self, tmp_path):
        """Test save method with custom path."""
        config = EmailToolConfig(config_path=tmp_path / "config.yaml")
        custom_path = tmp_path / "custom_config.yaml"
        config.save(path=custom_path)
        
        assert custom_path.exists()


class TestLoadConfigFunction:
    """Tests for load_config function."""

    def test_load_config_function(self, tmp_path):
        """Test load_config function."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("log_level: DEBUG")
        
        config = load_config(config_path=config_file)
        assert isinstance(config, EmailToolConfig)
        assert config.get('log_level') == 'DEBUG'

    def test_load_config_default(self, tmp_path):
        """Test load_config function with default path."""
        config = load_config()
        assert isinstance(config, EmailToolConfig)


class TestValidateRuleConfig:
    """Tests for rule configuration validation."""

    def test_validate_valid_rule(self):
        """Test validation of valid rule."""
        rule_data = {
            "name": "test_rule",
            "type": "from_exact",
            "pattern": "test@example.com",
            "priority": 50
        }
        
        errors = validate_rule_config(rule_data, "test_rule")
        assert len(errors) == 0

    def test_validate_missing_name(self):
        """Test validation of rule with missing name."""
        rule_data = {
            "type": "from_exact",
            "pattern": "test@example.com"
        }
        
        errors = validate_rule_config(rule_data, "unnamed_rule")
        assert len(errors) > 0
        assert "missing required field 'name'" in errors[0]

    def test_validate_empty_name(self):
        """Test validation of rule with empty name."""
        rule_data = {
            "name": "",
            "type": "from_exact",
            "pattern": "test@example.com"
        }
        
        errors = validate_rule_config(rule_data, "test_rule")
        assert len(errors) > 0
        assert "name cannot be empty" in errors[0]

    def test_validate_missing_type(self):
        """Test validation of rule with missing type."""
        rule_data = {
            "name": "test_rule",
            "pattern": "test@example.com"
        }
        
        errors = validate_rule_config(rule_data, "test_rule")
        assert len(errors) > 0
        assert "missing required field 'type'" in errors[0]

    def test_validate_invalid_type(self):
        """Test validation of rule with invalid type."""
        rule_data = {
            "name": "test_rule",
            "type": "invalid_type",
            "pattern": "test@example.com"
        }
        
        errors = validate_rule_config(rule_data, "test_rule")
        assert len(errors) > 0
        assert "invalid rule type" in errors[0]

    def test_validate_missing_pattern_for_pattern_rule(self):
        """Test validation of pattern rule without pattern."""
        rule_data = {
            "name": "test_rule",
            "type": "from_pattern",
            "priority": 50
        }
        
        errors = validate_rule_config(rule_data, "test_rule")
        assert len(errors) > 0
        assert "missing required field 'pattern'" in errors[0]

    def test_validate_invalid_regex_pattern(self):
        """Test validation of rule with invalid regex pattern."""
        rule_data = {
            "name": "test_rule",
            "type": "from_pattern",
            "pattern": "[invalid(regex"
        }
        
        errors = validate_rule_config(rule_data, "test_rule")
        assert len(errors) > 0
        assert "invalid regex pattern" in errors[0]

    def test_validate_invalid_priority_type(self):
        """Test validation of rule with non-integer priority."""
        rule_data = {
            "name": "test_rule",
            "type": "from_exact",
            "pattern": "test@example.com",
            "priority": "high"
        }
        
        errors = validate_rule_config(rule_data, "test_rule")
        assert len(errors) > 0
        assert "priority must be an integer" in errors[0]

    def test_validate_priority_out_of_range(self):
        """Test validation of rule with priority out of range."""
        rule_data = {
            "name": "test_rule",
            "type": "from_exact",
            "pattern": "test@example.com",
            "priority": 150
        }
        
        errors = validate_rule_config(rule_data, "test_rule")
        assert len(errors) > 0
        assert "priority must be between 0 and 100" in errors[0]


class TestLoadRulesFromDict:
    """Tests for loading rules from dictionary."""

    def test_load_rules_from_dict_valid(self):
        """Test loading valid rules from dictionary."""
        rules_dict = {
            "rules": [
                {
                    "name": "rule1",
                    "type": "from_exact",
                    "pattern": "test@example.com",
                    "priority": 50
                },
                {
                    "name": "rule2",
                    "type": "subject_exact",
                    "pattern": "Test Subject",
                    "priority": 60
                }
            ]
        }
        
        rules = load_rules_from_dict(rules_dict)
        assert len(rules) == 2
        assert rules[0].name == "rule1"
        assert rules[1].name == "rule2"

    def test_load_rules_from_dict_invalid_skipped(self):
        """Test loading rules with invalid entries skipped."""
        rules_dict = {
            "rules": [
                {
                    "name": "valid_rule",
                    "type": "from_exact",
                    "pattern": "test@example.com"
                },
                {
                    "type": "from_exact",  # Missing name
                    "pattern": "test@example.com"
                }
            ]
        }
        
        with patch('email_tool.config.logger') as mock_logger:
            rules = load_rules_from_dict(rules_dict)
            assert len(rules) == 1
            assert rules[0].name == "valid_rule"


class TestLoadRulesFromYaml:
    """Tests for loading rules from YAML file."""

    def test_load_rules_from_yaml_valid(self, tmp_path):
        """Test loading valid rules from YAML file."""
        rules_file = tmp_path / "rules.yaml"
        rules_file.write_text("""
rules:
  - name: rule1
    type: from_exact
    pattern: test@example.com
    priority: 50
  - name: rule2
    type: subject_exact
    pattern: Test Subject
    priority: 60
""")
        
        rules = load_rules_from_yaml(str(rules_file))
        assert len(rules) == 2
        assert rules[0].name == "rule1"

    def test_load_rules_from_yaml_nonexistent(self, tmp_path):
        """Test loading rules from non-existent file."""
        rules = load_rules_from_yaml(str(tmp_path / "nonexistent.yaml"))
        assert len(rules) == 0

    def test_load_rules_from_yaml_invalid_yaml(self, tmp_path):
        """Test loading rules from invalid YAML file."""
        rules_file = tmp_path / "invalid.yaml"
        rules_file.write_text("invalid: yaml: [")
        
        with patch('email_tool.config.logger') as mock_logger:
            rules = load_rules_from_yaml(str(rules_file))
            assert len(rules) == 0


class TestEmailToolConfigEdgeCases:
    """Tests for edge cases."""

    def test_config_with_special_characters_in_path(self, tmp_path):
        """Test configuration with special characters in path."""
        config_file = tmp_path / "config with spaces.yaml"
        config_file.write_text("log_level: DEBUG")
        
        config = EmailToolConfig(config_path=config_file)
        assert config.get('log_level') == 'DEBUG'

    def test_config_with_unicode_content(self, tmp_path):
        """Test configuration with unicode content."""
        config_file = tmp_path / "unicode_config.yaml"
        config_file.write_text("base_path: /tmp/日本語フォルダ", encoding="utf-8")
        
        config = EmailToolConfig(config_path=config_file)
        assert config.get('base_path') == '/tmp/日本語フォルダ'

    def test_config_merge_complex(self, tmp_path):
        """Test complex configuration merging."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
dashboard:
  enabled: true
  port: 9000
sync:
  enabled: true
  interval: 7200
""")
        
        config = EmailToolConfig(config_path=config_file)
        assert config.get('dashboard.enabled') is True
        assert config.get('dashboard.port') == 9000
        assert config.get('sync.enabled') is True
        assert config.get('sync.interval') == 7200
