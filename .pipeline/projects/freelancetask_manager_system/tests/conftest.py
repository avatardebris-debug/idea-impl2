"""Pytest configuration — ensures workspace is on sys.path."""

import sys
import os

# Add the workspace directory to the Python path
workspace = os.path.join(os.path.dirname(__file__), "..", "workspace")
workspace = os.path.abspath(workspace)
if workspace not in sys.path:
    sys.path.insert(0, workspace)
