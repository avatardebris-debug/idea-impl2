"""Universal LLM Router.

Provides fallback and load-balancing across multiple LLM clients.
"""
from .router import UniversalRouter, RouteConfig, RouteStrategy

__all__ = ["UniversalRouter", "RouteConfig", "RouteStrategy"]
