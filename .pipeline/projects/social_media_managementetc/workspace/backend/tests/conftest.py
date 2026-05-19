"""conftest.py — ensure 'backend/' is on sys.path for all tests."""
import sys
from pathlib import Path

# Insert the backend directory so `from app.X` imports resolve correctly
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
