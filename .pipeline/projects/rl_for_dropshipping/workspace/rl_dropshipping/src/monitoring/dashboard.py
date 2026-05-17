"""Monitoring module — tracks system health and triggers kill-switch."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    KILL_SWITCH = "kill_switch"


@dataclass
class Alert:
    """A monitoring alert."""
    level: AlertLevel
    metric: str
    value: float
    threshold: float
    message: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class MetricTracker:
    """Tracks a single metric over time."""

    def __init__(self, name: str, window_seconds: float = 3600.0):
        self.name = name
        self.window_seconds = window_seconds
        self._values: List[Dict[str, float]] = []

    def record(self, value: float) -> None:
        """Record a metric value."""
        self._values.append({"value": value, "timestamp": time.time()})
        self._cleanup()

    def _cleanup(self) -> None:
        """Remove old values outside the window."""
        cutoff = time.time() - self.window_seconds
        self._values = [v for v in self._values if v["timestamp"] >= cutoff]

    def get_average(self) -> float:
        """Get the average value in the current window."""
        if not self._values:
            return 0.0
        return sum(v["value"] for v in self._values) / len(self._values)

    def get_max(self) -> float:
        """Get the maximum value in the current window."""
        if not self._values:
            return 0.0
        return max(v["value"] for v in self._values)

    def get_min(self) -> float:
        """Get the minimum value in the current window."""
        if not self._values:
            return 0.0
        return min(v["value"] for v in self._values)

    def get_count(self) -> int:
        """Get the number of values in the current window."""
        return len(self._values)


class KillSwitch:
    """Emergency kill switch for the RL system.

    Can be triggered manually or automatically based on thresholds.
    """

    def __init__(self):
        self._active = False
        self._triggered_at: Optional[float] = None
        self._trigger_reason: str = ""
        self._history: List[Dict[str, Any]] = []

    @property
    def is_active(self) -> bool:
        """Check if the kill switch is active."""
        return self._active

    def trigger(self, reason: str) -> None:
        """Trigger the kill switch.

        Args:
            reason: Reason for triggering.
        """
        self._active = True
        self._triggered_at = time.time()
        self._trigger_reason = reason
        self._history.append({
            "event": "triggered",
            "reason": reason,
            "timestamp": time.time(),
        })
        logger.critical(f"KILL SWITCH TRIGGERED: {reason}")

    def reset(self) -> None:
        """Reset the kill switch (requires human confirmation)."""
        if self._active:
            self._history.append({
                "event": "reset",
                "timestamp": time.time(),
            })
        self._active = False
        self._triggered_at = None
        self._trigger_reason = ""
        logger.info("Kill switch reset")

    def get_status(self) -> Dict[str, Any]:
        """Get kill switch status."""
        return {
            "active": self._active,
            "triggered_at": self._triggered_at,
            "trigger_reason": self._trigger_reason,
            "history": self._history,
        }


class MonitoringDashboard:
    """Main monitoring dashboard for the RL system.

    Tracks metrics, generates alerts, and manages the kill switch.
    """

    def __init__(self):
        self._trackers: Dict[str, MetricTracker] = {}
        self._alerts: List[Alert] = []
        self._kill_switch = KillSwitch()
        self._thresholds: Dict[str, Dict[str, float]] = {}

    def register_metric(
        self,
        name: str,
        window_seconds: float = 3600.0,
    ) -> MetricTracker:
        """Register a metric to track."""
        tracker = MetricTracker(name, window_seconds)
        self._trackers[name] = tracker
        return tracker

    def record_metric(self, name: str, value: float) -> None:
        """Record a metric value."""
        if name not in self._trackers:
            self.register_metric(name)
        self._trackers[name].record(value)
        self._check_thresholds(name, value)

    def set_threshold(
        self,
        name: str,
        upper: Optional[float] = None,
        lower: Optional[float] = None,
    ) -> None:
        """Set alert thresholds for a metric."""
        if name not in self._thresholds:
            self._thresholds[name] = {}
        if upper is not None:
            self._thresholds[name]["upper"] = upper
        if lower is not None:
            self._thresholds[name]["lower"] = lower

    def _check_thresholds(self, name: str, value: float) -> None:
        """Check if a value violates any thresholds."""
        if name not in self._thresholds:
            return

        thresholds = self._thresholds[name]
        level = None
        message = ""

        if "upper" in thresholds and value > thresholds["upper"]:
            level = AlertLevel.CRITICAL
            message = f"{name} exceeded upper threshold: {value} > {thresholds['upper']}"
        elif "lower" in thresholds and value < thresholds["lower"]:
            level = AlertLevel.WARNING
            message = f"{name} below lower threshold: {value} < {thresholds['lower']}"

        if level:
            alert = Alert(
                level=level,
                metric=name,
                value=value,
                threshold=thresholds.get("upper", thresholds.get("lower", 0)),
                message=message,
            )
            self._alerts.append(alert)
            logger.warning(f"Alert: {message}")

            if level == AlertLevel.KILL_SWITCH:
                self._kill_switch.trigger(message)

    def trigger_kill_switch(self, reason: str) -> None:
        """Manually trigger the kill switch."""
        self._kill_switch.trigger(reason)
        alert = Alert(
            level=AlertLevel.KILL_SWITCH,
            metric="kill_switch",
            value=1.0,
            threshold=0.0,
            message=f"Manual kill switch: {reason}",
        )
        self._alerts.append(alert)

    def reset_kill_switch(self) -> None:
        """Reset the kill switch."""
        self._kill_switch.reset()

    @property
    def kill_switch(self) -> KillSwitch:
        """Get the kill switch."""
        return self._kill_switch

    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
    ) -> List[Alert]:
        """Get alerts, optionally filtered by level."""
        if level is None:
            return list(self._alerts)
        return [a for a in self._alerts if a.level == level]

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get a summary of the current dashboard state."""
        metrics_summary = {}
        for name, tracker in self._trackers.items():
            metrics_summary[name] = {
                "average": tracker.get_average(),
                "max": tracker.get_max(),
                "min": tracker.get_min(),
                "count": tracker.get_count(),
            }

        return {
            "kill_switch_active": self._kill_switch.is_active,
            "total_alerts": len(self._alerts),
            "critical_alerts": len([a for a in self._alerts if a.level == AlertLevel.CRITICAL]),
            "metrics": metrics_summary,
        }

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self._alerts.clear()
