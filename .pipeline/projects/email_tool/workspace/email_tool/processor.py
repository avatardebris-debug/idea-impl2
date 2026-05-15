"""Processor module for the email processing pipeline."""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any
from email_tool.models import Rule, RuleMatch, ActionType


logger = logging.getLogger(__name__)


class EmailMessage:
    """
    Represents an email message with metadata and content.
    
    Attributes:
        subject: Email subject line.
        from_addr: Sender's email address.
        to_addr: Recipient's email address.
        body: Email body content.
        timestamp: Unix timestamp of when email was received.
        attachments: List of attachment filenames.
    """
    
    def __init__(
        self,
        subject: str,
        from_addr: str,
        to_addr: str,
        body: str,
        timestamp: int,
        attachments: Optional[List[str]] = None
    ):
        """
        Initialize an EmailMessage.
        
        Args:
            subject: Email subject.
            from_addr: Sender email address.
            to_addr: Recipient email address.
            body: Email body content.
            timestamp: Unix timestamp.
            attachments: Optional list of attachment filenames.
        """
        self.subject = subject
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.body = body
        self.timestamp = timestamp
        self.attachments = attachments or []
    
    def to_dict(self) -> dict:
        """
        Convert email message to dictionary.
        
        Returns:
            Dictionary representation of the email.
        """
        return {
            'subject': self.subject,
            'from_addr': self.from_addr,
            'to_addr': self.to_addr,
            'body': self.body,
            'timestamp': self.timestamp,
            'attachments': self.attachments
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EmailMessage':
        """
        Create EmailMessage from dictionary.
        
        Args:
            data: Dictionary with email data.
        
        Returns:
            EmailMessage instance.
        """
        return cls(
            subject=data['subject'],
            from_addr=data['from_addr'],
            to_addr=data['to_addr'],
            body=data['body'],
            timestamp=data['timestamp'],
            attachments=data.get('attachments', [])
        )


class EmailProcessor:
    """
    Main processor for email processing pipeline.
    
    Pipeline stages:
    1. Receive email message
    2. Apply rules to categorize email
    3. Save email to file system
    4. Track processing statistics
    """
    
    def __init__(
        self,
        base_path: str = "./archive",
        rules: Optional[List[Any]] = None,
        config: Optional[Any] = None,
        dry_run: bool = False,
        collision_strategy: str = "rename",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the email processor.
        
        Args:
            base_path: Base directory for saving emails.
            rules: Optional list of rules to apply.
            config: Optional configuration object.
            dry_run: If True, don't actually save emails.
            collision_strategy: How to handle filename collisions.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.
        """
        self.base_path = Path(base_path)
        self.rules = rules or []
        self.config = config
        self.dry_run = dry_run
        self.collision_strategy = collision_strategy
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.stats = {'processed': 0, 'errors': 0, 'rules_matched': 0}
        self.actions: List[Any] = []
        
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return self.stats.copy()
        
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {'processed': 0, 'errors': 0, 'rules_matched': 0}
    
    def process_email(self, email_message: EmailMessage) -> bool:
        """
        Process a single email message.
        
        Args:
            email_message: The email message to process.
        
        Returns:
            True if processing succeeded, False otherwise.
        """
        try:
            # Apply rules to categorize email
            self._apply_rules(email_message)
            
            # Save email to file system
            self._save_email(email_message)
            
            # Update statistics
            self.stats['processed'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_email(self, email_source, rules=None, actions=None):
        """
        Process a single email.
        
        Accepts two call styles:
        - process_email(path, rules, actions) -> dict with success/matches/actions_performed
        - process_email(email_message) -> bool (legacy)
        
        Args:
            email_source: Path to email file (str/Path) or legacy EmailMessage object.
            rules: List of rules to apply (Phase 6 API).
            actions: List of (ActionType, params) tuples (Phase 6 API).
        
        Returns:
            dict (Phase 6 API) or bool (legacy API).
        """
        from email_tool.parser import EmailParser
        from email_tool.rules import RuleEngine
        from email_tool.dispatcher import ActionDispatcher
        
        # Phase 6 API: path + rules + actions
        if isinstance(email_source, (str, Path)) and (rules is not None or actions is not None):
            rules = rules or []
            actions = actions or []
            
            try:
                # Parse email
                parser = EmailParser()
                email_obj = parser.parse(str(email_source))
                
                if email_obj is None:
                    return {"success": False, "error": "Failed to parse email", "matches": [], "actions_performed": []}
                
                # Apply rules
                engine = RuleEngine(rules=rules)
                matches = engine.evaluate(email_obj)
                
                # Execute actions
                dispatcher = ActionDispatcher(
                    base_path=str(self.base_path),
                    dry_run=self.dry_run,
                    collision_strategy=self.collision_strategy
                )
                actions_performed = []
                for action in actions:
                    result = dispatcher.dispatch(action, email_obj)
                    actions_performed.append(result)
                
                self.stats['processed'] += 1
                
                return {
                    "success": True,
                    "email": email_obj,
                    "matches": matches,
                    "actions_performed": actions_performed
                }
                
            except Exception as e:
                logger.error(f"Error processing email {email_source}: {e}")
                self.stats['errors'] += 1
                return {"success": False, "error": str(e), "matches": [], "actions_performed": []}
        
        # Legacy API: process_email(email_message) -> bool
        else:
            email_message = email_source
            try:
                self._apply_rules(email_message)
                self._save_email(email_message)
                self.stats['processed'] += 1
                return True
            except Exception as e:
                logger.error(f"Error processing email: {e}")
                self.stats['errors'] += 1
                return False
    
    def process_batch(self, email_sources, rules=None, actions=None):
        """
        Process a batch of emails.
        
        Args:
            email_sources: List of email file paths.
            rules: List of rules to apply.
            actions: List of (ActionType, params) tuples.
        
        Returns:
            List of result dicts.
        """
        results = []
        for source in email_sources:
            result = self.process_email(source, rules=rules, actions=actions)
            results.append(result)
        return results

    def scan_directory(self, path, pattern="*.eml") -> dict:
        """
        Scan a directory of emails and report matching rules.
        (Legacy API for CLI compatibility)
        """
        import glob
        from pathlib import Path
        
        results = {
            "total_files": 0,
            "matched_files": [],
            "unmatched_files": []
        }
        
        path_obj = Path(path)
        if not path_obj.exists():
            return results
            
        # Get all files matching pattern
        files = []
        if pattern == "*":
            files = [p for p in path_obj.rglob("*") if p.is_file()]
        else:
            files = list(path_obj.rglob(pattern))
            
        results["total_files"] = len(files)
        
        for file_path in files:
            # Process each file to get rule matches
            res = self.process_email(str(file_path), rules=self.rules if hasattr(self, 'rules') else None)
            
            if res and isinstance(res, dict) and res.get("success") and res.get("matches"):
                # Format for CLI output
                matches = res.get("matches", [])
                best_match = matches[0] if matches else None
                rule_name = best_match.rule_name if hasattr(best_match, "rule_name") else "unknown"
                
                results["matched_files"].append({
                    "file": str(file_path),
                    "category": "unknown",  # Could be derived from rule if needed
                    "rule_name": rule_name
                })
            else:
                results["unmatched_files"].append({
                    "file": str(file_path)
                })
                
        return results


    def _save_email(self, email_message: EmailMessage) -> bool:
        """
        Save email message to file system.
        
        Args:
            email_message: The email message to save.
        
        Returns:
            True if save succeeded, False otherwise.
        """
        try:
            # Create sender directory
            sender_dir = self.base_path / email_message.from_addr
            sender_dir.mkdir(parents=True, exist_ok=True)
            
            # Build filename
            filename = f"{email_message.timestamp}_{email_message.subject.replace(' ', '_')}.eml"
            file_path = sender_dir / filename
            
            # Write email content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Subject: {email_message.subject}\n")
                f.write(f"From: {email_message.from_addr}\n")
                f.write(f"To: {email_message.to_addr}\n")
                f.write(f"Timestamp: {email_message.timestamp}\n")
                f.write(f"Attachments: {', '.join(email_message.attachments)}\n")
                f.write(f"\nBody:\n{email_message.body}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving email: {e}")
            return False
    
    def _apply_rules(self, email_message: EmailMessage) -> Optional[str]:
        """
        Apply rules to email message.
        
        Args:
            email_message: The email message to apply rules to.
        
        Returns:
            Category string if rules matched, None otherwise.
        """
        if not self.rules:
            return None
        
        for rule in self.rules:
            if hasattr(rule, 'matches') and rule.matches(email_message):
                return rule.category
        
        return None
    
    def get_stats(self) -> dict:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics.
        """
        return self.stats.copy()


class PipelineBuilder:
    """
    Builder for constructing email processing pipelines.
    """
    
    def __init__(self):
        """Initialize the pipeline builder."""
        self.base_path = "./archive"
        self.dry_run = False
        self.collision_strategy = "rename"
        self.max_retries = 3
        self.retry_delay = 1.0
        self.rules: List[Rule] = []
        self.actions: List[tuple] = []
    
    def set_base_path(self, path: str) -> 'PipelineBuilder':
        """Set the base path for operations."""
        self.base_path = path
        return self
    
    def set_base_path_absolute(self, path: str) -> 'PipelineBuilder':
        """Set the base path for operations (absolute path)."""
        import os
        self.base_path = os.path.abspath(path)
        return self
    
    def set_dry_run(self, dry_run: bool) -> 'PipelineBuilder':
        """Set dry run mode."""
        self.dry_run = dry_run
        return self
    
    def set_collision_strategy(self, strategy: str) -> 'PipelineBuilder':
        """Set collision handling strategy."""
        self.collision_strategy = strategy
        return self
    
    def set_retry_config(
        self,
        max_retries: int,
        retry_delay: float
    ) -> 'PipelineBuilder':
        """Set retry configuration."""
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        return self
    
    def add_rule(self, rule: Rule) -> 'PipelineBuilder':
        """Add a rule to the pipeline."""
        self.rules.append(rule)
        return self
    
    def add_rules(self, rules: List[Rule]) -> 'PipelineBuilder':
        """Add multiple rules to the pipeline."""
        self.rules.extend(rules)
        return self
    
    def add_action(self, action_type_or_tuple, action_params: dict = None) -> 'PipelineBuilder':
        """
        Add an action to the pipeline.
        
        Args:
            action_type_or_tuple: Action type enum, or a tuple of (ActionType, params).
            action_params: Parameters for the action (if action_type_or_tuple is just the type).
        
        Returns:
            Self for chaining.
        """
        if isinstance(action_type_or_tuple, tuple) and len(action_type_or_tuple) == 2:
            self.actions.append(action_type_or_tuple)
        else:
            self.actions.append((action_type_or_tuple, action_params or {}))
        return self
    
    def add_actions(self, actions: List[tuple]) -> 'PipelineBuilder':
        """Add multiple actions to the pipeline."""
        self.actions.extend(actions)
        return self
    
    def build(self) -> EmailProcessor:
        """
        Build the email processor.
        
        Returns:
            Configured EmailProcessor instance.
        """
        processor = EmailProcessor(
            base_path=self.base_path,
            dry_run=self.dry_run,
            collision_strategy=self.collision_strategy,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay
        )
        processor.rules = self.rules.copy()
        processor.actions = self.actions.copy()
        return processor


class PipelineExecutor:
    """
    Executes email processing pipelines with progress tracking.
    """
    
    def __init__(
        self,
        processor: EmailProcessor,
        progress_callback=None
    ):
        """
        Initialize the pipeline executor.
        
        Args:
            processor: The email processor to use.
            progress_callback: Optional callback function for progress updates.
        """
        self.processor = processor
        self.progress_callback = progress_callback
    
    def execute(
        self,
        email_sources: List[str],
        rules: List[Rule],
        actions: List[tuple]
    ) -> List[dict]:
        """
        Execute the pipeline with progress tracking.
        
        Args:
            email_sources: List of email sources to process.
            rules: List of rules to match against.
            actions: List of actions to perform.
        
        Returns:
            List of processing results.
        """
        results = []
        total = len(email_sources)
        
        for i, source in enumerate(email_sources):
            result = self.processor.process_email(source, rules, actions)
            results.append(result)
            
            # Call progress callback if provided
            if self.progress_callback:
                self.progress_callback(i + 1, total, result)
        
        return results
    
    def execute_directory(
        self,
        source_dir: str,
        rules: List[Rule],
        actions: List[tuple],
        file_pattern: str = "*.eml"
    ) -> List[dict]:
        """
        Execute the pipeline on a directory of emails.
        
        Args:
            source_dir: Directory containing email files.
            rules: List of rules to match against.
            actions: List of actions to perform.
            file_pattern: Glob pattern for matching files.
        
        Returns:
            List of processing results.
        """
        from pathlib import Path
        source_path = Path(source_dir)
        email_files = list(source_path.glob(file_pattern))
        
        return self.execute(
            [str(f) for f in email_files],
            rules,
            actions
        )


class PipelineMonitor:
    """
    Monitors pipeline execution and provides progress information.
    """
    
    def __init__(self, processor=None):
        """Initialize the pipeline monitor.
        
        Args:
            processor: Optional EmailProcessor instance to monitor.
        """
        self.processor = processor
        self.start_time = None
        self.end_time = None
        self.total_emails = 0
        self.processed_emails = 0
        self.failed_emails = 0
        self.matched_emails = 0
        self.errors: List[str] = []
        # Phase 6 stats dict
        self.stats = {
            'total_processed': 0,
            'total_success': 0,
            'total_failed': 0,
        }
        self._rule_performance: dict = {}
    
    def start(self, total_emails: int):
        """
        Start monitoring.
        
        Args:
            total_emails: Total number of emails to process.
        """
        self.start_time = datetime.now()
        self.total_emails = total_emails
        self.processed_emails = 0
        self.failed_emails = 0
        self.matched_emails = 0
        self.errors = []
    
    def record_success(self, matched: bool):
        """
        Record a successful processing.
        
        Args:
            matched: Whether the email matched any rules.
        """
        self.processed_emails += 1
        if matched:
            self.matched_emails += 1
    
    def record_failure(self, error: str):
        """
        Record a failed processing.
        
        Args:
            error: Error message.
        """
        self.failed_emails += 1
        self.errors.append(error)
    
    def stop(self):
        """Stop monitoring."""
        self.end_time = datetime.now()
    
    def get_progress(self) -> dict:
        """
        Get current progress information.
        
        Returns:
            Dictionary with progress information.
        """
        elapsed = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        return {
            'total_emails': self.total_emails,
            'processed_emails': self.processed_emails,
            'failed_emails': self.failed_emails,
            'matched_emails': self.matched_emails,
            'elapsed_seconds': elapsed,
            'success_rate': (
                (self.processed_emails / self.total_emails * 100)
                if self.total_emails > 0 else 0
            )
        }
    
    def update_stats(self, total_processed: int = 0, total_success: int = 0, total_failed: int = 0):
        """Update processing statistics (Phase 6 API).
        
        Args:
            total_processed: Total emails processed.
            total_success: Total successes.
            total_failed: Total failures.
        """
        self.stats['total_processed'] = total_processed
        self.stats['total_success'] = total_success
        self.stats['total_failed'] = total_failed
    
    def get_success_rate(self) -> float:
        """Get success rate as a percentage (Phase 6 API).
        
        Returns:
            Success rate as percentage (0-100).
        """
        total = self.stats['total_processed']
        if total == 0:
            return 0.0
        return (self.stats['total_success'] / total) * 100
    
    def update_rule_performance(self, rule_name: str, match_count: int):
        """Track rule performance (Phase 6 API).
        
        Args:
            rule_name: Name of the rule.
            match_count: Number of times rule matched.
        """
        self._rule_performance[rule_name] = match_count
    
    def get_rule_performance(self) -> dict:
        """Get rule performance metrics (Phase 6 API).
        
        Returns:
            Dictionary mapping rule names to match counts.
        """
        return self._rule_performance.copy()


class PipelineConfig:
    """
    Configuration for email processing pipeline.
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
        Initialize pipeline configuration.
        
        Args:
            base_path: Base directory for saving emails.
            dry_run: If True, don't actually save emails.
            collision_strategy: How to handle filename collisions.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.
        """
        self.base_path = base_path
        self.dry_run = dry_run
        self.collision_strategy = collision_strategy
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration.
        """
        return {
            'base_path': self.base_path,
            'dry_run': self.dry_run,
            'collision_strategy': self.collision_strategy,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PipelineConfig':
        """
        Create configuration from dictionary.
        
        Args:
            data: Dictionary with configuration data.
        
        Returns:
            PipelineConfig instance.
        """
        return cls(
            base_path=data.get('base_path', './archive'),
            dry_run=data.get('dry_run', False),
            collision_strategy=data.get('collision_strategy', 'rename'),
            max_retries=data.get('max_retries', 3),
            retry_delay=data.get('retry_delay', 1.0)
        )
