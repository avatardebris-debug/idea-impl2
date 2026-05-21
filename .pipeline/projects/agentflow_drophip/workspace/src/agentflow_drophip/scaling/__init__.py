"""Scaling module — multi-store scaling and autonomous optimization."""

from .multi_store_manager import MultiStoreManager, StoreConfig
from .optimization_agent import OptimizationAgent, ABOption
from .analytics_agent import AnalyticsAgent, MetricResult
from .scaling_engine import ScalingEngine
from .auto_scaling_agent import AutoScalingAgent

__all__ = [
    "MultiStoreManager",
    "StoreConfig",
    "OptimizationAgent",
    "ABOption",
    "AnalyticsAgent",
    "MetricResult",
    "ScalingEngine",
    "AutoScalingAgent",
]
