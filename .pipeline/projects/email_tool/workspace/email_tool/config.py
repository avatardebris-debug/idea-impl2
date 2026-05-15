"""Configuration loader for Email Tool.

This module provides configuration loading from YAML files and environment variables.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from email_tool.logging_config import setup_logging, get_logger
from email_tool.models import Rule, RuleType

logger = get_logger(__name__)


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    
    def __init__(self, message: str, file: Optional[str] = None, line: Optional[int] = None):
        super().__init__(message)
        self.file = file
        self.line = line
        self.message = message
    
    def __str__(self):
        parts = [self.message]
        if self.file:
            parts.append(f"file: {self.file}")
        if self.line:
            parts.append(f"line {self.line}")
        return " | ".join(parts)


class EmailToolConfig:
    """Main configuration class for Email Tool.
    
    Loads configuration from YAML file and environment variables.
    Provides a unified interface for all configuration values.
    """
    
    DEFAULT_CONFIG_DIR = Path.home() / ".email_tool"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file and merge with environment variables."""
        # Load from YAML file
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                logger.debug(f"Loaded config from {self.config_path}")
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML config: {e}")
                file_config = {}
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
                file_config = {}
        else:
            logger.debug(f"Config file not found: {self.config_path}")
            file_config = {}
        
        # Load from environment variables
        env_config = self._load_from_env()
        
        # Merge configurations (file takes precedence over env)
        self.config = self._merge_configs(env_config, file_config)
        
        # Apply defaults
        self._apply_defaults()
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config: Dict[str, Any] = {}
        
        # Log level
        log_level = os.getenv('EMAIL_TOOL_LOG_LEVEL')
        if log_level:
            env_config['log_level'] = log_level
        
        # Log file
        log_file = os.getenv('EMAIL_TOOL_LOG_FILE')
        if log_file:
            env_config['log_file'] = log_file
        
        # Base path
        base_path = os.getenv('EMAIL_TOOL_BASE_PATH')
        if base_path:
            env_config['base_path'] = base_path
        
        # Output format
        output_format = os.getenv('EMAIL_TOOL_OUTPUT_FORMAT')
        if output_format:
            env_config['output_format'] = output_format
        
        # Dashboard settings
        dashboard_enabled = os.getenv('EMAIL_TOOL_DASHBOARD_ENABLED')
        if dashboard_enabled:
            if 'dashboard' not in env_config:
                env_config['dashboard'] = {}
            env_config['dashboard']['enabled'] = dashboard_enabled.lower() == 'true'
        
        dashboard_port = os.getenv('EMAIL_TOOL_DASHBOARD_PORT')
        if dashboard_port:
            if 'dashboard' not in env_config:
                env_config['dashboard'] = {}
            env_config['dashboard']['port'] = int(dashboard_port)
        
        return env_config
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries.
        
        Args:
            base: Base configuration.
            override: Override configuration (takes precedence).
        
        Returns:
            Merged configuration.
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_defaults(self):
        """Apply default values for missing configuration."""
        defaults = {
            'log_level': 'INFO',
            'log_file': None,
            'base_path': str(Path.home() / "email_organized"),
            'output_format': 'eml',
            'collision_strategy': 'rename',
            'dashboard': {
                'enabled': False,
                'port': 8000
            },
            'sync': {
                'enabled': False,
                'interval': 3600,  # 1 hour
                'sources': []
            },
            'rules': {
                'path': None
            }
        }
        
        self.config = self._merge_configs(defaults, self.config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation for nested keys).
            default: Default value if key not found.
        
        Returns:
            Configuration value.
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_log_level(self) -> str:
        """Get log level configuration."""
        return self.get('log_level', 'INFO')
    
    def get_log_file(self) -> Optional[str]:
        """Get log file path configuration."""
        return self.get('log_file')
    
    def get_base_path(self) -> str:
        """Get base path for organized emails."""
        return self.get('base_path', str(Path.home() / "email_organized"))
    
    def get_output_format(self) -> str:
        """Get output format configuration."""
        return self.get('output_format', 'eml')
    
    def get_collision_strategy(self) -> str:
        """Get collision handling strategy."""
        return self.get('collision_strategy', 'rename')
    
    def get_dashboard_enabled(self) -> bool:
        """Get dashboard enabled status."""
        return self.get('dashboard.enabled', False)
    
    def get_dashboard_port(self) -> int:
        """Get dashboard port."""
        return self.get('dashboard.port', 8000)
    
    def get_sync_enabled(self) -> bool:
        """Get sync enabled status."""
        return self.get('sync.enabled', False)
    
    def get_sync_interval(self) -> int:
        """Get sync interval in seconds."""
        return self.get('sync.interval', 3600)
    
    def get_sync_sources(self) -> List[str]:
        """Get sync sources."""
        return self.get('sync.sources', [])
    
    def get_rules_path(self) -> Optional[str]:
        """Get rules file path."""
        return self.get('rules.path')
    
    def setup_logging(self):
        """Set up logging based on configuration."""
        log_level = self.get_log_level()
        log_file = self.get_log_file()
        
        setup_logging(
            log_level=log_level,
            log_file=log_file,
            console_output=True,
            use_colors=True
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.config.copy()
    
    def save(self, path: Optional[Path] = None):
        """Save configuration to YAML file.
        
        Args:
            path: Path to save configuration. If None, uses config_path.
        """
        save_path = path or self.config_path
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to {save_path}")


def load_config(config_path: Optional[Path] = None) -> EmailToolConfig:
    """Load configuration from file.
    
    Args:
        config_path: Path to configuration file. If None, uses default location.
    
    Returns:
        EmailToolConfig instance.
    """
    return EmailToolConfig(config_path)


# == Rule Configuration Functions ==

def validate_rule_config(rule_data: Dict[str, Any], rule_name: str = "unnamed_rule") -> List[str]:
    """Validate a single rule configuration.
    
    Args:
        rule_data: Dictionary containing rule configuration.
        rule_name: Name of the rule for error messages.
    
    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    
    # Check for required fields
    if "name" not in rule_data:
        errors.append(f"Rule '{rule_name}': missing required field 'name'")
    elif not rule_data.get("name", "").strip():
        errors.append(f"Rule '{rule_name}': name cannot be empty")
    
    if "type" not in rule_data:
        errors.append(f"Rule '{rule_name}': missing required field 'type'")
    elif rule_data.get("type") not in [rt.value for rt in RuleType]:
        errors.append(f"Rule '{rule_name}': invalid rule type '{rule_data.get('type')}'")
    
    # Check pattern for pattern-based rules
    pattern_required_types = [
        RuleType.FROM_EXACT.value, RuleType.FROM_PATTERN.value,
        RuleType.SUBJECT_EXACT.value, RuleType.SUBJECT_PATTERN.value,
        RuleType.BODY_CONTAINS_EXACT.value, RuleType.BODY_CONTAINS_PATTERN.value
    ]
    
    if rule_data.get("type") in pattern_required_types:
        if "pattern" not in rule_data:
            errors.append(f"Rule '{rule_name}': missing required field 'pattern'")
        elif rule_data.get("type") in [RuleType.FROM_PATTERN.value, RuleType.SUBJECT_PATTERN.value, RuleType.BODY_CONTAINS_PATTERN.value]:
            # Validate regex pattern
            try:
                re.compile(rule_data.get("pattern", ""))
            except re.error as e:
                errors.append(f"Rule '{rule_name}': invalid regex pattern: {e}")
    
    # Validate priority
    if "priority" in rule_data:
        priority = rule_data.get("priority")
        if not isinstance(priority, int):
            errors.append(f"Rule '{rule_name}': priority must be an integer")
        elif priority < 0 or priority > 100:
            errors.append(f"Rule '{rule_name}': priority must be between 0 and 100")
    
    return errors


def _parse_rule(rule_data: Dict[str, Any], rule_name: str = "unnamed_rule") -> Rule:
    """Parse a rule configuration into a Rule object.
    
    Args:
        rule_data: Dictionary containing rule configuration.
        rule_name: Name of the rule.
    
    Returns:
        Rule object.
    """
    rule_type_str = rule_data.get("type", "from_exact")
    try:
        rule_type = RuleType(rule_type_str)
    except ValueError:
        # This should not happen if validation is done first
        rule_type = RuleType.FROM_EXACT
    
    return Rule(
        name=rule_data.get("name", rule_name),
        rule_type=rule_type,
        pattern=rule_data.get("pattern", ""),
        priority=rule_data.get("priority", 50),
        category=rule_data.get("category", "general"),
        description=rule_data.get("description", "")
    )


def load_rules_from_dict(rules_dict: Dict[str, Any]) -> List[Rule]:
    """Load rules from a dictionary.
    
    Args:
        rules_dict: Dictionary containing rules under 'rules' key.
    
    Returns:
        List of Rule objects.
    """
    rules = []
    rules_list = rules_dict.get("rules", [])
    
    for i, rule_data in enumerate(rules_list):
        rule_name = rule_data.get("name", f"rule_{i+1}")
        errors = validate_rule_config(rule_data, rule_name)
        
        if not errors:
            rule = _parse_rule(rule_data, rule_name)
            rules.append(rule)
        else:
            logger.warning(f"Skipping invalid rule '{rule_name}': {'; '.join(errors)}")
    
    return rules


def load_rules_from_yaml(yaml_path: str) -> List[Rule]:
    """Load rules from a YAML file.
    
    Args:
        yaml_path: Path to YAML file.
    
    Returns:
        List of Rule objects.
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            rules_dict = yaml.safe_load(f) or {}
        return load_rules_from_dict(rules_dict)
    except FileNotFoundError:
        logger.warning(f"Rules file not found: {yaml_path}")
        return []
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse YAML file {yaml_path}: {e}")
        return []
    except Exception as e:
        logger.warning(f"Failed to load rules from {yaml_path}: {e}")
        return []


def validate_rule_config_file(yaml_path: str) -> List[str]:
    """Validate a rules configuration file.
    
    Args:
        yaml_path: Path to YAML file.
    
    Returns:
        List of error messages.
    """
    errors = []
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            rules_dict = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return [f"File not found: {yaml_path}"]
    except yaml.YAMLError as e:
        return [f"YAML parsing error: {e}"]
    except Exception as e:
        return [f"Failed to read file: {e}"]
    
    rules_list = rules_dict.get("rules", [])
    
    for i, rule_data in enumerate(rules_list):
        rule_name = rule_data.get("name", f"rule_{i+1}")
        rule_errors = validate_rule_config(rule_data, rule_name)
        errors.extend(rule_errors)
    
    return errors
