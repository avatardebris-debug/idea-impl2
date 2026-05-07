#!/usr/bin/env python3
"""CLI demo script for the DashboardDataSource.

Instantiates DashboardDataSource, starts it, and prints 20 metric
updates to stdout with correct formatting showing all three metric types.
"""

import sys
import time
from pathlib import Path

# Ensure the project root (workspace) is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# Also add current directory for relative imports
if "." not in sys.path:
    sys.path.insert(0, ".")

from src.dashboard.data_source import DashboardDataSource
from src.dashboard.models import DashboardState


def format_metric_update(update_num: int, state: DashboardState) -> str:
    """Format a single metric update for stdout display."""
    lines = [
        f"{'='*60}",
        f"  Update #{update_num:4d}  |  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(state.timestamp))}",
        f"{'='*60}",
        f"  Win Rate:       {state.win_rate.value:>8.4f}  "
        f"(wins={state.win_rate.wins:>4d} / "
        f"losses={state.win_rate.losses:>4d} / "
        f"total={state.win_rate.total_games:>4d})",
        f"  Bankroll:       {state.bankroll.bankroll:>10.2f}  "
        f"(peak={state.bankroll.peak_bankroll:>10.2f}, "
        f"drawdown={state.bankroll.drawdown:>8.4f})",
        f"  Nash Distance:  {state.nash_shift.distance:>8.4f}  "
        f"(strategy={state.nash_shift.current_strategy})",
        f"  Color Hint:     {state.win_rate.value > 0.5: <5} "
        f"(>0.5 = green, <0.5 = red, =0.5 = white)",
        f"{'='*60}",
    ]
    return "\n".join(lines)


def main() -> None:
    """Run the CLI demo: produce 20 metric updates."""
    print("\nDashboard Data Source CLI Demo")
    print("Producing 20 metric updates...\n")

    # Create data source with 0.5s interval
    source = DashboardDataSource(interval=0.5, initial_bankroll=1000.0, seed=42)

    # Collect updates
    updates: list[DashboardState] = []

    def on_update(payload: dict) -> None:
        state = DashboardState.from_dict(payload)
        updates.append(state)

    source.register_callback(on_update)
    source.start()

    # Force 20 updates
    for i in range(20):
        payload = source.force_update()
        state = DashboardState.from_dict(payload)
        print(format_metric_update(i + 1, state))
        time.sleep(0.1)  # small delay for realism

    source.stop()

    print("\nDemo complete. 20 metric updates produced.")


if __name__ == "__main__":
    main()
