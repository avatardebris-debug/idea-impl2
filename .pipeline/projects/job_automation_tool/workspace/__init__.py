"""Job Automation Tool - Job description parsing and profile matching."""

from .profile import Profile
from .parser import parse_job_description
from .matcher import match_profiles

__all__ = ["Profile", "parse_job_description", "match_profiles"]
__version__ = "0.1.0"
