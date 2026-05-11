"""SOP Executor for AutomatedClientOps Manager.

Executes Standard Operating Procedures to automate client operations
including file delivery and invoice generation.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SOPStep:
    """A single step in an SOP execution.

    Attributes:
        name: Unique step identifier.
        action: The action to perform (e.g., 'send_email', 'generate_invoice', 'deliver_file').
        params: Parameters for the action.
        description: Human-readable description.
    """

    name: str
    action: str
    params: dict = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "action": self.action,
            "params": self.params,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SOPStep":
        return cls(
            name=data["name"],
            action=data["action"],
            params=data.get("params", {}),
            description=data.get("description", ""),
        )


@dataclass
class SOP:
    """A Standard Operating Procedure for client operations.

    Attributes:
        name: SOP identifier.
        description: Human-readable description.
        steps: Ordered list of execution steps.
        inputs: Required input fields.
    """

    name: str
    description: str
    steps: list[SOPStep] = field(default_factory=list)
    inputs: list[dict] = field(default_factory=list)

    def add_step(self, step: SOPStep) -> None:
        self.steps.append(step)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "inputs": self.inputs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SOP":
        return cls(
            name=data["name"],
            description=data["description"],
            steps=[SOPStep.from_dict(s) for s in data.get("steps", [])],
            inputs=data.get("inputs", []),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SOP":
        """Load an SOP from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            A validated SOP.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"SOP file not found: {path}")

        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required to load SOPs from YAML. Install with: pip install pyyaml")

        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"SOP YAML must resolve to a mapping, got {type(raw).__name__}")
        return cls.from_dict(raw)


@dataclass
class ExecutionResult:
    """Result of executing an SOP.

    Attributes:
        success: Whether the execution succeeded.
        output: Output data from the execution.
        errors: List of error messages.
        step_results: Results from each step.
    """

    success: bool
    output: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    step_results: list[dict] = field(default_factory=list)


class SOPExecutor:
    """Executes SOPs for automated client operations.

    Attributes:
        sop: The SOP to execute.
        context: Shared context across steps.
    """

    def __init__(self, sop: SOP):
        self.sop = sop
        self.context: dict[str, Any] = {}

    def execute(self, inputs: Optional[dict[str, Any]] = None) -> ExecutionResult:
        """Execute the SOP with the given inputs.

        Args:
            inputs: Input data for the SOP.

        Returns:
            ExecutionResult with the outcome.
        """
        self.context = {"inputs": inputs or {}, "outputs": {}}
        step_results = []

        for step in self.sop.steps:
            try:
                # Render Jinja2 templates in params using context
                rendered_params = self._render_templates(step.params)
                result = self._execute_step(step, rendered_params)
                step_results.append({
                    "step": step.name,
                    "success": True,
                    "result": result,
                })
            except Exception as e:
                logger.error(f"Step '{step.name}' failed: {e}")
                step_results.append({
                    "step": step.name,
                    "success": False,
                    "error": str(e),
                })
                return ExecutionResult(
                    success=False,
                    errors=[f"Step '{step.name}' failed: {e}"],
                    step_results=step_results,
                )

        return ExecutionResult(
            success=True,
            output=self.context.get("outputs", {}),
            step_results=step_results,
        )

    def _render_templates(self, obj: Any) -> Any:
        """Recursively render Jinja2 templates in a data structure.

        Args:
            obj: The object to render (dict, list, str, or other).

        Returns:
            The rendered object with all Jinja2 templates resolved.
        """
        try:
            from jinja2 import Template
        except ImportError:
            raise ImportError("Jinja2 is required for SOP templating. Install with: pip install jinja2")

        if isinstance(obj, dict):
            return {k: self._render_templates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._render_templates(item) for item in obj]
        elif isinstance(obj, str):
            try:
                template = Template(obj)
                return template.render(**self.context)
            except Exception:
                # If rendering fails, return the original string
                return obj
        else:
            return obj

    def _execute_step(self, step: SOPStep, params: dict) -> dict:
        """Execute a single SOP step.

        Args:
            step: The step to execute.

        Returns:
            Result dictionary from the step.
        """
        action_handlers = {
            "send_email": self._handle_send_email,
            "generate_invoice": self._handle_generate_invoice,
            "deliver_file": self._handle_deliver_file,
            "log": self._handle_log,
            "set_context": self._handle_set_context,
        }

        handler = action_handlers.get(step.action)
        if handler is None:
            raise ValueError(f"Unknown action: {step.action}")

        return handler(step.params)

    def _handle_send_email(self, params: dict) -> dict:
        """Handle send_email action."""
        from email_tool import EmailMessage

        msg = EmailMessage(
            to=params["to"],
            subject=params.get("subject", ""),
            body=params.get("body", ""),
            html_body=params.get("html_body"),
            attachments=params.get("attachments", []),
            cc=params.get("cc"),
            bcc=params.get("bcc"),
        )
        self.context["last_email"] = msg
        return {"action": "send_email", "to": msg.to, "subject": msg.subject}

    def _handle_generate_invoice(self, params: dict) -> dict:
        """Handle generate_invoice action."""
        from invoice import Invoice, InvoiceItem

        items = [
            InvoiceItem(description=item["description"], quantity=item.get("quantity", 1), unit_price=item.get("unit_price", 0))
            for item in params.get("items", [])
        ]
        invoice = Invoice(
            invoice_id=params.get("invoice_id", ""),
            client_id=params.get("client_id", ""),
            items=items,
            due_date=None,
            notes=params.get("notes", ""),
        )
        self.context["last_invoice"] = invoice
        return {
            "action": "generate_invoice",
            "invoice_id": invoice.invoice_id,
            "total": invoice.total,
        }

    def _handle_deliver_file(self, params: dict) -> dict:
        """Handle deliver_file action."""
        files = params.get("files", [])
        self.context["last_delivered_files"] = files
        return {"action": "deliver_file", "files": files}

    def _handle_log(self, params: dict) -> dict:
        """Handle log action."""
        message = params.get("message", "")
        level = params.get("level", "info").upper()
        getattr(logger, level.lower(), logger.info)(message)
        return {"action": "log", "message": message}

    def _handle_set_context(self, params: dict) -> dict:
        """Handle set_context action."""
        for key, value in params.items():
            self.context[key] = value
        return {"action": "set_context", "keys": list(params.keys())}


def create_sop(
    name: str,
    description: str,
    steps: list[dict],
    inputs: Optional[list[dict]] = None,
) -> SOP:
    """Convenience function to create an SOP.

    Args:
        name: SOP name.
        description: SOP description.
        steps: List of step dicts.
        inputs: Optional list of input field dicts.

    Returns:
        A new SOP instance.
    """
    sop = SOP(name=name, description=description, inputs=inputs or [])
    for step_data in steps:
        sop.add_step(SOPStep.from_dict(step_data))
    return sop
