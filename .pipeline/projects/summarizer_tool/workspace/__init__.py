"""Summarizer Tool - A CLI tool for summarizing various content sources.

This package provides functionality to summarize PDFs, YouTube videos, and web pages.
"""

__version__ = "1.0.0"

from summarizer_tool.sources.pdf_summarizer import PDFSummarizer
from summarizer_tool.sources.youtube_summarizer import YouTubeSummarizer
from summarizer_tool.sources.web_summarizer import WebSummarizer

__all__ = ['PDFSummarizer', 'YouTubeSummarizer', 'WebSummarizer']
