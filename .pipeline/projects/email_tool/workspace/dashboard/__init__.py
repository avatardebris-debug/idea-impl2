"""Dashboard package for Email Tool.

This package provides a web-based dashboard for monitoring email organization
statistics, recent activity, and system health.
"""

from email_tool.dashboard.app import create_app, Dashboard

__version__ = "0.1.0"
__all__ = ["create_app", "Dashboard"]
