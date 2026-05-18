"""Code Review Diff Summarizer.

Reads git diff output and summarizes changes.
"""
from .summarizer import summarize_diff

__all__ = ["summarize_diff"]
