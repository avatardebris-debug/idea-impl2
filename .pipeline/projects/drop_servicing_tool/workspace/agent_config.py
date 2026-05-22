"""
Agent configuration for multi-agent SOP execution.

Defines per-step model configurations and provides presets for common use cases.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProviderType(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    LOCAL = "local"


class AgentMode(str, Enum):
    """Predefined agent mode presets."""
    AUTO = "auto"
    STEP = "step"
    FREEFORM = "freeform"
    FAST = "fast"
    BALANCED = "balanced"
    QUALITY = "quality"


@dataclass
class AgentConfig:
    """Configuration for a single agent/model step."""
    provider: Optional[ProviderType] = None
    model: Optional[str] = None
    mode: AgentMode = AgentMode.AUTO
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt_override: Optional[str] = None
    fallback_models: list = field(default_factory=list)

    def __post_init__(self):
        """Validate configuration."""
        if not self.provider:
            raise ValueError("Provider is required")
        if not self.model:
            raise ValueError("Model is required")
        if not (0.0 <= self.temperature <= 1.0):
            raise ValueError("Temperature must be between 0 and 1")
        # Validate mode is a valid AgentMode
        if not isinstance(self.mode, AgentMode):
            try:
                self.mode = AgentMode(self.mode)
            except ValueError:
                raise ValueError(f"Invalid mode: {self.mode}. Must be one of: {', '.join([m.value for m in AgentMode])}")

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "mode": self.mode.value,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt_override": self.system_prompt_override,
            "fallback_models": self.fallback_models,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        """Deserialize from dictionary."""
        return cls(
            provider=ProviderType(data["provider"]),
            model=data["model"],
            mode=AgentMode(data.get("mode", "auto")),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens"),
            system_prompt_override=data.get("system_prompt_override"),
            fallback_models=data.get("fallback_models", []),
        )

    @classmethod
    def from_yaml(cls, data: dict) -> "AgentConfig":
        """Deserialize from YAML data."""
        return cls.from_dict(data)

    def __getitem__(self, key):
        """Support dict-like access for compatibility."""
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Support dict-like assignment."""
        setattr(self, key, value)

    def __contains__(self, key):
        """Support 'in' operator."""
        return hasattr(self, key)

    def get(self, key, default=None):
        """Support dict-like .get() access."""
        if hasattr(self, key):
            return getattr(self, key)
        return default


@dataclass
class AgentConfigList:
    """Manages per-step agent configurations for an SOP."""
    fast: AgentConfig = field(default=None)
    balanced: AgentConfig = field(default=None)
    quality: AgentConfig = field(default=None)
    configs: list = field(default_factory=list)
    _explicit_configs: bool = field(default=False, repr=False, init=False)

    def __post_init__(self):
        # Track if configs were explicitly provided (non-empty list)
        if self.configs:
            self._explicit_configs = True
        
        # Set up default configs if not provided
        if self.fast is None:
            self.fast = AgentConfig(
                provider=ProviderType.OLLAMA,
                model="llama3.2:1b",
                temperature=0.3,
                max_tokens=512,
            )
        if self.balanced is None:
            self.balanced = AgentConfig(
                provider=ProviderType.OPENAI,
                model="gpt-4o-mini",
                temperature=0.5,
                max_tokens=1024,
            )
        if self.quality is None:
            self.quality = AgentConfig(
                provider=ProviderType.ANTHROPIC,
                model="claude-3-5-sonnet-20241022",
                temperature=0.2,
                max_tokens=2048,
            )
        
        # Only populate configs with defaults if explicitly requested via fast/balanced/quality fields
        # If configs list is empty and no explicit configs were provided, keep it empty
        # The fast/balanced/quality attributes are available as fallback defaults

    def add_config(self, step_index: int, config: AgentConfig):
        """Add or update config for a specific step."""
        while len(self.configs) <= step_index:
            self.configs.append(None)
        self.configs[step_index] = config

    def get_config(self, step_index: int) -> Optional[AgentConfig]:
        """Get config for a specific step."""
        if step_index < len(self.configs):
            return self.configs[step_index]
        return None

    def get_config_by_provider(self, provider: ProviderType) -> AgentConfig:
        """Get config by provider type.
        
        Args:
            provider: The provider type to search for.
            
        Returns:
            AgentConfig for the specified provider.
            
        Raises:
            KeyError: If no config found for the specified provider.
        """
        for config in self.configs:
            if config and config.provider == provider:
                return config
        raise KeyError(f"No config found for provider: {provider.value}")

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            str(i): config.to_dict() if config else None
            for i, config in enumerate(self.configs)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfigList":
        """Deserialize from dictionary."""
        configs = []
        for key in sorted(data.keys(), key=int):
            value = data[key]
            if value is None:
                configs.append(None)
            else:
                configs.append(AgentConfig.from_dict(value))
        result = cls()
        result.configs = configs
        result._explicit_configs = True
        return result

    @classmethod
    def from_yaml(cls, data: dict) -> "AgentConfigList":
        """Deserialize from YAML data."""
        return cls.from_dict(data)


def get_preset(mode: str | AgentMode) -> AgentConfig:
    """Get default agent configs for a preset mode.
    
    Args:
        mode: Either an AgentMode enum value or a string.
              Can be: "fast", "balanced", "quality", or provider names like "openai", "anthropic", etc.
    
    Returns:
        AgentConfig object with preset configuration.
    
    Raises:
        ValueError: If mode is not recognized.
    """
    # Handle provider name presets directly
    if isinstance(mode, str):
        provider_presets = {
            "openai": AgentConfig(
                provider=ProviderType.OPENAI,
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=512,
            ),
            "anthropic": AgentConfig(
                provider=ProviderType.ANTHROPIC,
                model="claude-3-5-sonnet-20241022",
                temperature=0.5,
                max_tokens=1024,
            ),
            "gemini": AgentConfig(
                provider=ProviderType.GEMINI,
                model="gemini-1.5-pro",
                temperature=0.2,
                max_tokens=2048,
            ),
            "ollama": AgentConfig(
                provider=ProviderType.OLLAMA,
                model="llama3.2:1b",
                temperature=0.3,
                max_tokens=512,
            ),
        }
        if mode.lower() in provider_presets:
            return provider_presets[mode.lower()]
        
        # Try to match to AgentMode enum
        try:
            mode = AgentMode(mode)
        except Exception:
            raise KeyError(f"Unknown preset: {mode}. Choose from: fast, balanced, quality, openai, anthropic, gemini, ollama, auto, step, freeform")
    
    presets = {
        AgentMode.AUTO: AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=512,
        ),
        AgentMode.STEP: AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=512,
        ),
        AgentMode.FREEFORM: AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=512,
        ),
        AgentMode.FAST: AgentConfig(
            provider=ProviderType.OLLAMA,
            model="llama3.2:1b",
            temperature=0.3,
            max_tokens=512,
        ),
        AgentMode.BALANCED: AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=1024,
        ),
        AgentMode.QUALITY: AgentConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            temperature=0.2,
            max_tokens=2048,
        ),
    }
    return presets[mode]
