#!/usr/bin/env python3
"""Monitoring script for the RL dropshipping system."""

import argparse
import json
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rl_dropshipping.src.monitoring import MonitoringDashboard, AlertLevel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_dashboard() -> MonitoringDashboard:
    """Create a monitoring dashboard with default metrics."""
    dashboard = MonitoringDashboard()

    # Register default metrics
    dashboard.register_metric("prediction_latency", window_seconds=3600)
    dashboard.register_metric("reward", window_seconds=3600)
    dashboard.register_metric("inventory_turnover", window_seconds=86400)
    dashboard.register_metric("ad_spend", window_seconds=3600)

    # Set thresholds
    dashboard.set_threshold("prediction_latency", upper=0.5)
    dashboard.set_threshold("reward", lower=-10.0)
    dashboard.set_threshold("ad_spend", upper=1000.0)

    return dashboard


def record_sample_metrics(dashboard: MonitoringDashboard) -> None:
    """Record sample metrics for demonstration."""
    import random

    dashboard.record_metric("prediction_latency", random.uniform(0.01, 0.8))
    dashboard.record_metric("reward", random.uniform(-5.0, 15.0))
    dashboard.record_metric("inventory_turnover", random.uniform(0.5, 3.0))
    dashboard.record_metric("ad_spend", random.uniform(100.0, 1200.0))


def print_dashboard(dashboard: MonitoringDashboard) -> None:
    """Print the dashboard summary."""
    summary = dashboard.get_dashboard_summary()

    print("\n" + "=" * 60)
    print("RL DROP SHIPPING MONITORING DASHBOARD")
    print("=" * 60)

    print(f"\nKill Switch: {'ACTIVE' if summary['kill_switch_active'] else 'OK'}")
    print(f"Total Alerts: {summary['total_alerts']}")
    print(f"Critical Alerts: {summary['critical_alerts']}")

    print("\nMetrics:")
    for name, stats in summary["metrics"].items():
        print(f"  {name}:")
        print(f"    Average: {stats['average']:.3f}")
        print(f"    Max: {stats['max']:.3f}")
        print(f"    Min: {stats['min']:.3f}")
        print(f"    Count: {stats['count']}")

    if summary["critical_alerts"] > 0:
        print("\n" + "!" * 60)
        print("CRITICAL ALERTS:")
        print("!" * 60)
        for alert in dashboard.get_alerts(AlertLevel.CRITICAL):
            print(f"  [{alert.timestamp}] {alert.metric}: {alert.value} "
                  f"(threshold: {alert.threshold})")
            print(f"    {alert.message}")

    print("\n" + "=" * 60)


def main() -> None:
    """Main monitoring loop."""
    parser = argparse.ArgumentParser(description="RL Dropshipping Monitor")
    parser.add_argument("--samples", type=int, default=10,
                        help="Number of sample metrics to record")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    dashboard = create_dashboard()

    # Record sample metrics
    for _ in range(args.samples):
        record_sample_metrics(dashboard)

    if args.json:
        print(json.dumps(dashboard.get_dashboard_summary(), indent=2))
    else:
        print_dashboard(dashboard)


if __name__ == "__main__":
    main()
