"""Example: Create sample data files for testing.

Generates sample roster and free agent pool JSON files that can be used
with the CLI or the API.

Usage::

    python examples/create_sample_data.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    output_dir = Path(__file__).resolve().parent

    # Sample roster
    roster = [
        {
            "name": "Player A",
            "position": "FWD",
            "overall_rating": 85.0,
            "age": 28,
            "contract_length": 3,
            "salary": 15000000,
            "value": 70000000,
        },
        {
            "name": "Player B",
            "position": "MID",
            "overall_rating": 80.0,
            "age": 31,
            "contract_length": 2,
            "salary": 12000000,
            "value": 50000000,
        },
        {
            "name": "Player C",
            "position": "DEF",
            "overall_rating": 75.0,
            "age": 26,
            "contract_length": 4,
            "salary": 8000000,
            "value": 40000000,
        },
        {
            "name": "Player D",
            "position": "GK",
            "overall_rating": 78.0,
            "age": 30,
            "contract_length": 2,
            "salary": 6000000,
            "value": 30000000,
        },
    ]

    # Sample free agent pool
    pool = [
        {
            "name": "Agent X",
            "position": "FWD",
            "overall_rating": 90.0,
            "age": 24,
            "contract_length": 5,
            "salary": 18000000,
            "value": 80000000,
            "available": True,
            "agent_name": "EliteAgents",
            "preferred_positions": ["FWD"],
        },
        {
            "name": "Agent Y",
            "position": "MID",
            "overall_rating": 82.0,
            "age": 27,
            "contract_length": 3,
            "salary": 10000000,
            "value": 45000000,
            "available": True,
            "agent_name": "EliteAgents",
            "preferred_positions": ["MID"],
        },
        {
            "name": "Agent Z",
            "position": "DEF",
            "overall_rating": 86.0,
            "age": 25,
            "contract_length": 4,
            "salary": 14000000,
            "value": 55000000,
            "available": True,
            "agent_name": "TopTalent",
            "preferred_positions": ["DEF"],
        },
        {
            "name": "Agent W",
            "position": "GK",
            "overall_rating": 78.0,
            "age": 30,
            "contract_length": 2,
            "salary": 5000000,
            "value": 25000000,
            "available": True,
            "agent_name": "GoalKeepers Inc",
            "preferred_positions": ["GK"],
        },
    ]

    roster_path = output_dir / "sample_roster.json"
    pool_path = output_dir / "sample_pool.json"

    with open(roster_path, "w") as f:
        json.dump(roster, f, indent=2)
    print(f"Created {roster_path}")

    with open(pool_path, "w") as f:
        json.dump(pool, f, indent=2)
    print(f"Created {pool_path}")

    print("\nYou can now use these files with the CLI:")
    print(f"  python -m ffo.cli optimize --roster {roster_path} --pool {pool_path} --cap 50000000")


if __name__ == "__main__":
    main()
