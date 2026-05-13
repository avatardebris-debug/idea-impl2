"""Public API for FFO — Football Financial Optimizer.

This module exposes a clean, documented public API for programmatic use.
Import it as::

    from ffo.api import optimize, load_roster_from_json, load_pool_from_json, generate_report

All functions accept keyword arguments and return plain Python types (dicts, lists,
strings) so they can be used in scripts, notebooks, or web services.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ffo.io_utils import load_json as _load_json, save_json as _save_json
from ffo.models.player import Player, FreeAgent
from ffo.models.salary_cap import SalaryCap
from ffo.models.free_agent_pool import FreeAgentPool
from ffo.models.valuation import value_player, rank_by_efficiency
from ffo.optimizer import optimize_roster


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def load_roster_from_json(path: str | Path) -> list[dict[str, Any]]:
    """Load a roster from a JSON file.

    Args:
        path: Path to a JSON file containing a list of player dicts.

    Returns:
        List of player dictionaries.

    Raises:
        IOError: If the file does not exist or contains invalid JSON.
    """
    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError("Roster file must contain a JSON array of player objects.")
    return data


def load_pool_from_json(path: str | Path) -> list[dict[str, Any]]:
    """Load a free agent pool from a JSON file.

    Args:
        path: Path to a JSON file containing a list of free agent dicts.

    Returns:
        List of free agent dictionaries.

    Raises:
        IOError: If the file does not exist or contains invalid JSON.
    """
    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError("Pool file must contain a JSON array of free agent objects.")
    return data


# ---------------------------------------------------------------------------
# High-level optimisation
# ---------------------------------------------------------------------------

def optimize(
    roster_path: str | Path,
    pool_path: str | Path,
    cap: float,
    age_weight: float = 1.0,
    contract_weight: float = 1.0,
) -> list[dict[str, Any]]:
    """Run the full optimisation pipeline from file paths.

    This is the simplest entry point: give it two JSON files and a salary cap,
    and it returns the optimised roster as a list of player dicts.

    Args:
        roster_path: Path to the current roster JSON file.
        pool_path: Path to the free agent pool JSON file.
        cap: Salary cap limit in dollars.
        age_weight: Weight for the age factor in valuation (default 1.0).
        contract_weight: Weight for the contract factor in valuation (default 1.0).

    Returns:
        List of player dictionaries representing the optimised roster.

    Raises:
        ValueError: If inputs are invalid.
        IOError: If files cannot be read.
    """
    roster_data = load_roster_from_json(roster_path)
    pool_data = load_pool_from_json(pool_path)

    roster = [Player(**p) for p in roster_data]
    agents = [FreeAgent(**a) for a in pool_data]

    cap_obj = SalaryCap(cap_limit=cap)
    pool = FreeAgentPool(agents)

    optimized = optimize_roster(
        roster=roster,
        cap=cap_obj,
        pool=pool,
        age_weight=age_weight,
        contract_weight=contract_weight,
    )

    return [p.to_dict() for p in optimized]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def generate_report(
    roster_path: str | Path,
    pool_path: str | Path,
    cap: float,
    age_weight: float = 1.0,
    contract_weight: float = 1.0,
) -> dict[str, Any]:
    """Run optimisation and return a summary report.

    Args:
        roster_path: Path to the current roster JSON file.
        pool_path: Path to the free agent pool JSON file.
        cap: Salary cap limit in dollars.
        age_weight: Weight for the age factor in valuation (default 1.0).
        contract_weight: Weight for the contract factor in valuation (default 1.0).

    Returns:
        A dictionary with keys:
            - ``original_roster``: list of player dicts (before optimisation)
            - ``optimized_roster``: list of player dicts (after optimisation)
            - ``original_value``: total value score of the original roster
            - ``optimized_value``: total value score of the optimised roster
            - ``original_payroll``: total payroll of the original roster
            - ``optimized_payroll``: total payroll of the optimised roster
            - ``cap_limit``: the salary cap limit
            - ``remaining_budget``: remaining budget after optimisation
            - ``players_added``: list of player names added
            - ``players_removed``: list of player names removed
    """
    roster_data = load_roster_from_json(roster_path)
    pool_data = load_pool_from_json(pool_path)

    original_roster = [Player(**p) for p in roster_data]
    agents = [FreeAgent(**a) for a in pool_data]

    cap_obj = SalaryCap(cap_limit=cap)
    pool = FreeAgentPool(agents)

    # Original stats
    original_value = sum(value_player(p, age_weight, contract_weight) for p in original_roster)
    original_payroll = sum(p.salary for p in original_roster)

    # Optimise
    optimized = optimize_roster(
        roster=original_roster,
        cap=cap_obj,
        pool=pool,
        age_weight=age_weight,
        contract_weight=contract_weight,
    )

    optimized_value = sum(value_player(p, age_weight, contract_weight) for p in optimized)
    optimized_payroll = sum(p.salary for p in optimized)

    orig_names = {p.name for p in original_roster}
    opt_names = {p.name for p in optimized}

    return {
        "original_roster": [p.to_dict() for p in original_roster],
        "optimized_roster": [p.to_dict() for p in optimized],
        "original_value": original_value,
        "optimized_value": optimized_value,
        "original_payroll": original_payroll,
        "optimized_payroll": optimized_payroll,
        "cap_limit": cap,
        "remaining_budget": cap - optimized_payroll,
        "players_added": list(opt_names - orig_names),
        "players_removed": list(orig_names - opt_names),
    }


# ---------------------------------------------------------------------------
# Convenience: save report to JSON
# ---------------------------------------------------------------------------

def save_report(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    """Save an optimisation report to a JSON file.

    Args:
        report: Report dictionary (output of :func:`generate_report`).
        path: Destination file path.
    """
    _save_json(report, path)
