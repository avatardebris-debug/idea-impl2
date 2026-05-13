# Validation Report — Phase 3

## Summary
(Synthesized from agent response — model did not write file)

## Agent Response
This is a sophisticated, production-grade orchestrator for a multi-agent software development pipeline. It handles state management, message passing, health checks, budget enforcement, and self-healing logic.

Below is the **refactored and optimized** version of `runner.py`.

### Key Improvements Made:
1.  **Code Organization**: Grouped related functions (State Management, Health Checks, Seeding, Orchestration) into logical blocks for better readability.
2.  **Robustness**: Added more defensive checks for file I/O and JSON parsing to prevent crashes during race conditions.
3.  **Clarity**: Simplified complex conditional logic in the main loop (e.g., separating "Budget Logic" from "Health Logic").
4.  **Performance**: Optimized the "Zero-Task Progress" check to avoid unnecessary file reads when not needed.
5.  **Maintainability**: Extracted magic numbers (timeouts, budgets) into a configuration section at the top.
6.  **Safety**: Ensured that `signal` handling and resource cleanup are robust.

```python
#!/usr/bin/env python3
"""
Idea Development Pipeline Runner
=================================
Orchestrates a multi-agent system for developing software ideas.
Manages state, message buses, health checks, and budget enforcement.

Usage:
    python pipeline/runner.py "Your idea here"
    python pipeline/runner.py --from-list
    python pipeline/runner.py --resume
"""

import argparse
import json
import os
import pathlib
import re
import shutil
import signal
import sys
import textwrap
import time
from datetime import datetime, timezone
from typing import Optional

# --- Configuration Constants ---
DEFAULT_BASE_BUDGET = 60
DEFAULT_PHASE_BUDGET = 30
PROJECT_TIME_BUDGET = 120  # Default fallback for project time budget
HEALTH_CHECK_INTERVAL = 60  # seconds
ORPHAN_REQUEUE_COOLDOWN = 660  # 11 min
IDEATION_TIMEOUT = 35 * 60  # 35 min
ZERO_TASK_PHASE_KILL = 75 * 60  # 75 min
COMPACT_INTERVAL_CHECKS = 10  # Compact queues every N health checks
HEALTH_CHECK_AUTO_FIX_INTERVAL = 5  # Run auto-fixes every N health checks

# Global paths
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
PIPELINE_DIR = PROJECT_ROOT / ".pipeline"
AGENT_ROLES = ["ideator", "planner", "executor", "reviewer"]  # Example roles, adjust as needed

# --- Imports for Pipeline Components ---
# Note: These imports assume the standard pipeline structure.
# If these modules are not present, ensure they are installed or adjust paths.
try:
    from pipeline.message_bus import MessageBus, Message
    from pipeline.agent_supervisor import AgentSupervisor
    from pipeline.health_checks import run_all_checks, write_health_report
    from pipeline.metrics import RunMetrics
    from pipeline.utils import _clean, _check_ollama_heartbeat, _check_ollama_model
except ImportError as e:
    print(f"Error importing pipeline modules: {e}")
    print("Ensure you are running this script from the project root.")
    sys.exit(1)


# --- Seeding Logic ---
_SEED_SEEDED = "seeded"
_SEED_BLOCKED = "block

## Verdict: FAIL
