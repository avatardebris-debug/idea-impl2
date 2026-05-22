"""Dispatcher for handling email actions (move, file, label, notify)."""

import json
import logging
import os
import shutil
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from email_tool.models import Email, Rule, RuleMatch, ActionType, ActionExecutionResult
from email_tool.path_builder import PathBuilder
from email_tool.formatter import Formatter


class ActionDispatcher:
    """
    Dispatcher for handling email actions (move, file, label, notify).
    
    Actions:
    - MOVE: Move email to destination directory
    - FILE: Save email to file system
    - LABEL: Apply labels/tags to email (metadata only)
    - NOTIFY: Send notification (metadata only)
    """
    
    def __init__(
        self,
        base_path: str = "./archive",
        dry_run: bool = False,
        collision_strategy: str = "rename"
    ):
        """
        Initialize the dispatcher.
        
        Args:
            base_path: Base directory for all operations.
            dry_run: If True, only simulate actions without making changes.
            collision_strategy: Strategy for handling filename collisions:
                - "rename": Auto-rename with timestamp
                - "number": Add number suffix (file_1, file_2)
                - "overwrite": Overwrite existing file
        """
        self.base_path = os.path.abspath(base_path)
        self.dry_run = dry_run
        self.collision_strategy = collision_strategy
        self.path_builder = PathBuilder()
        self.operations_log: List[dict] = []
    
    def handle_action(
        self,
        email: Optional[Email] = None,
        rule_match: Optional[Any] = None,
        action: Optional[ActionType] = None,
        action_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle a single action for an email.
        
        Args:
            email: The email to process.
            rule_match: The rule match that triggered the action.
            action: The action type to execute.
            action_params: Parameters for the action.
        
        Returns:
            Dictionary with action execution results.
        """
        action_params = action_params or {}
        
        if action is None:
            return {
                "success": False,
                "error": "No action specified"
            }
        
        if action == ActionType.MOVE:
            result = self._handle_move_as_dict(email, action_params)
        elif action == ActionType.FILE:
            result = self._handle_file_as_dict(email, action_params)
        elif action == ActionType.LABEL:
            result = self._handle_label_as_dict(email, action_params)
        elif action == ActionType.NOTIFY:
            result = self._handle_notify_as_dict(email, action_params)
        else:
            result = {
                "success": False,
                "error": f"Unknown action type: {action}"
            }
            
        self.operations_log.append(result)
        return result
    
    def dispatch(
        self,
        action: Tuple[ActionType, Dict[str, Any]],
        email: Optional[Email] = None
    ) -> ActionExecutionResult:
        """
        Dispatch an action for an email.
        
        Args:
            action: Tuple of (action_type, action_params).
            email: The email to process (optional for some actions).
        
        Returns:
            ActionExecutionResult with operation results.
        """
        action_type, action_params = action
        action_params = action_params or {}
        
        if action_type == ActionType.MOVE:
            result = self._handle_move(email, action_params)
        elif action_type == ActionType.FILE:
            result = self._handle_file(email, action_params)
        elif action_type == ActionType.LABEL:
            result = self._handle_label(email, action_params)
        elif action_type == ActionType.NOTIFY:
            result = self._handle_notify(email, action_params)
        else:
            result = ActionExecutionResult(
                action_type=action_type,
                success=False,
                message=f"Unknown action type: {action_type}"
            )
            
        # Convert ActionExecutionResult to dict for operations log
        result_dict = {
            "success": result.success,
            "action": result.action_type.value if hasattr(result.action_type, 'value') else str(result.action_type),
            "message": result.message,
            "details": result.details
        }
        if not result.success:
            result_dict["error"] = result.message
            
        self.operations_log.append(result_dict)
        return result
    
    def _handle_move_as_dict(
        self,
        email: Optional[Email],
        action_params: dict
    ) -> Dict[str, Any]:
        """Handle MOVE action and return dict."""
        # Determine destination directory
        dest_dir = action_params.get("destination", self.base_path)
        
        # Build path
        if email:
            filename = self.path_builder.build_filename(
                email,
                extension="eml"
            )
            dest_path = os.path.join(dest_dir, filename)
            
            # Check for collision
            if os.path.exists(dest_path):
                dest_path = self._resolve_collision(dest_path)
            
            # Perform move
            if self.dry_run:
                return {
                    "success": True,
                    "action": "MOVE",
                    "message": f"Would move to {dest_path}",
                    "details": {"destination": dest_path}
                }
            else:
                # Create destination directory if needed
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Move file
                shutil.move(email.source_path, dest_path)
                
                return {
                    "success": True,
                    "action": "MOVE",
                    "message": f"Moved to {dest_path}",
                    "details": {"destination": dest_path}
                }
        else:
            return {
                "success": False,
                "error": "No email provided for MOVE action"
            }
    
    def _handle_file_as_dict(
        self,
        email: Optional[Email],
        action_params: dict
    ) -> Dict[str, Any]:
        """Handle FILE action and return dict."""
        # Determine format
        file_format = action_params.get("format", "eml")
        
        # Determine destination directory
        dest_dir = action_params.get("destination", self.base_path)
        
        # Build path
        if email:
            filename = self.path_builder.build_filename(
                email,
                extension=file_format
            )
            dest_path = os.path.join(dest_dir, filename)
            
            # Check for collision
            if os.path.exists(dest_path):
                dest_path = self._resolve_collision(dest_path)
            
            # Perform file operation
            if self.dry_run:
                return {
                    "success": True,
                    "action": "FILE",
                    "message": f"Would save as {file_format} to {dest_path}",
                    "details": {"destination": dest_path, "format": file_format}
                }
            else:
                # Create destination directory if needed
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Read email content
                if file_format == "eml":
                    content = email.raw_content
                elif file_format == "json":
                    content = json.dumps(email.to_dict(), indent=2)
                elif file_format == "md":
                    content = self._format_email_as_markdown(email)
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported format: {file_format}"
                    }
                
                # Write file
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "action": "FILE",
                    "message": f"Saved as {file_format} to {dest_path}",
                    "details": {"destination": dest_path, "format": file_format}
                }
        else:
            return {
                "success": False,
                "error": "No email provided for FILE action"
            }
    
    def _handle_label_as_dict(
        self,
        email: Optional[Email],
        action_params: dict
    ) -> Dict[str, Any]:
        """Handle LABEL action and return dict."""
        # Get labels to apply
        labels = action_params.get("labels", [])
        
        if not labels:
            return {
                "success": True,
                "action": "LABEL",
                "message": "No labels to apply",
                "details": {"labels": []}
            }
        
        # Apply labels
        if email:
            # Update email labels
            existing_labels = set(email.labels)
            new_labels = set(labels)
            added = new_labels - existing_labels
            removed = existing_labels - new_labels
            
            if self.dry_run:
                return {
                    "success": True,
                    "action": "LABEL",
                    "message": f"Would apply labels: {labels}",
                    "details": {
                        "labels": labels,
                        "added": list(added),
                        "removed": list(removed)
                    }
                }
            else:
                # Update email labels
                email.labels = list(new_labels)
                
                return {
                    "success": True,
                    "action": "LABEL",
                    "message": f"Applied labels: {labels}",
                    "details": {
                        "labels": labels,
                        "added": list(added),
                        "removed": list(removed)
                    }
                }
        else:
            return {
                "success": False,
                "error": "No email provided for LABEL action"
            }
    
    def _handle_notify_as_dict(
        self,
        email: Optional[Email],
        action_params: dict
    ) -> Dict[str, Any]:
        """Handle NOTIFY action and return dict."""
        # Get notification details
        notify_type = action_params.get("type", "log")
        message = action_params.get("message", "")
        
        if self.dry_run:
            return {
                "success": True,
                "action": "NOTIFY",
                "message": f"Would send {notify_type} notification",
                "details": {"type": notify_type, "message": message}
            }
        else:
            # Send notification
            if notify_type == "log":
                logging.info(f"Email notification: {message}")
            elif notify_type == "print":
                print(f"Email notification: {message}")
            elif notify_type == "email":
                # TODO: Implement email notification
                logging.warning("Email notification not implemented")
            else:
                logging.warning(f"Unknown notification type: {notify_type}")
            
            return {
                "success": True,
                "action": "NOTIFY",
                "message": f"Sent {notify_type} notification",
                "details": {"type": notify_type, "message": message}
            }
    
    def _handle_move(
        self,
        email: Optional[Email],
        action_params: dict
    ) -> ActionExecutionResult:
        """Handle MOVE action."""
        # Determine destination directory
        dest_dir = action_params.get("destination", self.base_path)
        
        # Build path
        if email:
            filename = self.path_builder.build_filename(
                email,
                extension="eml"
            )
            dest_path = os.path.join(dest_dir, filename)
            
            # Check for collision
            if os.path.exists(dest_path):
                dest_path = self._resolve_collision(dest_path)
            
            # Perform move
            if self.dry_run:
                return ActionExecutionResult(
                    action_type=ActionType.MOVE,
                    success=True,
                    message=f"Would move to {dest_path}",
                    details={"destination": dest_path, "dry_run": True}
                )
            else:
                try:
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # Move file
                    shutil.move(str(email.source_path), dest_path)
                    
                    return ActionExecutionResult(
                        action_type=ActionType.MOVE,
                        success=True,
                        message=f"Moved to {dest_path}",
                        details={"destination": dest_path, "dry_run": False}
                    )
                except Exception as e:
                    return ActionExecutionResult(
                        action_type=ActionType.MOVE,
                        success=False,
                        message=str(e)
                    )
        else:
            if self.dry_run:
                return ActionExecutionResult(
                    action_type=ActionType.MOVE,
                    success=True,
                    message="Would move (no email provided, dry_run mode)",
                    details={"dry_run": True}
                )
            return ActionExecutionResult(
                action_type=ActionType.MOVE,
                success=False,
                message="Email required for MOVE action"
            )
    
    def _handle_file(
        self,
        email: Optional[Email],
        action_params: dict
    ) -> ActionExecutionResult:
        """Handle FILE action."""
        # Determine output format
        output_format = action_params.get("format", "eml")
        dest_dir = action_params.get("destination", self.base_path)
        
        # Build path
        if email:
            filename = self.path_builder.build_filename(
                email,
                extension=output_format
            )
            dest_path = os.path.join(dest_dir, filename)
            
            # Check for collision
            if os.path.exists(dest_path):
                dest_path = self._resolve_collision(dest_path)
            
            # Perform file operation
            if self.dry_run:
                return ActionExecutionResult(
                    action_type=ActionType.FILE,
                    success=True,
                    message=f"Would save to {dest_path}",
                    details={"format": output_format, "destination": dest_path, "dry_run": True}
                )
            else:
                try:
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # Create content based on format
                    if output_format == "eml":
                        content = email.raw_content
                    elif output_format == "json":
                        content = json.dumps(email.to_dict(), indent=2)
                    elif output_format == "md":
                        content = self._format_email_as_markdown(email)
                    else:
                        return ActionExecutionResult(
                            action_type=ActionType.FILE,
                            success=False,
                            message=f"Unsupported format: {output_format}"
                        )
                    
                    # Write file
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    return ActionExecutionResult(
                        action_type=ActionType.FILE,
                        success=True,
                        message=f"Saved to {dest_path}",
                        details={"format": output_format, "destination": dest_path, "dry_run": False}
                    )
                except Exception as e:
                    return ActionExecutionResult(
                        action_type=ActionType.FILE,
                        success=False,
                        message=str(e)
                    )
        else:
            if self.dry_run:
                return ActionExecutionResult(
                    action_type=ActionType.FILE,
                    success=True,
                    message="Would file (no email provided, dry_run mode)",
                    details={"dry_run": True}
                )
            return ActionExecutionResult(
                action_type=ActionType.FILE,
                success=False,
                message="Email required for FILE action"
            )
    
    def _handle_label(
        self,
        email: Optional[Email],
        action_params: dict
    ) -> ActionExecutionResult:
        """Handle LABEL action (metadata only, no file operations)."""
        # Get labels from action params
        labels = action_params.get("labels", [])
        
        # Apply labels to email metadata
        if email:
            all_labels = list(set(email.labels + labels))
            email.labels = all_labels
            
            return ActionExecutionResult(
                action_type=ActionType.LABEL,
                success=True,
                message=f"Applied labels: {labels}",
                details={"labels": labels, "dry_run": self.dry_run}
            )
        else:
            if self.dry_run:
                return ActionExecutionResult(
                    action_type=ActionType.LABEL,
                    success=True,
                    message="Would label (no email provided, dry_run mode)",
                    details={"dry_run": True}
                )
            return ActionExecutionResult(
                action_type=ActionType.LABEL,
                success=False,
                message="Email required for LABEL action"
            )
    
    def _handle_notify(
        self,
        email: Optional[Email],
        action_params: dict
    ) -> ActionExecutionResult:
        """Handle NOTIFY action (metadata only, no file operations)."""
        # Get notification message
        message = action_params.get("message", "Notification sent")
        
        return ActionExecutionResult(
            action_type=ActionType.NOTIFY,
            success=True,
            message=message,
            details={"dry_run": self.dry_run}
        )
    
    def _format_email_as_markdown(self, email: Email) -> str:
        """
        Format email as markdown.
        
        Args:
            email: Email to format.
        
        Returns:
            Markdown formatted email.
        """
        lines = [
            f"# Email: {email.subject}",
            "",
            f"**From:** {email.from_addr}",
            f"**To:** {', '.join(email.to_addrs)}",
            f"**Date:** {email.date.isoformat()}",
            "",
            "---",
            "",
            f"**Labels:** {', '.join(email.labels) if email.labels else 'None'}",
            "",
            "---",
            "",
            "## Body",
            "",
            email.body_plain or email.body_html or "[No content]",
            "",
            "---",
            "",
        ]
        
        if email.attachments:
            lines.append("## Attachments")
            lines.append("")
            for attachment in email.attachments:
                lines.append(f"- {attachment.filename} ({attachment.size} bytes)")
            lines.append("")
        
        lines.append("---")
        lines.append(f"*Processed on {datetime.now().isoformat()}*")
        
        return "\n".join(lines)
    
    def _resolve_collision(self, existing_path: str) -> str:
        """
        Resolve filename collision based on strategy.
        
        Args:
            existing_path: Path of existing file.
        
        Returns:
            New path that doesn't conflict.
        """
        base, ext = os.path.splitext(existing_path)
        
        if self.collision_strategy == "overwrite":
            return existing_path
        
        elif self.collision_strategy == "number":
            counter = 1
            while True:
                new_path = f"{base}_{counter}{ext}"
                if not os.path.exists(new_path):
                    return new_path
                counter += 1
        
        elif self.collision_strategy == "rename":
            # Add timestamp after extension
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_path = f"{base}{ext}_{timestamp}{ext}"
            return new_path
        
        else:
            # Default to number strategy
            return self._resolve_collision(existing_path)
    
    def handle_multiple_actions(
        self,
        email: Email,
        actions: List[Tuple[ActionType, Dict[str, Any]]]
    ) -> List[ActionExecutionResult]:
        """
        Handle multiple actions for an email.
        
        Args:
            email: The email to process.
            actions: List of (action_type, action_params) tuples.
        
        Returns:
            List of ActionExecutionResult objects.
        """
        results = []
        
        for action_type, action_params in actions:
            result = self.dispatch(
                action=(action_type, action_params),
                email=email
            )
            results.append(result)
        
        return results
    
    def get_operations_log(self) -> List[dict]:
        """
        Get the log of all operations performed.
        
        Returns:
            List of operation result dictionaries.
        """
        return self.operations_log.copy()
    
    def clear_operations_log(self):
        """Clear the operations log."""
        self.operations_log = []
    
    def get_summary(self) -> dict:
        """
        Get a summary of all operations.
        
        Returns:
            Dictionary with operation statistics.
        """
        summary = {
            "total_operations": len(self.operations_log),
            "successful_operations": 0,
            "failed_operations": 0,
            "dry_run": self.dry_run,
            "by_action": {},
            "by_email": {}
        }
        
        for op in self.operations_log:
            if op.get("success"):
                summary["successful_operations"] += 1
            else:
                summary["failed_operations"] += 1
            
            # Count by action type
            action = op.get("action", "UNKNOWN")
            summary["by_action"][action] = summary["by_action"].get(action, 0) + 1
            
            # Count by email
            email_id = op.get("email_id", "UNKNOWN")
            summary["by_email"][email_id] = summary["by_email"].get(email_id, 0) + 1
        
        return summary


class ActionExecutor:
    """
    Executor for running actions with retry logic.
    
    Handles:
    - Executing actions through the dispatcher
    - Retry logic for failed actions
    - Error handling and reporting
    """
    
    def __init__(
        self,
        dispatcher: ActionDispatcher,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the action executor.
        
        Args:
            dispatcher: The dispatcher to use for executing actions.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.
        """
        self.dispatcher = dispatcher
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def execute(
        self,
        email: Any,
        rule_match: Any,
        actions: List[Tuple[ActionType, Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Execute actions with retry logic.
        
        Args:
            email: The email to process.
            rule_match: The rule match that triggered the actions.
            actions: List of (action_type, action_params) tuples.
        
        Returns:
            List of action execution results.
        """
        import time
        
        results = []
        
        for action_type, action_params in actions:
            attempt = 0
            last_error = None
            
            while attempt <= self.max_retries:
                try:
                    result = self.dispatcher.handle_action(
                        email=email,
                        rule_match=rule_match,
                        action=action_type,
                        action_params=action_params
                    )
                    
                    if result.get("success"):
                        results.append(result)
                        break
                    else:
                        last_error = result.get("error", "Unknown error")
                        attempt += 1
                        
                        if attempt <= self.max_retries:
                            time.sleep(self.retry_delay)
                
                except Exception as e:
                    last_error = str(e)
                    attempt += 1
                    
                    if attempt <= self.max_retries:
                        time.sleep(self.retry_delay)
            
            if attempt > self.max_retries:
                results.append({
                    "success": False,
                    "action": action_type.value if hasattr(action_type, 'value') else str(action_type),
                    "error": f"Failed after {self.max_retries} retries: {last_error}",
                    "attempts": attempt
                })
        
        return results


class ActionBuilder:
    """
    Builder for constructing action configurations.
    """
    
    def __init__(self):
        """Initialize the action builder."""
        self.actions: List[tuple] = []
    
    def add_move(
        self,
        destination: str,
        priority: int = 1
    ) -> 'ActionBuilder':
        """
        Add a MOVE action.
        
        Args:
            destination: Destination directory path.
            priority: Action priority (higher = executed first).
        
        Returns:
            Self for chaining.
        """
        self.actions.append((ActionType.MOVE, {"destination": destination, "priority": priority}))
        return self
    
    def add_file(
        self,
        format: str = "eml",
        priority: int = 2
    ) -> 'ActionBuilder':
        """
        Add a FILE action.
        
        Args:
            format: Output format (eml, md, pdf).
            priority: Action priority.
        
        Returns:
            Self for chaining.
        """
        self.actions.append((ActionType.FILE, {"format": format, "priority": priority}))
        return self
    
    def add_label(
        self,
        labels: List[str],
        priority: int = 3
    ) -> 'ActionBuilder':
        """
        Add a LABEL action.
        
        Args:
            labels: List of label names to apply.
            priority: Action priority.
        
        Returns:
            Self for chaining.
        """
        self.actions.append((ActionType.LABEL, {"labels": labels, "priority": priority}))
        return self
    
    def add_notify(
        self,
        message: str = "Notification sent",
        priority: int = 4
    ) -> 'ActionBuilder':
        """
        Add a NOTIFY action.
        
        Args:
            message: Notification message.
            priority: Action priority.
        
        Returns:
            Self for chaining.
        """
        self.actions.append((ActionType.NOTIFY, {"message": message, "priority": priority}))
        return self
    
    def build(self) -> List[tuple]:
        """
        Build the action list.
        
        Returns:
            List of (action_type, action_params) tuples.
        """
        # Sort by priority (higher first)
        self.actions.sort(key=lambda x: x[1].get("priority", 0), reverse=True)
        
        # Remove priority from params
        return [(action, {k: v for k, v in params.items() if k != "priority"})
                for action, params in self.actions]


# Alias for backward compatibility
Dispatcher = ActionDispatcher
