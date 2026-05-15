"""Tests for the email_tool package."""

import pytest
from email_tool.models import (
    Email, Rule, RuleType, RuleMatch, ActionType,
    RuleMatchType, ActionExecutionResult
)
from email_tool.parser import EmailParser
from email_tool.matcher import RuleMatcher
from email_tool.dispatcher import ActionDispatcher
from email_tool.processor import (
    EmailProcessor, PipelineBuilder, PipelineExecutor,
    PipelineMonitor, PipelineConfig
)


class TestModels:
    """Test cases for model classes."""
    
    def test_email_creation(self):
        """Test Email object creation."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test Subject",
            date=None,
            body_plain="Test body",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
        
        assert email.from_addr == "sender@example.com"
        assert email.subject == "Test Subject"
        assert email.id is not None
        assert email.created_at is not None
    
    def test_email_to_eml(self):
        """Test Email to EML conversion."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test Subject",
            date=None,
            body_plain="Test body",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
        
        eml_str = email.to_eml()
        
        assert "From: sender@example.com" in eml_str
        assert "To: recipient@test.com" in eml_str
        assert "Subject: Test Subject" in eml_str
        assert "Test body" in eml_str
    
    def test_rule_creation(self):
        """Test Rule object creation."""
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="test",
            priority=50,
            category="general",
            labels=["important"]
        )
        
        assert rule.name == "test_rule"
        assert rule.rule_type == RuleType.SUBJECT_EXACT
        assert rule.priority == 50
        assert "important" in rule.labels
    
    def test_rule_match_creation(self):
        """Test RuleMatch object creation."""
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="test",
            priority=50,
            category="general",
            labels=[]
        )
        
        match = RuleMatch(
            rule=rule,
            match_type=RuleMatchType.EXACT,
            matched_value="test"
        )
        
        assert match.rule_name == "test_rule"
        assert match.match_type == RuleMatchType.EXACT
        assert match.matched_value == "test"
    
    def test_action_execution_result(self):
        """Test ActionExecutionResult object creation."""
        result = ActionExecutionResult(
            action_type=ActionType.MOVE,
            success=True,
            message="Moved successfully",
            details={"destination": "/tmp/archive"}
        )
        
        assert result.action_type == ActionType.MOVE
        assert result.success is True
        assert "Moved successfully" in result.message


class TestParser:
    """Test cases for EmailParser."""
    
    def test_parse_valid_email(self):
        """Test parsing a valid email."""
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        parser = EmailParser()
        email = parser.parse(email_content)
        
        assert email.from_addr == "sender@example.com"
        assert email.to_addrs == ["recipient@test.com"]
        assert email.subject == "Test Email"
        assert email.body_plain == "This is the email body."
    
    def test_parse_email_with_attachments(self):
        """Test parsing email with attachments."""
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Email with Attachment
Date: Mon, 15 Mar 2024 10:30:00 +0000
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="----=_Part_1"

------=_Part_1
Content-Type: text/plain

This is the email body.

------=_Part_1
Content-Type: text/plain; name="test.txt"
Content-Disposition: attachment; filename="test.txt"

file contents here
------=_Part_1--
"""
        parser = EmailParser()
        email = parser.parse(email_content)
        
        assert len(email.attachments) == 1
        assert email.attachments[0] == "test.txt"
    
    def test_parse_invalid_email(self):
        """Test parsing an invalid email."""
        invalid_content = "This is not a valid email format"
        
        parser = EmailParser()
        email = parser.parse(invalid_content)
        
        assert email is None


class TestMatcher:
    """Test cases for RuleMatcher."""
    
    def test_match_exact_subject(self):
        """Test exact subject matching."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="test",
            priority=50,
            category="general",
            labels=[]
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="test",
            date=None,
            body_plain="Test body",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
        
        matches = matcher.match(email, [rule])
        
        assert len(matches) == 1
        assert matches[0].rule_name == "test_rule"
    
    def test_match_contains_subject(self):
        """Test contains subject matching."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            priority=50,
            category="general",
            labels=[]
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="This is a test email",
            date=None,
            body_plain="Test body",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
        
        matches = matcher.match(email, [rule])
        
        assert len(matches) == 1
        assert matches[0].rule_name == "test_rule"
    
    def test_match_from_exact(self):
        """Test exact from address matching."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="sender@example.com",
            priority=50,
            category="sender",
            labels=[]
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=None,
            body_plain="Test body",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
        
        matches = matcher.match(email, [rule])
        
        assert len(matches) == 1
        assert matches[0].rule_name == "test_rule"
    
    def test_match_no_matches(self):
        """Test matching with no results."""
        matcher = RuleMatcher()
        
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="nonexistent",
            priority=50,
            category="general",
            labels=[]
        )
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="test",
            date=None,
            body_plain="Test body",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
        
        matches = matcher.match(email, [rule])
        
        assert len(matches) == 0
    
    def test_match_priority_ordering(self):
        """Test that matches are ordered by priority."""
        matcher = RuleMatcher()
        
        rules = [
            Rule(
                name="low_priority",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="test",
                priority=10,
                category="general",
                labels=[]
            ),
            Rule(
                name="high_priority",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="test",
                priority=100,
                category="general",
                labels=[]
            )
        ]
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="test",
            date=None,
            body_plain="Test body",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
        
        matches = matcher.match(email, rules)
        
        assert len(matches) == 2
        assert matches[0].rule_name == "high_priority"
        assert matches[1].rule_name == "low_priority"


class TestDispatcher:
    """Test cases for ActionDispatcher."""
    
    def test_dispatch_move_action(self):
        """Test dispatching MOVE action."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        action = (ActionType.MOVE, {"destination": "/tmp/archive"})
        result = dispatcher.dispatch(action, None)
        
        assert result.success is True
        assert result.action_type == ActionType.MOVE
    
    def test_dispatch_file_action(self):
        """Test dispatching FILE action."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        action = (ActionType.FILE, {"format": "md", "destination": "/tmp/archive"})
        result = dispatcher.dispatch(action, None)
        
        assert result.success is True
        assert result.action_type == ActionType.FILE
    
    def test_dispatch_label_action(self):
        """Test dispatching LABEL action."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        action = (ActionType.LABEL, {"labels": ["processed"]})
        result = dispatcher.dispatch(action, None)
        
        assert result.success is True
        assert result.action_type == ActionType.LABEL
    
    def test_dispatch_notify_action(self):
        """Test dispatching NOTIFY action."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        action = (ActionType.NOTIFY, {"message": "Test notification"})
        result = dispatcher.dispatch(action, None)
        
        assert result.success is True
        assert result.action_type == ActionType.NOTIFY


class TestProcessor:
    """Test cases for EmailProcessor."""
    
    def test_processor_initialization(self, tmp_path):
        """Test processor initialization."""
        processor = EmailProcessor(
            base_path=str(tmp_path),
            dry_run=True
        )
        
        assert str(processor.base_path) == str(tmp_path)
        assert processor.dry_run is True
        assert processor.collision_strategy == "rename"
        assert processor.max_retries == 3
    
    def test_processor_custom_config(self, tmp_path):
        """Test processor with custom configuration."""
        processor = EmailProcessor(
            base_path=str(tmp_path),
            dry_run=True,
            collision_strategy="number",
            max_retries=5,
            retry_delay=2.0
        )
        
        assert processor.collision_strategy == "number"
        assert processor.max_retries == 5
        assert processor.retry_delay == 2.0


class TestPipelineBuilder:
    """Test cases for PipelineBuilder."""
    
    def test_builder_default_config(self):
        """Test builder with default configuration."""
        builder = PipelineBuilder()
        processor = builder.build()
        
        assert str(processor.base_path) in ("archive", "./archive")
        assert processor.dry_run is False
        assert processor.collision_strategy == "rename"
    
    def test_builder_custom_config(self):
        """Test builder with custom configuration."""
        builder = PipelineBuilder()
        processor = (
            builder
            .set_base_path("/custom/path")
            .set_dry_run(True)
            .set_collision_strategy("number")
            .set_retry_config(max_retries=5, retry_delay=2.0)
            .build()
        )
        
        from pathlib import Path
        assert Path(processor.base_path).as_posix() == "/custom/path"
        assert processor.dry_run is True
        assert processor.collision_strategy == "number"
        assert processor.max_retries == 5
        assert processor.retry_delay == 2.0
    
    def test_builder_add_rules(self):
        """Test adding rules via builder."""
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="test",
            priority=50,
            category="general",
            labels=[]
        )
        
        builder = PipelineBuilder()
        processor = builder.add_rule(rule).build()
        
        assert len(processor.rules) == 1
        assert processor.rules[0].name == "test_rule"
    
    def test_builder_add_actions(self):
        """Test adding actions via builder."""
        action = (ActionType.MOVE, {"destination": "/tmp/archive"})
        
        builder = PipelineBuilder()
        processor = builder.add_action(action).build()
        
        assert len(processor.actions) == 1
        assert processor.actions[0][0] == ActionType.MOVE


class TestPipelineMonitor:
    """Test cases for PipelineMonitor."""
    
    def test_monitor_initialization(self):
        """Test monitor initialization."""
        processor = EmailProcessor(base_path="./archive", dry_run=True)
        monitor = PipelineMonitor(processor)
        
        assert monitor.processor == processor
        assert monitor.stats["total_processed"] == 0
        assert monitor.stats["total_success"] == 0
        assert monitor.stats["total_failed"] == 0
    
    def test_monitor_update_stats(self):
        """Test updating statistics."""
        processor = EmailProcessor(base_path="./archive", dry_run=True)
        monitor = PipelineMonitor(processor)
        
        # Simulate processing
        monitor.update_stats(
            total_processed=10,
            total_success=8,
            total_failed=2
        )
        
        assert monitor.stats["total_processed"] == 10
        assert monitor.stats["total_success"] == 8
        assert monitor.stats["total_failed"] == 2
    
    def test_monitor_get_success_rate(self):
        """Test getting success rate."""
        processor = EmailProcessor(base_path="./archive", dry_run=True)
        monitor = PipelineMonitor(processor)
        
        monitor.update_stats(
            total_processed=100,
            total_success=90,
            total_failed=10
        )
        
        success_rate = monitor.get_success_rate()
        assert success_rate == 90.0
    
    def test_monitor_get_rule_performance(self):
        """Test getting rule performance."""
        processor = EmailProcessor(base_path="./archive", dry_run=True)
        monitor = PipelineMonitor(processor)
        
        # Simulate rule matches
        monitor.update_rule_performance("rule1", 10)
        monitor.update_rule_performance("rule2", 5)
        
        performance = monitor.get_rule_performance()
        
        assert "rule1" in performance
        assert "rule2" in performance


class TestIntegration:
    """Integration test cases."""
    
    def test_full_processing_pipeline(self, tmp_path):
        """Test complete processing pipeline."""
        # Create test email
        email_content = """From: sender@example.com
To: recipient@test.com
Subject: Test Email
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is the email body.
"""
        email_path = tmp_path / "test.eml"
        email_path.write_text(email_content)
        
        # Create rules
        rules = [
            Rule(
                name="test_rule",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="Test Email",
                priority=50,
                category="general",
                labels=["important"]
            )
        ]
        
        # Create actions
        actions = [
            (ActionType.MOVE, {"destination": str(tmp_path / "archive")}),
            (ActionType.LABEL, {"labels": ["processed"]})
        ]
        
        # Create processor
        processor = EmailProcessor(
            base_path=str(tmp_path),
            dry_run=True
        )
        
        # Process email
        result = processor.process_email(str(email_path), rules, actions)
        
        # Verify results
        assert result["success"] is True
        assert len(result["matches"]) == 1
        assert len(result["actions_performed"]) == 2
        assert result["matches"][0].rule_name == "test_rule"
    
    def test_batch_processing(self, tmp_path):
        """Test batch processing of multiple emails."""
        # Create test emails
        for i in range(3):
            email_content = f"""From: sender@example.com
To: recipient@test.com
Subject: Test Email {i}
Date: Mon, 15 Mar 2024 10:30:00 +0000

This is email {i}.
"""
            email_path = tmp_path / f"test_{i}.eml"
            email_path.write_text(email_content)
        
        # Create rules
        rules = [
            Rule(
                name="test_rule",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="Test Email",
                priority=50,
                category="general",
                labels=[]
            )
        ]
        
        # Create actions
        actions = [
            (ActionType.LABEL, {"labels": ["processed"]})
        ]
        
        # Create processor
        processor = EmailProcessor(
            base_path=str(tmp_path),
            dry_run=True
        )
        
        # Process batch
        results = processor.process_batch(
            email_sources=[str(tmp_path / f"test_{i}.eml") for i in range(3)],
            rules=rules,
            actions=actions
        )
        
        # Verify results
        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert all(len(r["matches"]) == 1 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
