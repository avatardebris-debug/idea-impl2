"""Custom exception classes for the Human-in-the-Loop Reviewer."""


class InvalidCheckpointError(Exception):
    """Raised when a checkpoint operation receives an invalid checkpoint reference."""

    def __init__(self, message: str = "Invalid checkpoint reference", checkpoint_id: str = ""):
        super().__init__(message)
        self.message = message
        self.checkpoint_id = checkpoint_id

    def __str__(self) -> str:
        if self.checkpoint_id:
            return f"{self.message} (checkpoint_id: {self.checkpoint_id})"
        return self.message


class InvalidStatusError(Exception):
    """Raised when an invalid status transition is attempted."""

    VALID_STATUSES = ("pending", "approved", "rejected")

    def __init__(self, message: str = "Invalid status transition", current_status: str = "", new_status: str = ""):
        super().__init__(message)
        self.message = message
        self.current_status = current_status
        self.new_status = new_status

    def __str__(self) -> str:
        parts = [self.message]
        if self.current_status:
            parts.append(f"current_status: {self.current_status}")
        if self.new_status:
            parts.append(f"new_status: {self.new_status}")
        return " | ".join(parts)
