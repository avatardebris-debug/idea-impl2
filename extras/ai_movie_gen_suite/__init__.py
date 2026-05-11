"""AI Movie Generation Suite — Generate feature-length screenplays with AI."""

from ai_movie_gen_suite import models
from ai_movie_gen_suite.config import AppConfig
from ai_movie_gen_suite.project_manager import create_project, run_full_pipeline

__version__ = "0.1.0"
__all__ = ["models", "AppConfig", "create_project", "run_full_pipeline"]
