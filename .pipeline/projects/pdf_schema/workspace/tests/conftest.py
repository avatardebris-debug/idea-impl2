"""conftest.py — ensure pdf_schema package is importable in tests."""
import sys
from pathlib import Path

# Workspace root sits one level above tests/
workspace = Path(__file__).resolve().parent.parent
if str(workspace) not in sys.path:
    sys.path.insert(0, str(workspace))
