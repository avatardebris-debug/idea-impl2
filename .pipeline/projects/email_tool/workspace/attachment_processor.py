"""Attachment processor module for the email processing pipeline."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from email_tool.models import Email, Rule, RuleMatch, ActionType
from email_tool.attachment_parsers import (
    PDFAttachmentParser,
    OfficeAttachmentParser,
    TextAttachmentParser,
    ImageAttachmentParser,
    ZipAttachmentParser
)
from email_tool.attachment_types import AttachmentType, get_attachment_type
from email_tool.attachment_parsers.base import ParsedAttachment
from email_tool.models import AttachmentProcessingResult


class AttachmentProcessor:
    """
    Main processor for attachment processing pipeline.
    
    Pipeline stages:
    1. Identify attachment type
    2. Parse attachment content
    3. Extract metadata
    4. Save processed attachments
    5. Generate processing report
    """
    
    def __init__(
        self,
        base_path: str = "./archive",
        dry_run: bool = False,
        collision_strategy: str = "rename",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the attachment processor.
        
        Args:
            base_path: Base directory for all operations.
            dry_run: If True, only simulate actions without making changes.
            collision_strategy: Strategy for handling filename collisions.
            max_retries: Maximum retry attempts for actions.
            retry_delay: Delay between retries in seconds.
        """
        self.base_path = base_path
        self.dry_run = dry_run
        self.collision_strategy = collision_strategy
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize parsers
        self.parsers = {
            'pdf': PDFAttachmentParser(base_path),
            'office': OfficeAttachmentParser(base_path),
            'text': TextAttachmentParser(base_path),
            'image': ImageAttachmentParser(base_path),
            'zip': ZipAttachmentParser(base_path)
        }
        
        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "by_type": {},
            "by_parser": {}
        }
        
        # Store results for monitoring
        self.results: List[AttachmentProcessingResult] = []
    
    def process_attachment(
        self,
        file_path: str,
        attachment_id: str,
        email_id: str,
        original_filename: str,
        content_type: str,
        size_bytes: int,
        attachment_type: AttachmentType
    ) -> AttachmentProcessingResult:
        """
        Process a single attachment through the pipeline.
        
        Args:
            file_path: Path to the attachment file.
            attachment_id: Unique ID for this attachment.
            email_id: ID of the email this attachment belongs to.
            original_filename: Original filename of the attachment.
            content_type: MIME content type of the attachment.
            size_bytes: Size of the attachment in bytes.
            attachment_type: Type of the attachment.
        
        Returns:
            AttachmentProcessingResult with processing details.
        """
        result = AttachmentProcessingResult(
            attachment_id=attachment_id,
            email_id=email_id,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            attachment_type=attachment_type,
            processed_at=datetime.now().isoformat()
        )
        
        try:
            file_path_obj = Path(file_path)
            
            # Select appropriate parser based on attachment type
            parser = self._get_parser(attachment_type)
            
            if parser:
                # Parse the attachment
                parsed = parser.parse(
                    file_path=file_path_obj,
                    attachment_id=attachment_id,
                    email_id=email_id,
                    original_filename=original_filename,
                    content_type=content_type,
                    size_bytes=size_bytes,
                    attachment_type=attachment_type
                )
                
                # Update result with parsed data
                result.text_content = parsed.text_content
                result.metadata = parsed.metadata
                result.success = parsed.success
                
                if parsed.success:
                    self.stats["total_successful"] += 1
                    self.stats["by_parser"][parser.get_parser_name()] = \
                        self.stats["by_parser"].get(parser.get_parser_name(), 0) + 1
                else:
                    self.stats["total_failed"] += 1
                    result.error_message = parsed.error_message
                    
            else:
                # No parser available for this type
                result.success = False
                result.error_message = f"No parser available for attachment type: {attachment_type}"
                self.stats["total_failed"] += 1
            
            # Update type statistics
            type_name = attachment_type.name
            self.stats["by_type"][type_name] = \
                self.stats["by_type"].get(type_name, 0) + 1
            
            # Store result
            self.results.append(result)
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            self.stats["total_failed"] += 1
            self.results.append(result)
        
        # Update total processed
        self.stats["total_processed"] += 1
        
        return result
    
    def process_email_attachments(
        self,
        email: Email,
        attachments: List[str]
    ) -> List[AttachmentProcessingResult]:
        """
        Process all attachments from an email.
        
        Args:
            email: The email object containing attachments.
            attachments: List of attachment file paths.
        
        Returns:
            List of AttachmentProcessingResult objects.
        """
        results = []
        
        for i, file_path in enumerate(attachments):
            # Determine attachment type
            attachment_type = get_attachment_type(
                mime_type=email.raw_headers.get('Content-Type', ''),
                filename=os.path.basename(file_path)
            )
            
            # Process the attachment
            result = self.process_attachment(
                file_path=file_path,
                attachment_id=f"{email.id}_att_{i+1}",
                email_id=email.id,
                original_filename=os.path.basename(file_path),
                content_type=email.raw_headers.get('Content-Type', 'application/octet-stream'),
                size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                attachment_type=attachment_type
            )
            
            results.append(result)
        
        return results
    
    def _get_parser(self, attachment_type: AttachmentType) -> Optional[Any]:
        """
        Get the appropriate parser for an attachment type.
        
        Args:
            attachment_type: Type of the attachment.
        
        Returns:
            Parser instance or None if no parser available.
        """
        if attachment_type == AttachmentType.PDF:
            return self.parsers['pdf']
        elif attachment_type in [AttachmentType.DOCX, AttachmentType.XLSX, AttachmentType.PPTX]:
            return self.parsers['office']
        elif attachment_type in [AttachmentType.TXT, AttachmentType.CSV]:
            return self.parsers['text']
        elif attachment_type in [AttachmentType.PNG, AttachmentType.JPG, AttachmentType.GIF, AttachmentType.BMP, AttachmentType.TIFF]:
            return self.parsers['image']
        elif attachment_type == AttachmentType.ZIP:
            return self.parsers['zip']
        else:
            return None
    
    def get_stats(self) -> dict:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics.
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "by_type": {},
            "by_parser": {}
        }
    
    def get_results(self) -> List[AttachmentProcessingResult]:
        """
        Get all processing results.
        
        Returns:
            List of AttachmentProcessingResult objects.
        """
        return self.results.copy()
    
    def clear_results(self):
        """Clear all processing results."""
        self.results = []


class AttachmentDispatcher:
    """
    Dispatcher for attachment actions (save, move, etc.).
    """
    
    def __init__(
        self,
        base_path: str = "./archive",
        dry_run: bool = False,
        collision_strategy: str = "rename"
    ):
        """
        Initialize the attachment dispatcher.
        
        Args:
            base_path: Base directory for all operations.
            dry_run: If True, only simulate actions without making changes.
            collision_strategy: Strategy for handling filename collisions.
        """
        self.base_path = base_path
        self.dry_run = dry_run
        self.collision_strategy = collision_strategy
        self.operations_log: List[Dict[str, Any]] = []
    
    def save_attachment(
        self,
        file_path: str,
        target_path: str,
        attachment_id: str
    ) -> Dict[str, Any]:
        """
        Save an attachment to a target location.
        
        Args:
            file_path: Source path of the attachment.
            target_path: Target path for the attachment.
            attachment_id: ID of the attachment.
        
        Returns:
            Dictionary with operation result.
        """
        operation = {
            "operation": "save",
            "attachment_id": attachment_id,
            "source": file_path,
            "target": target_path,
            "dry_run": self.dry_run,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Create target directory if it doesn't exist
            target_dir = os.path.dirname(target_path)
            if target_dir and not self.dry_run:
                os.makedirs(target_dir, exist_ok=True)
            
            # Handle filename collisions
            if os.path.exists(target_path) and not self.dry_run:
                target_path = self._handle_collision(target_path)
            
            # Copy the file
            if not self.dry_run:
                shutil.copy2(file_path, target_path)
            
            operation["success"] = True
            operation["final_path"] = target_path
            
        except Exception as e:
            operation["success"] = False
            operation["error"] = str(e)
        
        self.operations_log.append(operation)
        return operation
    
    def move_attachment(
        self,
        file_path: str,
        target_path: str,
        attachment_id: str
    ) -> Dict[str, Any]:
        """
        Move an attachment to a target location.
        
        Args:
            file_path: Source path of the attachment.
            target_path: Target path for the attachment.
            attachment_id: ID of the attachment.
        
        Returns:
            Dictionary with operation result.
        """
        operation = {
            "operation": "move",
            "attachment_id": attachment_id,
            "source": file_path,
            "target": target_path,
            "dry_run": self.dry_run,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Create target directory if it doesn't exist
            target_dir = os.path.dirname(target_path)
            if target_dir and not self.dry_run:
                os.makedirs(target_dir, exist_ok=True)
            
            # Handle filename collisions
            if os.path.exists(target_path) and not self.dry_run:
                target_path = self._handle_collision(target_path)
            
            # Move the file
            if not self.dry_run:
                shutil.move(file_path, target_path)
            
            operation["success"] = True
            operation["final_path"] = target_path
            
        except Exception as e:
            operation["success"] = False
            operation["error"] = str(e)
        
        self.operations_log.append(operation)
        return operation
    
    def delete_attachment(
        self,
        file_path: str,
        attachment_id: str
    ) -> Dict[str, Any]:
        """
        Delete an attachment.
        
        Args:
            file_path: Path to the attachment file.
            attachment_id: ID of the attachment.
        
        Returns:
            Dictionary with operation result.
        """
        operation = {
            "operation": "delete",
            "attachment_id": attachment_id,
            "source": file_path,
            "dry_run": self.dry_run,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if not self.dry_run:
                os.remove(file_path)
            
            operation["success"] = True
            
        except Exception as e:
            operation["success"] = False
            operation["error"] = str(e)
        
        self.operations_log.append(operation)
        return operation
    
    def _handle_collision(self, target_path: str) -> str:
        """
        Handle filename collision based on strategy.
        
        Args:
            target_path: Original target path.
        
        Returns:
            New target path with collision handled.
        """
        if self.collision_strategy == "rename":
            # Add timestamp to filename
            path_obj = Path(target_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{path_obj.stem}_{timestamp}{path_obj.suffix}"
            return str(path_obj.parent / new_name)
        
        elif self.collision_strategy == "overwrite":
            return target_path
        
        elif self.collision_strategy == "skip":
            # Return original path, caller should check if file exists
            return target_path
        
        else:
            # Default to rename
            path_obj = Path(target_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{path_obj.stem}_{timestamp}{path_obj.suffix}"
            return str(path_obj.parent / new_name)
    
    def get_operations_log(self) -> List[Dict[str, Any]]:
        """
        Get the operation log.
        
        Returns:
            List of operation results.
        """
        return self.operations_log.copy()
    
    def clear_operations_log(self):
        """Clear the operation log."""
        self.operations_log = []


class AttachmentActionExecutor:
    """
    Executor for attachment actions.
    """
    
    def __init__(
        self,
        dispatcher: AttachmentDispatcher,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the attachment action executor.
        
        Args:
            dispatcher: The attachment dispatcher to use.
            max_retries: Maximum retry attempts for actions.
            retry_delay: Delay between retries in seconds.
        """
        self.dispatcher = dispatcher
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def execute(
        self,
        file_path: str,
        action_type: str,
        action_params: Dict[str, Any],
        attachment_id: str
    ) -> Dict[str, Any]:
        """
        Execute an attachment action.
        
        Args:
            file_path: Path to the attachment file.
            action_type: Type of action to execute.
            action_params: Parameters for the action.
            attachment_id: ID of the attachment.
        
        Returns:
            Dictionary with execution result.
        """
        result = {
            "action": action_type,
            "attachment_id": attachment_id,
            "success": False,
            "message": "",
            "details": {}
        }
        
        attempt = 0
        while attempt < self.max_retries:
            try:
                if action_type == "save":
                    target_path = action_params.get("target_path", file_path)
                    operation = self.dispatcher.save_attachment(
                        file_path=file_path,
                        target_path=target_path,
                        attachment_id=attachment_id
                    )
                    result["success"] = operation["success"]
                    result["message"] = "Attachment saved successfully" if operation["success"] else "Failed to save attachment"
                    result["details"] = {"final_path": operation.get("final_path", "")}
                
                elif action_type == "move":
                    target_path = action_params.get("target_path", file_path)
                    operation = self.dispatcher.move_attachment(
                        file_path=file_path,
                        target_path=target_path,
                        attachment_id=attachment_id
                    )
                    result["success"] = operation["success"]
                    result["message"] = "Attachment moved successfully" if operation["success"] else "Failed to move attachment"
                    result["details"] = {"final_path": operation.get("final_path", "")}
                
                elif action_type == "delete":
                    operation = self.dispatcher.delete_attachment(
                        file_path=file_path,
                        attachment_id=attachment_id
                    )
                    result["success"] = operation["success"]
                    result["message"] = "Attachment deleted successfully" if operation["success"] else "Failed to delete attachment"
                
                else:
                    result["message"] = f"Unknown action type: {action_type}"
                
                if result["success"]:
                    break
                
                attempt += 1
                if attempt < self.max_retries:
                    import time
                    time.sleep(self.retry_delay)
                
            except Exception as e:
                attempt += 1
                if attempt >= self.max_retries:
                    result["message"] = f"Action failed after {self.max_retries} attempts: {str(e)}"
                else:
                    import time
                    time.sleep(self.retry_delay)
        
        return result


class AttachmentPipelineBuilder:
    """
    Builder for constructing attachment processing pipelines.
    """
    
    def __init__(self):
        """Initialize the attachment pipeline builder."""
        self.base_path = "./archive"
        self.dry_run = False
        self.collision_strategy = "rename"
        self.max_retries = 3
        self.retry_delay = 1.0
        self.save_path: Optional[str] = None
    
    def set_base_path(self, path: str) -> 'AttachmentPipelineBuilder':
        """Set the base path for operations."""
        self.base_path = path
        return self
    
    def set_base_path_absolute(self, path: str) -> 'AttachmentPipelineBuilder':
        """Set the base path for operations (absolute path)."""
        import os
        self.base_path = os.path.abspath(path)
        return self
    
    def set_dry_run(self, dry_run: bool) -> 'AttachmentPipelineBuilder':
        """Set dry run mode."""
        self.dry_run = dry_run
        return self
    
    def set_collision_strategy(self, strategy: str) -> 'AttachmentPipelineBuilder':
        """Set collision handling strategy."""
        self.collision_strategy = strategy
        return self
    
    def set_save_path(self, path: str) -> 'AttachmentPipelineBuilder':
        """Set the save path for processed attachments."""
        self.save_path = path
        return self
    
    def set_retry_config(
        self,
        max_retries: int,
        retry_delay: float
    ) -> 'AttachmentPipelineBuilder':
        """Set retry configuration."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        return self
    
    def build(self) -> 'AttachmentPipelineExecutor':
        """
        Build the attachment pipeline executor.
        
        Returns:
            Configured AttachmentPipelineExecutor instance.
        """
        processor = AttachmentProcessor(
            base_path=self.base_path,
            dry_run=self.dry_run,
            collision_strategy=self.collision_strategy,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay
        )
        
        dispatcher = AttachmentDispatcher(
            base_path=self.base_path,
            dry_run=self.dry_run,
            collision_strategy=self.collision_strategy
        )
        
        executor = AttachmentActionExecutor(
            dispatcher=dispatcher,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay
        )
        
        return AttachmentPipelineExecutor(
            processor=processor,
            dispatcher=dispatcher,
            executor=executor,
            save_path=self.save_path
        )


class AttachmentPipelineExecutor:
    """
    Executes attachment processing pipelines with progress tracking.
    """
    
    def __init__(
        self,
        processor: AttachmentProcessor,
        dispatcher: AttachmentDispatcher,
        executor: AttachmentActionExecutor,
        save_path: Optional[str] = None,
        progress_callback=None
    ):
        """
        Initialize the attachment pipeline executor.
        
        Args:
            processor: The attachment processor to use.
            dispatcher: The attachment dispatcher to use.
            executor: The attachment action executor to use.
            save_path: Path to save processed attachments.
            progress_callback: Optional callback function for progress updates.
        """
        self.processor = processor
        self.dispatcher = dispatcher
        self.executor = executor
        self.save_path = save_path
        self.progress_callback = progress_callback
    
    def execute(
        self,
        email: Email,
        attachments: List[str],
        action_type: str = "save",
        action_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute the attachment processing pipeline.
        
        Args:
            email: The email object containing attachments.
            attachments: List of attachment file paths.
            action_type: Type of action to perform (save, move, delete).
            action_params: Parameters for the action.
        
        Returns:
            List of execution results.
        """
        if action_params is None:
            action_params = {}
        
        results = []
        total = len(attachments)
        
        for i, file_path in enumerate(attachments):
            # Process the attachment
            result = self.processor.process_attachment(
                file_path=file_path,
                attachment_id=f"{email.id}_att_{i+1}",
                email_id=email.id,
                original_filename=os.path.basename(file_path),
                content_type=email.raw_headers.get('Content-Type', 'application/octet-stream'),
                size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                attachment_type=get_attachment_type(
                    mime_type=email.raw_headers.get('Content-Type', ''),
                    filename=os.path.basename(file_path)
                )
            )
            
            # Execute action if successful
            if result.success:
                # Determine target path
                target_path = action_params.get("target_path", "")
                if not target_path:
                    target_path = self._generate_target_path(file_path)
                
                action_result = self.executor.execute(
                    file_path=file_path,
                    action_type=action_type,
                    action_params={"target_path": target_path},
                    attachment_id=result.attachment_id
                )
                
                result.details = action_result.get("details", {})
                result.success = action_result["success"]
            
            results.append({
                "attachment_id": result.attachment_id,
                "original_filename": result.original_filename,
                "attachment_type": result.attachment_type.name,
                "success": result.success,
                "message": result.error_message or "Success",
                "details": result.details
            })
            
            # Call progress callback if provided
            if self.progress_callback:
                self.progress_callback(i + 1, total, result)
        
        return results
    
    def _generate_target_path(self, file_path: str) -> str:
        """
        Generate a target path for saving an attachment.
        
        Args:
            file_path: Original file path.
        
        Returns:
            Target path for the attachment.
        """
        if self.save_path:
            return os.path.join(self.save_path, os.path.basename(file_path))
        
        # Default to same directory
        return file_path


class AttachmentPipelineMonitor:
    """
    Monitors and reports on attachment processing pipeline execution.
    """
    
    def __init__(self, processor: AttachmentProcessor):
        """
        Initialize the attachment pipeline monitor.
        
        Args:
            processor: The attachment processor to monitor.
        """
        self.processor = processor
        self.stats = {
            "total_processed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "by_type": {},
            "by_parser": {}
        }
    
    def update_stats(self, **kwargs):
        """
        Update statistics from the processor or with provided values.
        
        Args:
            **kwargs: Optional keyword arguments to update stats.
        """
        if kwargs:
            # Update with provided values
            for key, value in kwargs.items():
                if key in self.stats:
                    self.stats[key] = value
        else:
            # Update from processor
            self.stats = self.processor.get_stats()
    
    def get_status(self) -> dict:
        """
        Get current pipeline status.
        
        Returns:
            Dictionary with status information.
        """
        self.update_stats()
        
        return {
            "total_processed": self.stats["total_processed"],
            "total_successful": self.stats["total_successful"],
            "total_failed": self.stats["total_failed"],
            "success_rate": self._calculate_success_rate(self.stats),
            "by_type": self.stats["by_type"],
            "by_parser": self.stats["by_parser"],
            "last_updated": datetime.now().isoformat()
        }
    
    def _calculate_success_rate(self, stats: dict) -> float:
        """Calculate success rate from statistics."""
        total = stats["total_processed"]
        if total == 0:
            return 0.0
        return (stats["total_successful"] / total) * 100
    
    def get_parser_performance(self) -> dict:
        """
        Get performance metrics for each parser.
        
        Returns:
            Dictionary with parser performance metrics.
        """
        self.update_stats()
        
        performance = {}
        for parser_name, count in self.stats["by_parser"].items():
            performance[parser_name] = {
                "processed": count,
                "percentage": (count / max(self.stats["total_processed"], 1)) * 100
            }
        
        return performance
    
    def get_type_performance(self) -> dict:
        """
        Get performance metrics for each attachment type.
        
        Returns:
            Dictionary with attachment type performance metrics.
        """
        self.update_stats()
        
        performance = {}
        for type_name, count in self.stats["by_type"].items():
            performance[type_name] = {
                "processed": count,
                "percentage": (count / max(self.stats["total_processed"], 1)) * 100
            }
        
        return performance


class AttachmentPipelineConfig:
    """
    Configuration for attachment processing pipeline.
    """
    
    def __init__(
        self,
        base_path: str = "./archive",
        dry_run: bool = False,
        collision_strategy: str = "rename",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        save_path: Optional[str] = None
    ):
        """
        Initialize attachment pipeline configuration.
        
        Args:
            base_path: Base directory for operations.
            dry_run: Enable dry run mode.
            collision_strategy: Strategy for filename collisions.
            max_retries: Maximum retry attempts.
            retry_delay: Delay between retries.
            save_path: Path to save processed attachments.
        """
        self.base_path = base_path
        self.dry_run = dry_run
        self.collision_strategy = collision_strategy
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.save_path = save_path
    
    def to_executor(self) -> AttachmentPipelineExecutor:
        """
        Convert configuration to AttachmentPipelineExecutor instance.
        
        Returns:
            Configured AttachmentPipelineExecutor.
        """
        processor = AttachmentProcessor(
            base_path=self.base_path,
            dry_run=self.dry_run,
            collision_strategy=self.collision_strategy,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay
        )
        
        dispatcher = AttachmentDispatcher(
            base_path=self.base_path,
            dry_run=self.dry_run,
            collision_strategy=self.collision_strategy
        )
        
        executor = AttachmentActionExecutor(
            dispatcher=dispatcher,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay
        )
        
        return AttachmentPipelineExecutor(
            processor=processor,
            dispatcher=dispatcher,
            executor=executor,
            save_path=self.save_path
        )
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'AttachmentPipelineConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary with configuration values.
        
        Returns:
            AttachmentPipelineConfig instance.
        """
        return cls(
            base_path=config_dict.get("base_path", "./archive"),
            dry_run=config_dict.get("dry_run", False),
            collision_strategy=config_dict.get("collision_strategy", "rename"),
            max_retries=config_dict.get("max_retries", 3),
            retry_delay=config_dict.get("retry_delay", 1.0),
            save_path=config_dict.get("save_path")
        )
    
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary with configuration values.
        """
        return {
            "base_path": self.base_path,
            "dry_run": self.dry_run,
            "collision_strategy": self.collision_strategy,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "save_path": self.save_path
        }
