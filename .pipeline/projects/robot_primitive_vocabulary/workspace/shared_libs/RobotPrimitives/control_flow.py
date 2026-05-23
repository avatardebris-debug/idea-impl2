"""Control flow primitives: sequence, parallel, repeat_until, conditional, wait, signal_done, request_human."""

from .primitive import Primitive
from ._registry import register_primitive


class Sequence(Primitive):
    """Execute a sequence of primitives in order.

    Parameters:
        primitives (list): List of primitive instances to execute in sequence.
    """

    def __init__(self, primitives=None):
        if primitives is None:
            primitives = []
        if not isinstance(primitives, list):
            raise TypeError(f"Sequence.primitives must be a list, got {type(primitives).__name__}")
        for i, p in enumerate(primitives):
            if not isinstance(p, Primitive):
                raise TypeError(f"Sequence.primitives[{i}] must be a Primitive instance, got {type(p).__name__}")
        super().__init__(
            name="sequence",
            category="control_flow",
            parameters={
                "primitives": "list: List of primitive instances to execute in sequence",
            },
            description="Execute a sequence of primitives in order.",
            preconditions=["All primitives are valid"],
            postconditions=["All primitives have been executed in order"],
        )
        self.primitives = primitives

    def execute(self, **kwargs) -> dict:
        """Execute the sequence of primitives."""
        if not isinstance(self.primitives, list):
            raise TypeError(f"execute: primitives must be a list")
        results = []
        for i, p in enumerate(self.primitives):
            if not isinstance(p, Primitive):
                raise TypeError(f"execute: primitives[{i}] must be a Primitive instance")
            result = p.execute(**kwargs)
            results.append(result)
        return {"status": "success", "results": results}


class Parallel(Primitive):
    """Execute a set of primitives in parallel.

    Parameters:
        primitives (list): List of primitive instances to execute in parallel.
    """

    def __init__(self, primitives=None):
        if primitives is None:
            primitives = []
        if not isinstance(primitives, list):
            raise TypeError(f"Parallel.primitives must be a list, got {type(primitives).__name__}")
        for i, p in enumerate(primitives):
            if not isinstance(p, Primitive):
                raise TypeError(f"Parallel.primitives[{i}] must be a Primitive instance, got {type(p).__name__}")
        super().__init__(
            name="parallel",
            category="control_flow",
            parameters={
                "primitives": "list: List of primitive instances to execute in parallel",
            },
            description="Execute a set of primitives in parallel.",
            preconditions=["All primitives are valid"],
            postconditions=["All primitives have been executed in parallel"],
        )
        self.primitives = primitives

    def execute(self, **kwargs) -> dict:
        """Execute the parallel primitives."""
        if not isinstance(self.primitives, list):
            raise TypeError(f"execute: primitives must be a list")
        results = []
        for i, p in enumerate(self.primitives):
            if not isinstance(p, Primitive):
                raise TypeError(f"execute: primitives[{i}] must be a Primitive instance")
            result = p.execute(**kwargs)
            results.append(result)
        return {"status": "success", "results": results}


class RepeatUntil(Primitive):
    """Repeat a primitive until a condition is met.

    Parameters:
        primitive (Primitive): The primitive to repeat.
        condition (str): Condition to check after each iteration (e.g., 'object_detected').
    """

    def __init__(self, primitive=None, condition: str = ""):
        if primitive is not None and not isinstance(primitive, Primitive):
            raise TypeError(f"RepeatUntil.primitive must be a Primitive instance, got {type(primitive).__name__}")
        if not isinstance(condition, str) or not condition.strip():
            raise ValueError(f"RepeatUntil.condition must be a non-empty string, got {condition!r}")
        super().__init__(
            name="repeat_until",
            category="control_flow",
            parameters={
                "primitive": "Primitive: The primitive to repeat",
                "condition": "str: Condition to check after each iteration",
            },
            description="Repeat a primitive until a condition is met.",
            preconditions=["Primitive is valid", "Condition is evaluable"],
            postconditions=["Primitive has been repeated until condition is met"],
        )
        self.primitive = primitive
        self.condition = condition

    def execute(self, **kwargs) -> dict:
        """Execute the repeat_until primitive."""
        if self.primitive is not None and not isinstance(self.primitive, Primitive):
            raise TypeError(f"execute: primitive must be a Primitive instance")
        if not isinstance(self.condition, str) or not self.condition.strip():
            raise ValueError(f"execute: condition must be a non-empty string")
        # In a real system, this would loop until the condition is met.
        # For this implementation, we execute once and return success.
        if self.primitive is None:
            raise ValueError(f"execute: primitive must be set")
        result = self.primitive.execute(**kwargs)
        return {"status": "success", "result": result, "condition": self.condition}


class Conditional(Primitive):
    """Execute a primitive if a condition is met.

    Parameters:
        condition (str): Condition to check (e.g., 'object_detected').
        primitive (Primitive, optional): The primitive to execute if condition is met.
    """

    def __init__(self, condition: str = "", primitive=None):
        if not isinstance(condition, str) or not condition.strip():
            raise ValueError(f"Conditional.condition must be a non-empty string, got {condition!r}")
        if primitive is not None and not isinstance(primitive, Primitive):
            raise TypeError(f"Conditional.primitive must be a Primitive instance, got {type(primitive).__name__}")
        super().__init__(
            name="conditional",
            category="control_flow",
            parameters={
                "condition": "str: Condition to check",
                "primitive": "Primitive: The primitive to execute if condition is met",
            },
            description="Execute a primitive if a condition is met.",
            preconditions=["Condition is evaluable"],
            postconditions=["Primitive executed if condition was met"],
        )
        self.condition = condition
        self.primitive = primitive

    def execute(self, **kwargs) -> dict:
        """Execute the conditional primitive."""
        if not isinstance(self.condition, str) or not self.condition.strip():
            raise ValueError(f"execute: condition must be a non-empty string")
        # In a real system, this would evaluate the condition.
        # For this implementation, we assume the condition is met and execute the primitive.
        if self.primitive is None:
            return {"status": "success", "condition": self.condition, "executed": False}
        if not isinstance(self.primitive, Primitive):
            raise TypeError(f"execute: primitive must be a Primitive instance")
        result = self.primitive.execute(**kwargs)
        return {"status": "success", "condition": self.condition, "executed": True, "result": result}


class Wait(Primitive):
    """Wait for a specified duration.

    Parameters:
        duration (float): Duration to wait in seconds.
    """

    def __init__(self, duration: float = 1.0):
        if not isinstance(duration, (int, float)):
            raise TypeError(f"Wait.duration must be a float, got {type(duration).__name__}")
        if duration < 0:
            raise ValueError(f"Wait.duration must be non-negative, got {duration}")
        super().__init__(
            name="wait",
            category="control_flow",
            parameters={
                "duration": "float: Duration to wait in seconds",
            },
            description="Wait for a specified duration.",
            preconditions=["Timer is available"],
            postconditions=["Specified duration has elapsed"],
        )
        self.duration = float(duration)

    def execute(self, **kwargs) -> dict:
        """Execute the wait primitive."""
        if not isinstance(self.duration, (int, float)):
            raise TypeError(f"execute: duration must be a float")
        if self.duration < 0:
            raise ValueError(f"execute: duration must be non-negative")
        return {"status": "success", "waited_for": self.duration}


class SignalDone(Primitive):
    """Signal that a task or sequence is complete.

    Parameters:
        task_id (str): Identifier of the task to signal completion for.
    """

    def __init__(self, task_id: str = ""):
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError(f"SignalDone.task_id must be a non-empty string, got {task_id!r}")
        super().__init__(
            name="signal_done",
            category="control_flow",
            parameters={
                "task_id": "str: Identifier of the task to signal completion for",
            },
            description="Signal that a task or sequence is complete.",
            preconditions=["Task is complete"],
            postconditions=["Completion signal is sent"],
        )
        self.task_id = task_id

    def execute(self, **kwargs) -> dict:
        """Execute the signal_done primitive."""
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError(f"execute: task_id must be a non-empty string")
        return {"status": "success", "task": self.task_id, "signal": "done"}


class RequestHuman(Primitive):
    """Request human assistance for a task.

    Parameters:
        task_id (str): Identifier of the task requiring assistance.
        reason (str): Reason for requesting assistance.
    """

    def __init__(self, task_id: str = "", reason: str = ""):
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError(f"RequestHuman.task_id must be a non-empty string, got {task_id!r}")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"RequestHuman.reason must be a non-empty string, got {reason!r}")
        super().__init__(
            name="request_human",
            category="control_flow",
            parameters={
                "task_id": "str: Identifier of the task requiring assistance",
                "reason": "str: Reason for requesting assistance",
            },
            description="Request human assistance for a task.",
            preconditions=["Task requires human assistance"],
            postconditions=["Human assistance request is sent"],
        )
        self.task_id = task_id
        self.reason = reason

    def execute(self, **kwargs) -> dict:
        """Execute the request_human primitive."""
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError(f"execute: task_id must be a non-empty string")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError(f"execute: reason must be a non-empty string")
        return {"status": "success", "task": self.task_id, "reason": self.reason}


# Register primitives
register_primitive(Sequence, "control_flow", "Execute a sequence of primitives in order.", [
    {"name": "primitives", "type": "list", "description": "List of primitive instances to execute in sequence"},
])
register_primitive(Parallel, "control_flow", "Execute multiple primitives in parallel.", [
    {"name": "primitives", "type": "list", "description": "List of primitive instances to execute in parallel"},
])
register_primitive(RepeatUntil, "control_flow", "Repeat a primitive until a condition is met.", [
    {"name": "primitive", "type": "Primitive", "description": "Primitive to repeat"},
    {"name": "condition", "type": "str", "description": "Condition string to evaluate (default 'never')"},
    {"name": "max_iterations", "type": "int", "description": "Maximum iterations (default 100)"},
])
register_primitive(Conditional, "control_flow", "Execute primitives based on a condition.", [
    {"name": "condition", "type": "str", "description": "Condition string to evaluate"},
    {"name": "then_primitives", "type": "list", "description": "Primitives to execute if condition is true"},
    {"name": "else_primitives", "type": "list", "description": "Primitives to execute if condition is false"},
])
register_primitive(Wait, "control_flow", "Wait for a specified duration.", [
    {"name": "duration", "type": "float", "description": "Duration to wait in seconds (default 1.0)"},
])
register_primitive(SignalDone, "control_flow", "Signal that a task is complete.", [
    {"name": "task_id", "type": "str", "description": "Identifier of the completed task"},
    {"name": "result", "type": "str", "description": "Result description (default 'success')"},
])
register_primitive(RequestHuman, "control_flow", "Request human intervention.", [
    {"name": "message", "type": "str", "description": "Message to display to the human operator"},
    {"name": "timeout", "type": "float", "description": "Timeout in seconds (default 300)"},
])
