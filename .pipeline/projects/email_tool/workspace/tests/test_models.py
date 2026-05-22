"""Tests for Email Tool models.

This module contains comprehensive tests for all data models including
Rule, Action, Email, and related classes.
"""

import pytest
from datetime import datetime
from email_tool.models import (
    Rule, RuleType,
    Action, ActionType,
    Email, EmailMatch, EmailProcessingResult,
    EmailMetadata, ProcessingStats,
    RuleSet, ActionSet,
    ProcessingConfig,
    RuleMatch, RuleMatchStrategy, RuleMatchType,
    Category, ActionExecutionResult
)


class TestRule:
    """Tests for Rule dataclass."""
    
    def test_rule_creation(self):
        """Test basic rule creation."""
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            priority=75,
            category="testing",
            description="A test rule"
        )
        
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.SUBJECT_CONTAINS
        assert rule.pattern == "test"
        assert rule.priority == 75
        assert rule.category == "testing"
        assert rule.description == "A test rule"
        assert rule.enabled is True
    
    def test_rule_default_values(self):
        """Test rule with default values."""
        rule = Rule(name="Default Rule", rule_type=RuleType.FROM_EXACT)
        
        assert rule.pattern is None
        assert rule.priority == 50
        assert rule.category == "general"
        assert rule.labels == []
        assert rule.description == ""
        assert rule.enabled is True
    
    def test_rule_invalid_priority_low(self):
        """Test rule with priority below minimum."""
        with pytest.raises(ValueError, match="Priority must be between 0 and 100"):
            Rule(name="Invalid Rule", rule_type=RuleType.FROM_EXACT, priority=-1)
    
    def test_rule_invalid_priority_high(self):
        """Test rule with priority above maximum."""
        with pytest.raises(ValueError, match="Priority must be between 0 and 100"):
            Rule(name="Invalid Rule", rule_type=RuleType.FROM_EXACT, priority=101)
    
    def test_rule_to_dict(self):
        """Test rule serialization to dictionary."""
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            priority=75,
            category="testing",
            labels=["label1", "label2"],
            description="A test rule",
            enabled=False
        )
        
        result = rule.to_dict()
        
        assert result["name"] == "Test Rule"
        assert result["rule_type"] == "subject_contains"
        assert result["pattern"] == "test"
        assert result["priority"] == 75
        assert result["category"] == "testing"
        assert result["labels"] == ["label1", "label2"]
        assert result["description"] == "A test rule"
        assert result["enabled"] is False
    
    def test_rule_from_dict(self):
        """Test rule deserialization from dictionary."""
        data = {
            "name": "Test Rule",
            "rule_type": "subject_contains",
            "pattern": "test",
            "priority": 75,
            "category": "testing",
            "labels": ["label1"],
            "description": "A test rule",
            "enabled": False
        }
        
        rule = Rule.from_dict(data)
        
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.SUBJECT_CONTAINS
        assert rule.pattern == "test"
        assert rule.priority == 75
        assert rule.category == "testing"
        assert rule.labels == ["label1"]
        assert rule.description == "A test rule"
        assert rule.enabled is False
    
    def test_rule_from_dict_missing_optional_fields(self):
        """Test rule from dict with missing optional fields."""
        data = {
            "name": "Minimal Rule",
            "rule_type": "from_exact"
        }
        
        rule = Rule.from_dict(data)
        
        assert rule.name == "Minimal Rule"
        assert rule.rule_type == RuleType.FROM_EXACT
        assert rule.pattern is None
        assert rule.priority == 50
        assert rule.category == "general"
        assert rule.labels == []
        assert rule.description == ""
        assert rule.enabled is True


class TestAction:
    """Tests for Action dataclass."""
    
    def test_action_creation(self):
        """Test basic action creation."""
        action = Action(
            action_type=ActionType.MOVE,
            params={"destination": "inbox"},
            description="Move to inbox",
            enabled=True
        )
        
        assert action.action_type == ActionType.MOVE
        assert action.params == {"destination": "inbox"}
        assert action.description == "Move to inbox"
        assert action.enabled is True
    
    def test_action_default_values(self):
        """Test action with default values."""
        action = Action(action_type=ActionType.MARK_READ)
        
        assert action.params == {}
        assert action.description == ""
        assert action.enabled is True
    
    def test_action_to_dict(self):
        """Test action serialization to dictionary."""
        action = Action(
            action_type=ActionType.FORWARD,
            params={"email": "test@example.com"},
            description="Forward test",
            enabled=False
        )
        
        result = action.to_dict()
        
        assert result["action_type"] == "forward"
        assert result["params"] == {"email": "test@example.com"}
        assert result["description"] == "Forward test"
        assert result["enabled"] is False
    
    def test_action_from_dict(self):
        """Test action deserialization from dictionary."""
        data = {
            "action_type": "forward",
            "params": {"email": "test@example.com"},
            "description": "Forward test",
            "enabled": False
        }
        
        action = Action.from_dict(data)
        
        assert action.action_type == ActionType.FORWARD
        assert action.params == {"email": "test@example.com"}
        assert action.description == "Forward test"
        assert action.enabled is False
    
    def test_action_from_dict_missing_optional_fields(self):
        """Test action from dict with missing optional fields."""
        data = {
            "action_type": "mark_read"
        }
        
        action = Action.from_dict(data)
        
        assert action.action_type == ActionType.MARK_READ
        assert action.params == {}
        assert action.description == ""
        assert action.enabled is True


class TestEmail:
    """Tests for Email dataclass."""
    
    def test_email_creation(self):
        """Test basic email creation."""
        email = Email(
            id="msg123",
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            date=datetime(2024, 1, 15, 10, 30, 0),
            body_plain="Test body",
            attachments=["file.txt"],
            labels=["inbox", "important"]
        )
        
        assert email.id == "msg123"
        assert email.from_addr == "sender@example.com"
        assert email.to_addrs == ["recipient@example.com"]
        assert email.subject == "Test Subject"
        assert email.body_plain == "Test body"
        assert email.attachments == ["file.txt"]
        assert email.labels == ["inbox", "important"]
        assert email.created_at is not None
    
    def test_email_default_values(self):
        """Test email with default values."""
        email = Email()
        
        assert email.id is None
        assert email.from_addr == ""
        assert email.to_addrs == []
        assert email.subject == ""
        assert email.date is None
        assert email.body_plain is None
        assert email.body_html is None
        assert email.attachments == []
        assert email.raw_headers == {}
        assert email.labels == []
        assert email.source_path is None
        assert email.created_at is not None
    
    def test_email_to_eml(self):
        """Test email serialization to EML format."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            date=datetime(2024, 1, 15, 10, 30, 0),
            body_plain="Test body content"
        )
        
        eml = email.to_eml()
        
        assert "From: sender@example.com" in eml
        assert "To: recipient@example.com" in eml
        assert "Subject: Test Subject" in eml
        assert "Test body content" in eml
    
    def test_email_repr(self):
        """Test email string representation."""
        email = Email(
            id="msg123",
            from_addr="sender@example.com",
            subject="Test Subject"
        )
        
        repr_str = repr(email)
        assert "msg123" in repr_str
        assert "sender@example.com" in repr_str
        assert "Test Subject" in repr_str


class TestEmailMetadata:
    """Tests for EmailMetadata dataclass."""
    
    def test_email_metadata_creation(self):
        """Test email metadata creation."""
        metadata = EmailMetadata(
            subject="Test Subject",
            from_email="sender@example.com",
            from_name="Sender Name",
            to_emails=["recipient@example.com"],
            cc_emails=[],
            bcc_emails=[],
            date=datetime(2024, 1, 15, 10, 30, 0),
            message_id="<msg123@example.com>",
            size_bytes=1024,
            has_attachments=True,
            attachment_names=["file.txt"],
            labels=["inbox"]
        )
        
        assert metadata.subject == "Test Subject"
        assert metadata.from_email == "sender@example.com"
        assert metadata.from_name == "Sender Name"
        assert metadata.to_emails == ["recipient@example.com"]
        assert metadata.has_attachments is True
        assert metadata.attachment_names == ["file.txt"]
    
    def test_email_metadata_to_dict(self):
        """Test email metadata serialization."""
        metadata = EmailMetadata(
            subject="Test",
            from_email="sender@example.com",
            from_name="Sender",
            to_emails=["recipient@example.com"],
            cc_emails=[],
            bcc_emails=[],
            date=datetime(2024, 1, 15, 10, 30, 0),
            message_id="<msg123@example.com>",
            size_bytes=1024,
            has_attachments=False,
            attachment_names=[],
            labels=["inbox"],
            body_text="Body text",
            headers={"X-Custom": "value"}
        )
        
        result = metadata.to_dict()
        
        assert result["subject"] == "Test"
        assert result["from_email"] == "sender@example.com"
        assert result["body_text"] == "Body text"
        assert result["headers"] == {"X-Custom": "value"}
        assert "timestamp" in result
        assert "size_bytes" in result


class TestProcessingStats:
    """Tests for ProcessingStats dataclass."""
    
    def test_processing_stats_creation(self):
        """Test processing stats creation."""
        stats = ProcessingStats(
            total_emails=100,
            processed_emails=95,
            successful_emails=90,
            failed_emails=5,
            matched_emails=80,
            total_rules=10,
            total_actions=15
        )
        
        assert stats.total_emails == 100
        assert stats.processed_emails == 95
        assert stats.successful_emails == 90
        assert stats.failed_emails == 5
        assert stats.matched_emails == 80
        assert stats.total_rules == 10
        assert stats.total_actions == 15
        assert stats.success_rate == 94.73684210526316  # 90/95 * 100
    
    def test_processing_stats_empty(self):
        """Test empty processing stats."""
        stats = ProcessingStats()
        
        assert stats.total_emails == 0
        assert stats.processed_emails == 0
        assert stats.success_rate == 0.0
    
    def test_processing_stats_add_error(self):
        """Test error tracking."""
        stats = ProcessingStats()
        
        stats.add_error("validation_error")
        stats.add_error("validation_error")
        stats.add_error("timeout_error")
        
        assert stats.errors_by_type == {
            "validation_error": 2,
            "timeout_error": 1
        }
    
    def test_processing_stats_to_dict(self):
        """Test stats serialization."""
        stats = ProcessingStats(
            total_emails=100,
            processed_emails=100,
            successful_emails=100,
            matched_emails=50,
            total_rules=10,
            total_actions=20,
            total_processing_time_ms=5000.0,
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            end_time=datetime(2024, 1, 15, 10, 5, 0)
        )
        
        result = stats.to_dict()
        
        assert result["total_emails"] == 100
        assert result["success_rate"] == 100.0
        assert result["total_processing_time_ms"] == 5000.0
        assert "start_time" in result
        assert "end_time" in result


class TestRuleSet:
    """Tests for RuleSet dataclass."""
    
    def test_rule_set_creation(self):
        """Test rule set creation."""
        rule_set = RuleSet(
            name="Test Rules",
            description="A test rule set"
        )
        
        assert rule_set.name == "Test Rules"
        assert rule_set.description == "A test rules"
        assert len(rule_set.rules) == 0
        assert rule_set.created_at is not None
        assert rule_set.updated_at is not None
    
    def test_rule_set_add_rule(self):
        """Test adding rules to rule set."""
        rule_set = RuleSet(name="Test Rules")
        rule = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        
        rule_set.add_rule(rule)
        
        assert len(rule_set.rules) == 1
        assert rule_set.rules[0].name == "Rule 1"
        assert rule_set.updated_at > rule_set.created_at
    
    def test_rule_set_remove_rule(self):
        """Test removing rules from rule set."""
        rule_set = RuleSet(name="Test Rules")
        rule1 = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule2 = Rule(name="Rule 2", rule_type=RuleType.SUBJECT_CONTAINS)
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        
        result = rule_set.remove_rule("Rule 1")
        
        assert result is True
        assert len(rule_set.rules) == 1
        assert rule_set.rules[0].name == "Rule 2"
    
    def test_rule_set_remove_rule_not_found(self):
        """Test removing non-existent rule."""
        rule_set = RuleSet(name="Test Rules")
        rule = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule_set.add_rule(rule)
        
        result = rule_set.remove_rule("Non-existent")
        
        assert result is False
        assert len(rule_set.rules) == 1
    
    def test_rule_set_get_rule(self):
        """Test getting a rule by name."""
        rule_set = RuleSet(name="Test Rules")
        rule1 = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule2 = Rule(name="Rule 2", rule_type=RuleType.SUBJECT_CONTAINS)
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        
        result = rule_set.get_rule("Rule 1")
        
        assert result is not None
        assert result.name == "Rule 1"
        
        result = rule_set.get_rule("Non-existent")
        
        assert result is None
    
    def test_rule_set_to_dict(self):
        """Test rule set serialization."""
        rule_set = RuleSet(
            name="Test Rules",
            description="A test rule set"
        )
        rule = Rule(name="Rule 1", rule_type=RuleType.FROM_EXACT)
        rule_set.add_rule(rule)
        
        result = rule_set.to_dict()
        
        assert result["name"] == "Test Rules"
        assert result["description"] == "A test rule set"
        assert len(result["rules"]) == 1
        assert result["rules"][0]["name"] == "Rule 1"


class TestActionSet:
    """Tests for ActionSet dataclass."""
    
    def test_action_set_creation(self):
        """Test action set creation."""
        action_set = ActionSet(
            name="Test Actions",
            description="A test action set"
        )
        
        assert action_set.name == "Test Actions"
        assert action_set.description == "A test action set"
        assert len(action_set.actions) == 0
    
    def test_action_set_add_action(self):
        """Test adding actions to action set."""
        action_set = ActionSet(name="Test Actions")
        action = Action(action_type=ActionType.MOVE)
        
        action_set.add_action(action)
        
        assert len(action_set.actions) == 1
        assert action_set.actions[0].action_type == ActionType.MOVE
    
    def test_action_set_remove_action(self):
        """Test removing actions from action set."""
        action_set = ActionSet(name="Test Actions")
        action1 = Action(action_type=ActionType.MOVE)
        action2 = Action(action_type=ActionType.MARK_READ)
        
        action_set.add_action(action1)
        action_set.add_action(action2)
        
        result = action_set.remove_action("Move Action")
        
        assert result is False  # Name doesn't match
        
        result = action_set.remove_action("mark_read")
        
        assert result is True
        assert len(action_set.actions) == 1


class TestProcessingConfig:
    """Tests for ProcessingConfig dataclass."""
    
    def test_processing_config_creation(self):
        """Test processing config creation."""
        config = ProcessingConfig(
            rule_set_name="Test Rules",
            action_set_name="Test Actions",
            output_format="eml",
            collision_strategy="rename"
        )
        
        assert config.rule_set_name == "Test Rules"
        assert config.action_set_name == "Test Actions"
        assert config.output_format == "eml"
        assert config.collision_strategy == "rename"
        assert config.match_strategy == RuleMatchStrategy.PRIORITY
    
    def test_processing_config_default_values(self):
        """Test processing config with default values."""
        config = ProcessingConfig()
        
        assert config.rule_set_name is None
        assert config.action_set_name is None
        assert config.output_format == "eml"
        assert config.collision_strategy == "rename"
        assert config.match_strategy == RuleMatchStrategy.PRIORITY
        assert config.match_type == RuleMatchType.ANY
        assert config.parallel_processing is False
        assert config.max_concurrent == 4


class TestRuleMatch:
    """Tests for RuleMatch dataclass."""
    
    def test_rule_match_creation(self):
        """Test rule match creation."""
        match = RuleMatch(
            rule_name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            match_type=RuleMatchType.ANY,
            matched_value="test",
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        assert match.rule_name == "Test Rule"
        assert match.rule_type == RuleType.SUBJECT_CONTAINS
        assert match.match_type == RuleMatchType.ANY
        assert match.matched_value == "test"
        assert match.timestamp is not None
    
    def test_rule_match_to_dict(self):
        """Test rule match serialization."""
        match = RuleMatch(
            rule_name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            match_type=RuleMatchType.ANY,
            matched_value="test",
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        result = match.to_dict()
        
        assert result["rule_name"] == "Test Rule"
        assert result["rule_type"] == "subject_contains"
        assert result["match_type"] == "any"
        assert result["matched_value"] == "test"


class TestActionExecutionResult:
    """Tests for ActionExecutionResult dataclass."""
    
    def test_action_execution_result_success(self):
        """Test successful action execution."""
        result = ActionExecutionResult(
            action_name="Move to Inbox",
            action_type=ActionType.MOVE,
            success=True,
            message="Successfully moved email",
            execution_time_ms=150.5
        )
        
        assert result.success is True
        assert result.message == "Successfully moved email"
        assert result.execution_time_ms == 150.5
        assert result.error is None
    
    def test_action_execution_result_failure(self):
        """Test failed action execution."""
        result = ActionExecutionResult(
            action_name="Forward Email",
            action_type=ActionType.FORWARD,
            success=False,
            message="Invalid recipient address",
            error="InvalidEmailAddressError",
            execution_time_ms=50.0
        )
        
        assert result.success is False
        assert result.message == "Invalid recipient address"
        assert result.error == "InvalidEmailAddressError"
        assert result.execution_time_ms == 50.0


class TestEmailProcessingResult:
    """Tests for EmailProcessingResult dataclass."""
    
    def test_email_processing_result_success(self):
        """Test successful email processing."""
        result = EmailProcessingResult(
            email_id="msg123",
            success=True,
            rules_matched=["Rule 1", "Rule 2"],
            actions_executed=["Move to Inbox", "Mark as Read"],
            processing_time_ms=250.0,
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        assert result.success is True
        assert result.email_id == "msg123"
        assert len(result.rules_matched) == 2
        assert len(result.actions_executed) == 2
        assert result.processing_time_ms == 250.0
    
    def test_email_processing_result_failure(self):
        """Test failed email processing."""
        result = EmailProcessingResult(
            email_id="msg456",
            success=False,
            error="File not found",
            processing_time_ms=10.0,
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        assert result.success is False
        assert result.email_id == "msg456"
        assert result.error == "File not found"
        assert len(result.rules_matched) == 0
        assert len(result.actions_executed) == 0


class TestCategory:
    """Tests for Category enum."""
    
    def test_category_values(self):
        """Test category enum values."""
        assert Category.INBOX.value == "inbox"
        assert Category.SPAM.value == "spam"
        assert Category.TRASH.value == "trash"
        assert Category.ARCHIVE.value == "archive"
        assert Category.SENT.value == "sent"
        assert Category.DRAFTS.value == "drafts"
        assert Category.UNREAD.value == "unread"
        assert Category.IMPORTANT.value == "important"
        assert Category.GENERAL.value == "general"
        assert Category.CUSTOM.value == "custom"


class TestRuleMatchType:
    """Tests for RuleMatchType enum."""
    
    def test_rule_match_type_values(self):
        """Test rule match type enum values."""
        assert RuleMatchType.ANY.value == "any"
        assert RuleMatchType.ALL.value == "all"
        assert RuleMatchType.EXACT.value == "exact"
        assert RuleMatchType.PATTERN.value == "pattern"


class TestRuleMatchStrategy:
    """Tests for RuleMatchStrategy enum."""
    
    def test_rule_match_strategy_values(self):
        """Test rule match strategy enum values."""
        assert RuleMatchStrategy.PRIORITY.value == "priority"
        assert RuleMatchStrategy.FIRST.value == "first"
        assert RuleMatchStrategy.LAST.value == "last"
        assert RuleMatchStrategy.ALL.value == "all"