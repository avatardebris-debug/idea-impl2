"""sacbot — Generate content in Scott Adams' distinctive writing style."""

from sacbot.generator import generate

# Phase 4 modules
from sacbot import topic_research
from sacbot import review
from sacbot import publishers
from sacbot import scheduler
from sacbot import dashboard
from sacbot import pipeline

__all__ = [
    "generate",
    "topic_research",
    "review",
    "publishers",
    "scheduler",
    "dashboard",
    "pipeline",
]
