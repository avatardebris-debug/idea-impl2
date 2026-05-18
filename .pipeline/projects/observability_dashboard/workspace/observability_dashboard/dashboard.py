"""
dashboard.py — Core metrics aggregator for pipeline observability.
"""
from __future__ import annotations
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

# Example pricing (cost per 1k tokens)
_COST_MAP = {
    "qwen3:6b": 0.0,
    "gpt-4": 0.03,
    "gpt-3.5-turbo": 0.002,
    "claude-3-opus": 0.015,
    "claude-3-sonnet": 0.003
}


@dataclass
class AgentMetrics:
    total_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    errors: int = 0
    total_duration_ms: int = 0


@dataclass
class DashboardStats:
    total_executions: int
    global_cost: float
    global_errors: int
    agent_metrics: dict[str, AgentMetrics]
    project_metrics: dict[str, AgentMetrics]


def parse_logs(log_lines: list[str]) -> DashboardStats:
    """Parse JSONL log lines and aggregate metrics."""
    agent_stats: dict[str, AgentMetrics] = defaultdict(AgentMetrics)
    proj_stats: dict[str, AgentMetrics] = defaultdict(AgentMetrics)
    
    total_executions = 0
    global_cost = 0.0
    global_errors = 0

    for line in log_lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        total_executions += 1
        
        agent = record.get("agent", "unknown_agent")
        project = record.get("project", "unknown_project")
        tokens = int(record.get("tokens", 0))
        model = record.get("model", "qwen3:6b")
        duration = int(record.get("duration_ms", 0))
        is_error = bool(record.get("error", False))
        
        # Calculate cost
        cost_per_1k = _COST_MAP.get(model, 0.0)
        cost = (tokens / 1000.0) * cost_per_1k
        
        global_cost += cost
        if is_error:
            global_errors += 1
            
        for stats in (agent_stats[agent], proj_stats[project]):
            stats.total_calls += 1
            stats.total_tokens += tokens
            stats.total_cost += cost
            stats.total_duration_ms += duration
            if is_error:
                stats.errors += 1

    return DashboardStats(
        total_executions=total_executions,
        global_cost=global_cost,
        global_errors=global_errors,
        agent_metrics=dict(agent_stats),
        project_metrics=dict(proj_stats)
    )


def format_dashboard(stats: DashboardStats) -> str:
    """Format the dashboard as a text report."""
    lines = [
        "===========================================================",
        " 📊 PIPELINE OBSERVABILITY DASHBOARD",
        "===========================================================",
        f" Total Executions: {stats.total_executions}",
        f" Total Errors:     {stats.global_errors}",
        f" Total LLM Cost:   ${stats.global_cost:.4f}",
        "-----------------------------------------------------------",
        " 🤖 METRICS BY AGENT",
        f" {'Agent':<20} | {'Calls':<6} | {'Errors':<6} | {'Tokens':<8} | {'Cost':<8}",
        "-----------------------------------------------------------"
    ]
    
    for agent, m in sorted(stats.agent_metrics.items(), key=lambda x: -x[1].total_calls):
        lines.append(f" {agent:<20} | {m.total_calls:<6} | {m.errors:<6} | {m.total_tokens:<8} | ${m.total_cost:<7.4f}")

    lines.extend([
        "-----------------------------------------------------------",
        " 📁 METRICS BY PROJECT",
        f" {'Project':<20} | {'Calls':<6} | {'Errors':<6} | {'Tokens':<8} | {'Cost':<8}",
        "-----------------------------------------------------------"
    ])
    
    for proj, m in sorted(stats.project_metrics.items(), key=lambda x: -x[1].total_calls):
        lines.append(f" {proj:<20} | {m.total_calls:<6} | {m.errors:<6} | {m.total_tokens:<8} | ${m.total_cost:<7.4f}")

    lines.append("===========================================================")
    return "\n".join(lines)
