"""Example: Programmatic API usage.

Demonstrates using the FFO API directly in Python code without JSON files.
Useful for notebooks, web services, or custom workflows.

Usage::

    python examples/programmatic_api.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ffo.models.player import Player, FreeAgent
from ffo.models.salary_cap import SalaryCap
from ffo.models.free_agent_pool import FreeAgentPool
from ffo.models.valuation import value_player, rank_by_efficiency
from ffo.optimizer import optimize_roster


def main() -> None:
    # Build a roster programmatically
    roster = [
        Player(name="Messi", position="FWD", overall_rating=95.0,
               age=36, contract_length=2, salary=50000000, value=80000000),
        Player(name="De Bruyne", position="MID", overall_rating=92.0,
               age=32, contract_length=3, salary=40000000, value=70000000),
        Player(name="Van Dijk", position="DEF", overall_rating=90.0,
               age=32, contract_length=4, salary=35000000, value=65000000),
        Player(name="Ederson", position="GK", overall_rating=88.0,
               age=30, contract_length=5, salary=25000000, value=50000000),
    ]

    # Build a free agent pool
    pool = FreeAgentPool([
        FreeAgent(name="Haaland", position="FWD", overall_rating=94.0,
                  age=23, contract_length=5, salary=45000000, value=90000000,
                  available=True, agent_name="EliteAgents", preferred_positions=["FWD"]),
        FreeAgent(name="Bellingham", position="MID", overall_rating=91.0,
                  age=20, contract_length=6, salary=35000000, value=85000000,
                  available=True, agent_name="TopTalent", preferred_positions=["MID"]),
        FreeAgent(name="Rice", position="MID", overall_rating=86.0,
                  age=25, contract_length=4, salary=28000000, value=55000000,
                  available=True, agent_name="TopTalent", preferred_positions=["MID"]),
        FreeAgent(name="Saliba", position="DEF", overall_rating=87.0,
                  age=22, contract_length=5, salary=22000000, value=60000000,
                  available=True, agent_name="DefensivePros", preferred_positions=["DEF"]),
        FreeAgent(name="Onana", position="GK", overall_rating=84.0,
                  age=27, contract_length=3, salary=18000000, value=40000000,
                  available=True, agent_name="GoalKeepers Inc", preferred_positions=["GK"]),
    ])

    # Set salary cap
    cap = SalaryCap(cap_limit=150000000)  # $150M cap

    print("Original Roster:")
    print("-" * 60)
    for p in roster:
        score = value_player(p)
        print(f"  {p.name:15s}  {p.position:3s}  "
              f"Rating: {p.overall_rating:5.1f}  "
              f"Salary: ${p.salary:>10,.0f}  "
              f"Value Score: {score:,.2f}")

    original_value = sum(value_player(p) for p in roster)
    original_payroll = sum(p.salary for p in roster)
    print(f"\nTotal Payroll: ${original_payroll:,.0f}")
    print(f"Total Value Score: {original_value:,.2f}")

    # Run optimisation
    optimized = optimize_roster(
        roster=roster,
        cap=cap,
        pool=pool,
        age_weight=1.0,
        contract_weight=1.0,
    )

    print("\n" + "=" * 60)
    print("Optimized Roster:")
    print("=" * 60)
    for p in optimized:
        score = value_player(p)
        print(f"  {p.name:15s}  {p.position:3s}  "
              f"Rating: {p.overall_rating:5.1f}  "
              f"Salary: ${p.salary:>10,.0f}  "
              f"Value Score: {score:,.2f}")

    optimized_value = sum(value_player(p) for p in optimized)
    optimized_payroll = sum(p.salary for p in optimized)

    print(f"\nTotal Payroll: ${optimized_payroll:,.0f}")
    print(f"Total Value Score: {optimized_value:,.2f}")
    print(f"Remaining Budget: ${cap.remaining:,.0f}")
    print(f"Value Improvement: {optimized_value - original_value:,.2f}")

    # Show top candidates from pool
    print("\n" + "=" * 60)
    print("Top 3 Free Agent Candidates (by value efficiency):")
    print("=" * 60)
    top_candidates = pool.get_top_candidates(n=3)
    for agent, score in top_candidates:
        print(f"  {agent.name:15s}  {agent.position:3s}  "
              f"Rating: {agent.overall_rating:5.1f}  "
              f"Salary: ${agent.salary:>10,.0f}  "
              f"Score: {score:,.2f}")


if __name__ == "__main__":
    main()
