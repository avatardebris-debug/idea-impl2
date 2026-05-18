"""Telemetry and Cost Calculator for Pipeline Observability Dashboard."""
import json
from pathlib import Path
from typing import Dict, Any, Tuple

# Simple fixed cost model per 1k tokens for MVP
# In a real system, this would be updated dynamically or fetched from an API
MODEL_PRICING = {
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
    "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    "ollama": {"prompt": 0.0, "completion": 0.0},
    "default": {"prompt": 0.001, "completion": 0.002}
}

class TelemetryParser:
    """Parses execution logs to extract metrics and costs."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.workspace_dir = project_path / "workspace"
        
    def _find_execution_logs(self) -> list[Path]:
        """Find any execution_log.json files in the workspace recursively."""
        if not self.workspace_dir.exists():
            return []
        # Simple search for execution_log.json or token_usage.json
        logs = list(self.workspace_dir.rglob("execution_log.json"))
        logs.extend(list(self.workspace_dir.rglob("token_usage.json")))
        return logs

    def calculate_cost(self, tokens_in: int, tokens_out: int, model: str) -> float:
        """Calculate the estimated cost in USD based on token usage."""
        model_lower = model.lower()
        pricing = MODEL_PRICING.get("default")
        
        for key, rates in MODEL_PRICING.items():
            if key in model_lower:
                pricing = rates
                break
                
        # Price is per 1000 tokens
        cost_in = (tokens_in / 1000) * pricing["prompt"]
        cost_out = (tokens_out / 1000) * pricing["completion"]
        return cost_in + cost_out

    def parse_metrics(self) -> Tuple[float, float, float]:
        """
        Extract metrics from logs.
        Returns: (cost_estimate, error_rate, avg_step_duration)
        """
        logs = self._find_execution_logs()
        if not logs:
            return 0.0, 0.0, 0.0
            
        total_cost = 0.0
        total_steps = 0
        error_steps = 0
        total_duration = 0.0
        
        for log_path in logs:
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Handle list of steps or single dict with steps
                steps = data if isinstance(data, list) else data.get("steps", [])
                
                for step in steps:
                    if not isinstance(step, dict):
                        continue
                        
                    total_steps += 1
                    
                    if step.get("status") == "error" or step.get("error"):
                        error_steps += 1
                        
                    total_duration += float(step.get("duration", 0.0))
                    
                    # Token cost calculation
                    tokens_in = step.get("tokens_in", step.get("prompt_tokens", 0))
                    tokens_out = step.get("tokens_out", step.get("completion_tokens", 0))
                    model = step.get("model", "default")
                    
                    if tokens_in > 0 or tokens_out > 0:
                        total_cost += self.calculate_cost(tokens_in, tokens_out, model)
                        
            except Exception:
                continue
                
        error_rate = (error_steps / total_steps) if total_steps > 0 else 0.0
        avg_duration = (total_duration / total_steps) if total_steps > 0 else 0.0
        
        return total_cost, error_rate, avg_duration
