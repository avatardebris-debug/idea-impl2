"""Example: CLI usage.

Demonstrates using the FFO command-line interface with sample data files.

Usage::

    # Create sample data files
    python examples/create_sample_data.py

    # Run optimisation via CLI
    python -m ffo.cli optimize --roster sample_roster.json --pool sample_pool.json --cap 100000000

    # Generate a report
    python -m ffo.cli report --roster sample_roster.json --pool sample_pool.json --cap 100000000 --output report.json
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ffo.cli import main as cli_main


if __name__ == "__main__":
    cli_main()
