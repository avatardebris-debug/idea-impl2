"""Configuration management for the AI Movie Generation Suite.

Provides LLMConfig and AppConfig with JSON persistence.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class LLMConfig(BaseModel):
    """Configuration for an LLM provider.

    Attributes:
        provider: LLM provider ('openai' or 'anthropic').
        api_key: API key for the provider.
        model: Model name to use.
        use_json_mode: Whether to enforce JSON output mode.
        temperature: Sampling temperature (0.0-2.0).
        max_tokens: Maximum tokens in the response.
        base_url: Optional custom base URL for the API.
    """

    provider: str = Field(default="openai", description="LLM provider (openai or anthropic)")
    api_key: str = Field(default="", description="API key for the provider")
    model: str = Field(default="gpt-4o", description="Model name to use")
    use_json_mode: bool = Field(default=True, description="Enforce JSON output mode")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=4096, ge=1, description="Maximum tokens in response")
    base_url: Optional[str] = Field(None, description="Custom base URL for the API")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        valid = ("openai", "anthropic")
        if v.lower() not in valid:
            raise ValueError(f"Provider must be one of {valid}, got '{v}'")
        return v.lower()

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary."""
        return {
            "provider": self.provider,
            "api_key": self.api_key,
            "model": self.model,
            "use_json_mode": self.use_json_mode,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "base_url": self.base_url,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert config to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LLMConfig:
        """Create config from a dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> LLMConfig:
        """Create config from a JSON string."""
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Create config from environment variables."""
        return cls(
            provider=os.environ.get("FIVERR_LLM_PROVIDER", "openai"),
            api_key=os.environ.get("FIVERR_LLM_API_KEY", ""),
            model=os.environ.get("FIVERR_LLM_MODEL", "gpt-4o"),
            use_json_mode=os.environ.get("FIVERR_LLM_USE_JSON_MODE", "true").lower() == "true",
            temperature=float(os.environ.get("FIVERR_LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.environ.get("FIVERR_LLM_MAX_TOKENS", "4096")),
            base_url=os.environ.get("FIVERR_LLM_BASE_URL"),
        )


class AppConfig(BaseModel):
    """Application configuration for the AI Movie Generation Suite.

    Attributes:
        llm: LLM configuration.
        output_dir: Directory for output files.
        log_level: Logging level.
        max_retries: Maximum retry attempts for API calls.
        retry_delay: Delay between retries in seconds.
        enable_cache: Whether to enable response caching.
        cache_ttl: Cache time-to-live in seconds.
    """

    llm: LLMConfig = Field(default_factory=LLMConfig)
    output_dir: str = Field(default="./output", description="Directory for output files")
    log_level: str = Field(default="INFO", description="Logging level")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.0, description="Delay between retries in seconds")
    enable_cache: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, ge=0, description="Cache TTL in seconds")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if v.upper() not in valid:
            raise ValueError(f"Log level must be one of {valid}, got '{v}'")
        return v.upper()

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary."""
        return {
            "llm": self.llm.to_dict(),
            "output_dir": self.output_dir,
            "log_level": self.log_level,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "enable_cache": self.enable_cache,
            "cache_ttl": self.cache_ttl,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert config to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AppConfig:
        """Create config from a dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> AppConfig:
        """Create config from a JSON string."""
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def from_env(cls) -> AppConfig:
        """Create config from environment variables."""
        llm = LLMConfig.from_env()
        return cls(
            llm=llm,
            output_dir=os.environ.get("FIVERR_OUTPUT_DIR", "./output"),
            log_level=os.environ.get("FIVERR_LOG_LEVEL", "INFO"),
            max_retries=int(os.environ.get("FIVERR_MAX_RETRIES", "3")),
            retry_delay=float(os.environ.get("FIVERR_RETRY_DELAY", "1.0")),
            enable_cache=os.environ.get("FIVERR_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl=int(os.environ.get("FIVERR_CACHE_TTL", "3600")),
        )

    def save(self, filepath: str) -> None:
        """Save config to a JSON file."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> AppConfig:
        """Load config from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)


def get_default_config() -> AppConfig:
    """Get default application configuration."""
    return AppConfig()
