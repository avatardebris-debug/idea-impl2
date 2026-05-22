"""Workflow — defines the high-level workflow for Chronovision."""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Step:
    """A single step in the workflow."""
    name: str
    func: callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None


@dataclass
class Workflow:
    """Defines and manages a workflow."""
    name: str
    description: str = ""
    steps: List[Step] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, name: str, func: callable, *args, **kwargs) -> 'Workflow':
        """Add a step to the workflow."""
        self.steps.append(Step(name=name, func=func, args=args, kwargs=kwargs))
        return self
    
    def run(self) -> Dict[str, Any]:
        """Execute the workflow."""
        self.status = WorkflowStatus.RUNNING
        results = {}
        
        try:
            for step in self.steps:
                logger.info(f"Running step: {step.name}")
                try:
                    step.result = step.func(*step.args, **step.kwargs)
                    step.status = "completed"
                    results[step.name] = step.result
                    # Store result in context for subsequent steps
                    self.context[step.name] = step.result
                    logger.info(f"Step {step.name} completed successfully")
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    logger.error(f"Step {step.name} failed: {e}")
                    self.status = WorkflowStatus.FAILED
                    return {"status": "failed", "error": str(e), "results": results}
            
            self.status = WorkflowStatus.COMPLETED
            results["status"] = "completed"
            results["context"] = self.context
            logger.info(f"Workflow {self.name} completed successfully")
            return results
        
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            logger.error(f"Workflow {self.name} failed: {e}")
            return {"status": "failed", "error": str(e), "results": results}
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the workflow."""
        return {
            "name": self.name,
            "status": self.status.value,
            "steps": [
                {"name": s.name, "status": s.status, "error": s.error}
                for s in self.steps
            ],
            "context_keys": list(self.context.keys()),
        }
    
    def reset(self) -> None:
        """Reset the workflow."""
        self.status = WorkflowStatus.PENDING
        self.context.clear()
        for step in self.steps:
            step.status = "pending"
            step.result = None
            step.error = None
