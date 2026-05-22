"""
Project configuration for Transcript Extractor.

Contains settings for model paths, output directories, and API endpoints.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration class for Transcript Extractor settings."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        temp_dir: Optional[str] = None,
        api_endpoint: Optional[str] = None,
    ):
        """
        Initialize configuration.
        
        Args:
            model_path: Path to Whisper model files. Uses default if None.
            output_dir: Directory for output files. Uses current directory if None.
            temp_dir: Directory for temporary files. Uses system temp if None.
            api_endpoint: API endpoint for remote services. Uses local if None.
        """
        self.model_path = model_path or self._get_default_model_path()
        self.output_dir = output_dir or os.getcwd()
        self.temp_dir = temp_dir or self._get_temp_dir()
        self.api_endpoint = api_endpoint or "local"
        
        # Ensure directories exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_default_model_path(self) -> str:
        """Get default model path from environment or use default."""
        env_path = os.environ.get("TRANSCRIPT_EXTRACTOR_MODEL_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        return str(Path.home() / ".cache" / "transcript_extractor" / "models")
    
    def _get_temp_dir(self) -> str:
        """Get temporary directory for intermediate files."""
        return os.environ.get("TRANSCRIPT_EXTRACTOR_TEMP_DIR") or str(Path.home() / ".cache" / "transcript_extractor" / "temp")
    
    def get_output_path(self, filename: str) -> str:
        """Get full output path for a given filename."""
        return os.path.join(self.output_dir, filename)
    
    def get_temp_path(self, filename: str) -> str:
        """Get full temp path for a given filename."""
        return os.path.join(self.temp_dir, filename)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            model_path=os.environ.get("TRANSCRIPT_EXTRACTOR_MODEL_PATH"),
            output_dir=os.environ.get("TRANSCRIPT_EXTRACTOR_OUTPUT_DIR"),
            temp_dir=os.environ.get("TRANSCRIPT_EXTRACTOR_TEMP_DIR"),
            api_endpoint=os.environ.get("TRANSCRIPT_EXTRACTOR_API_ENDPOINT"),
        )
