"""
conftest.py — Pytest configuration for the OSINT Corp2 pipeline tests.
"""
import pathlib
import sys

# Add workspace to path for all tests
sys.path.insert(0, str(pathlib.Path(__file__).parent))
