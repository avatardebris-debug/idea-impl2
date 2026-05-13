"""Example: Full optimisation pipeline.

Demonstrates loading a roster and free agent pool from JSON files,
running the optimiser, and printing the results.

Usage::

    python examples/optimize_roster.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the workspace root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ffo.api import optimize, generate_report


def main() -> None:
    # Create sample data for demonstration
    roster_data = [
        {"name": "Player A", "position": "FWD", "overall_rating": 85.0,
         "age": 28, "contract_length": 3, "salary": 15000000, "value": 70000000},
        {"name": "Player B", "position": "MID", "overall_rating": 80.0,
         "age": 31, "contract_length": 2, "salary": 12000000, "value": 50000000},
        {"name": "Player C", "position": "DEF", "overall_rating": 75.0,
         "age": 26, "contract_length": 4, "salary": 8000000, "value": 40000000},
    ]

    pool_data = [
        {"name": "Agent X", "position": "FWD", "overall_rating": 90.0,
         "age": 24, "contract_length": 5, "salary": 18000000, "value": 80000000,
         "available": True, "agent_name": "EliteAgents", "preferred_positions": ["FWD"]},
        {"name": "Agent Y", "position": "MID", "overall_rating": 82.0,
         "age": 27, "contract_length": 3, "salary": 10000000, "value": 45000000,
         "available": True, "agent_name": "EliteAgents", "preferred_positions": ["MID"]},
        {"name": "Agent Z", "position": "GK", "overall_rating": 78.0,
         "age": 30, "contract_length": 2, "salary": 5000000, "value": 25000000,
         "available": True, "agent_name": "GoalKeepers Inc", "preferred_positions": ["GK"]},
    ]

    # Write temporary files
    roster_path = Path("tmp_roster.json")
    pool_path = Path("tmp_pool.json")

    with open(roster_path, "w") as f:
        json.dump(roster_data, f, indent=2)
    with open(pool_path, "w") as f:
        json.dump(pool_data, f, indent=2)

    try:
        # Run optimisation
        cap = 50000000  # $50M cap
        report = generate_report(
            roster_path=roster_path,
            pool_path=pool_path,
            cap=cap,
            age_weight=1.0,
            contract_weight=1.0,
        )

        print("=" * 60)
        print("FFO Optimisation Report")
        print("=" * 60)
        print(f"Salary Cap:          ${report['cap_limit']:,.0f}")
        print(f"Original Payroll:    ${report['original_payroll']:,.0f}")
        print(f"Optimized Payroll:   ${report['optimized_payroll']:,.0f}")
        print(f"Remaining Budget:    ${report['remaining_budget']:,.0f}")
        print(f"Original Value:      {report['original_value']:,.2f}")
        print(f"Optimized Value:     {report['optimized_value']:,.2f}")
        print(f"Value Improvement:   {report['optimized_value'] - report['original_value']:,.2f}")
        print()
        print("Players Added:")
        for name in report["players_added"]:
            print(f"  + {name}")
        print("Players Removed:")
        for name in report["players_removed"]:
            print(f"  - {name}")
        print()
        print("Optimized Roster:")
        for p in report["optimized_roster"]:
            print(f"  {p['name']:15s}  {p['position']:3s}  "
                  f"Rating: {p['overall_rating']:5.1f}  "
                  f"Salary: ${p['salary']:>10,.0f}")
        print("=" * 60)

        # Save report
        save_path = Path("optimization_report.json")
        from ffo.api import save_report
        save_report(report, save_path)
        print(f"\nReport saved to {save_path}")

    finally:
        # Cleanup
        roster_path.unlink(missing_ok=True)
        pool_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
