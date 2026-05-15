"""
Tests for Phase 6 Email Processing Models

Comprehensive test suite for the Phase 6 models including Email, Rule, RuleMatch,
RuleMatchType, Category, and ActionExecutionResult.
"""

import pytest
import json
from datetime import datetime
from email_tool.models import (
    Email,
    Rule,
    RuleMatch,
    RuleType,
    RuleMatchType,
    Category,
    ActionType,
    ActionExecutionResult,
    EmailMetadata,
    ProcessingStats,
    RuleSet,
    ActionSet,
    ProcessingConfig,
    EmailMatch,
    EmailProcessingResult,
    Phase6ProcessingConfig
)


class TestRuleMatchType:
    """Tests for RuleMatchType enum."""
    
    def test_rule_match_type_values(self):
        """Test that RuleMatchType has correct values."""
        assert RuleMatchType.EXACT.value == "exact"
        assert RuleMatchType.CONTAINS.value == "contains"
        assert RuleMatchType.REGEX.value == "regex"
        assert RuleMatchType.STARTS_WITH.value == "starts_with"
        assert RuleMatchType.ENDS_WITH.value == "ends_with"
    
    def test_rule_match_type_iteration(self):
        """Test that RuleMatchType can be iterated."""
        types = list(RuleMatchType)
        assert len(types) == 5
        assert RuleMatchType.EXACT in types
        assert RuleMatchType.CONTAINS in types


class TestCategory:
    """Tests for Category enum."""
    
    def test_category_values(self):
        """Test that Category has correct values."""
        assert Category.INBOX.value == "inbox"
        assert Category.SENT.value == "sent"
        assert Category.DRAFTS.value == "drafts"
        assert Category.ARCHIVE.value == "archive"
        assert Category.SPAM.value == "spam"
        assert Category.TRASH.value == "trash"
        assert Category.CUSTOM.value == "custom"
    
    def test_category_iteration(self):
        """Test that Category can be iterated."""
        categories = list(Category)
        assert len(categories) == 7
        assert Category.INBOX in categories
        assert Category.CUSTOM in categories


class TestEmail:
    """Tests for Email dataclass."""
    
    def test_email_creation(self):
        """Test basic email creation."""
        email = Email(
            id="test-001",
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject"
        )
        assert email.id == "test-001"
        assert email.from_addr == "sender@example.com"
        assert email.to_addrs == ["recipient@example.com"]
        assert email.subject == "Test Subject"
    
    def test_email_auto_id(self):
        """Test that email gets auto-generated ID if not provided."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject"
        )
        assert email.id is not None
        assert len(email.id) > 0
    
    def test_email_default_values(self):
        """Test that email has correct default values."""
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject"
        )
        assert email.date is None
        assert email.body_plain is None
        assert email.body_html is None
        assert email.attachments == []
        assert email.raw_headers == {}
        assert email.labels == []
        assert email.source_path is None
        assert email.created_at is not None
    
    def test_email_to_eml(self):
        """Test email to EML conversion."""
        email = Email(
            id="test-001",
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            date=datetime(2024, 1, 1, 12, 0, 0),
            body_plain="Test body"
        )
        eml = email.to_eml()
        assert "From: sender@example.com" in eml
        assert "To: recipient@example.com" in eml
        assert "Subject: Test Subject" in eml
        assert "Test body" in eml
    
    def test_email_repr(self):
        """Test email string representation."""
        email = Email(
            id="test-001",
            from_addr="sender@example.com",
            subject="Test Subject"
        )
        repr_str = repr(email)
        assert "Email" in repr_str
        assert "test-001" in repr_str
        assert "sender@example.com" in repr_str
        assert "Test Subject" in repr_str


class TestRule:
    """Tests for Rule dataclass."""
    
    def test_rule_creation(self):
        """Test basic rule creation."""
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.SUBJECT_CONTAINS
        assert rule.pattern == "test"
        assert rule.priority == 50
        assert rule.category == "general"
        assert rule.labels == []
        assert rule.description == ""
        assert rule.enabled is True
    
    def test_rule_priority_validation(self):
        """Test that rule validates priority range."""
        with pytest.raises(ValueError):
            Rule(
                name="Test Rule",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="test",
                priority=-1
            )
        
        with pytest.raises(ValueError):
            Rule(
                name="Test Rule",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="test",
                priority=101
            )
    
    def test_rule_to_dict(self):
        """Test rule serialization."""
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            priority=80,
            category="work",
            labels=["important"],
            description="A test rule"
        )
        rule_dict = rule.to_dict()
        assert rule_dict["name"] == "Test Rule"
        assert rule_dict["rule_type"] == "subject_contains"
        assert rule_dict["pattern"] == "test"
        assert rule_dict["priority"] == 80
        assert rule_dict["category"] == "work"
        assert rule_dict["labels"] == ["important"]
        assert rule_dict["description"] == "A test rule"
        assert rule_dict["enabled"] is True
    
    def test_rule_from_dict(self):
        """Test rule deserialization."""
        rule_dict = {
            "name": "Test Rule",
            "rule_type": "subject_contains",
            "pattern": "test",
            "priority": 80,
            "category": "work",
            "labels": ["important"],
            "description": "A test rule",
            "enabled": True
        }
        rule = Rule.from_dict(rule_dict)
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.SUBJECT_CONTAINS
        assert rule.pattern == "test"
        assert rule.priority == 80
        assert rule.category == "work"
        assert rule.labels == ["important"]
        assert rule.description == "A test rule"
        assert rule.enabled is True
    
    def test_rule_from_dict_defaults(self):
        """Test rule deserialization with defaults."""
        rule_dict = {
            "name": "Test Rule",
            "rule_type": "subject_contains",
            "pattern": "test"
        }
        rule = Rule.from_dict(rule_dict)
        assert rule.priority == 50
        assert rule.category == "general"
        assert rule.labels == []
        assert rule.description == ""
        assert rule.enabled is True


class TestRuleMatch:
    """Tests for RuleMatch dataclass."""
    
    def test_rule_match_creation(self):
        """Test basic rule match creation."""
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        match = RuleMatch(
            rule=rule,
            match_type=RuleMatchType.CONTAINS,
            matched_value="test",
            confidence=0.95
        )
        assert match.rule == rule
        assert match.match_type == RuleMatchType.CONTAINS
        assert match.matched_value == "test"
        assert match.confidence == 0.95
        assert match.rule_name == "Test Rule"
    
    def test_rule_match_auto_rule_name(self):
        """Test that rule_name is auto-populated from rule."""
        rule = Rule(
            name="Custom Rule Name",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        match = RuleMatch(
            rule=rule,
            match_type=RuleMatchType.CONTAINS,
            matched_value="test"
        )
        assert match.rule_name == "Custom Rule Name"
    
    def test_rule_match_repr(self):
        """Test rule match string representation."""
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        match = RuleMatch(
            rule=rule,
            match_type=RuleMatchType.CONTAINS,
            matched_value="test"
        )
        repr_str = repr(match)
        assert "RuleMatch" in repr_str
        assert "Test Rule" in repr_str
        assert "contains" in repr_str
        assert "test" in repr_str


class TestActionExecutionResult:
    """Tests for ActionExecutionResult dataclass."""
    
    def test_action_execution_result_creation(self):
        """Test basic action execution result creation."""
        result = ActionExecutionResult(
            action_type=ActionType.ADD_LABEL,
            success=True,
            message="Label added successfully"
        )
        assert result.action_type == ActionType.ADD_LABEL
        assert result.success is True
        assert result.message == "Label added successfully"
        assert result.details == {}
    
    def test_action_execution_result_with_details(self):
        """Test action execution result with details."""
        result = ActionExecutionResult(
            action_type=ActionType.ADD_LABEL,
            success=True,
            message="Label added successfully",
            details={"label": "work", "email_id": "email-001"}
        )
        assert result.details["label"] == "work"
        assert result.details["email_id"] == "email-001"
    
    def test_action_execution_result_repr(self):
        """Test action execution result string representation."""
        result = ActionExecutionResult(
            action_type=ActionType.ADD_LABEL,
            success=True,
            message="Label added successfully"
        )
        repr_str = repr(result)
        assert "ActionExecutionResult" in repr_str
        assert "ADD_LABEL" in repr_str
        assert "True" in repr_str
        assert "Label added successfully" in repr_str


class TestEmailMetadata:
    """Tests for EmailMetadata dataclass."""
    
    def test_email_metadata_creation(self):
        """Test basic email metadata creation."""
        metadata = EmailMetadata(
            subject="Test Subject",
            from_email="sender@example.com",
            from_name="Sender Name",
            to_emails=["recipient@example.com"],
            cc_emails=[],
            bcc_emails=[],
            date=datetime(2024, 1, 1, 12, 0, 0),
            message_id="<001@example.com>",
            size_bytes=1024,
            has_attachments=False,
            attachment_names=[],
            labels=["work"]
        )
        assert metadata.subject == "Test Subject"
        assert metadata.from_email == "sender@example.com"
        assert metadata.from_name == "Sender Name"
        assert metadata.to_emails == ["recipient@example.com"]
        assert metadata.labels == ["work"]
    
    def test_email_metadata_to_dict(self):
        """Test email metadata serialization."""
        metadata = EmailMetadata(
            subject="Test Subject",
            from_email="sender@example.com",
            from_name="Sender Name",
            to_emails=["recipient@example.com"],
            cc_emails=["cc@example.com"],
            bcc_emails=[],
            date=datetime(2024, 1, 1, 12, 0, 0),
            message_id="<001@example.com>",
            size_bytes=1024,
            has_attachments=True,
            attachment_names=["attachment.pdf"],
            labels=["work"],
            body_text="Test body",
            body_html="<p>Test body</p>",
            headers={"X-Priority": "1"}
        )
        metadata_dict = metadata.to_dict()
        assert metadata_dict["subject"] == "Test Subject"
        assert metadata_dict["from_email"] == "sender@example.com"
        assert metadata_dict["has_attachments"] is True
        assert metadata_dict["attachment_names"] == ["attachment.pdf"]
        assert metadata_dict["headers"] == {"X-Priority": "1"}


class TestProcessingStats:
    """Tests for ProcessingStats dataclass."""
    
    def test_processing_stats_creation(self):
        """Test basic processing stats creation."""
        stats = ProcessingStats()
        assert stats.total_emails == 0
        assert stats.processed_emails == 0
        assert stats.successful_emails == 0
        assert stats.failed_emails == 0
        assert stats.matched_emails == 0
        assert stats.total_rules == 0
        assert stats.total_actions == 0
        assert stats.total_processing_time_ms == 0.0
        assert stats.start_time is None
        assert stats.end_time is None
        assert stats.errors_by_type == {}
    
    def test_processing_stats_add_error(self):
        """Test error tracking in processing stats."""
        stats = ProcessingStats()
        stats.add_error("parse_error")
        stats.add_error("parse_error")
        stats.add_error("validation_error")
        
        assert stats.errors_by_type["parse_error"] == 2
        assert stats.errors_by_type["validation_error"] == 1
    
    def test_processing_stats_to_dict(self):
        """Test processing stats serialization."""
        stats = ProcessingStats(
            total_emails=100,
            processed_emails=95,
            successful_emails=90,
            failed_emails=5,
            matched_emails=50,
            total_rules=10,
            total_actions=20,
            total_processing_time_ms=1500.5,
            start_time=datetime(2024, 1, 1, 12, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 5, 0),
            errors_by_type={"parse_error": 2, "validation_error": 1}
        )
        stats_dict = stats.to_dict()
        assert stats_dict["total_emails"] == 100
        assert stats_dict["processed_emails"] == 95
        assert abs(stats_dict["success_rate"] - (90 / 95)) < 0.001
        assert stats_dict["total_processing_time_ms"] == 1500.5


class TestRuleSet:
    """Tests for RuleSet dataclass."""
    
    def test_rule_set_creation(self):
        """Test basic rule set creation."""
        rule_set = RuleSet(
            name="Work Rules",
            rules=[],
            description="Rules for work emails"
        )
        assert rule_set.name == "Work Rules"
        assert rule_set.rules == []
        assert rule_set.description == "Rules for work emails"
    
    def test_rule_set_add_rule(self):
        """Test adding rules to rule set."""
        rule_set = RuleSet(name="Work Rules", rules=[])
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        rule_set.add_rule(rule)
        assert len(rule_set.rules) == 1
        assert rule_set.rules[0] == rule
    
    def test_rule_set_remove_rule(self):
        """Test removing rules from rule set."""
        rule_set = RuleSet(name="Work Rules", rules=[])
        rule1 = Rule(
            name="Rule 1",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test1"
        )
        rule2 = Rule(
            name="Rule 2",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test2"
        )
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        assert len(rule_set.rules) == 2
        
        rule_set.remove_rule(rule1)
        assert len(rule_set.rules) == 1
        assert rule_set.rules[0] == rule2
    
    def test_rule_set_to_dict(self):
        """Test rule set serialization."""
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test"
        )
        rule_set = RuleSet(
            name="Work Rules",
            rules=[rule],
            description="Rules for work emails"
        )
        rule_set_dict = rule_set.to_dict()
        assert rule_set_dict["name"] == "Work Rules"
        assert len(rule_set_dict["rules"]) == 1
        assert rule_set_dict["rules"][0]["name"] == "Test Rule"
        assert rule_set_dict["description"] == "Rules for work emails"


class TestActionSet:
    """Tests for ActionSet dataclass."""
    
    def test_action_set_creation(self):
        """Test basic action set creation."""
        action_set = ActionSet(
            name="Work Actions",
            actions=[],
            description="Actions for work emails"
        )
        assert action_set.name == "Work Actions"
        assert action_set.actions == []
        assert action_set.description == "Actions for work emails"
    
    def test_action_set_add_action(self):
        """Test adding actions to action set."""
        action_set = ActionSet(name="Work Actions", actions=[])
        action = ActionType.ADD_LABEL
        action_set.add_action(action)
        assert len(action_set.actions) == 1
        assert action_set.actions[0] == action
    
    def test_action_set_remove_action(self):
        """Test removing actions from action set."""
        action_set = ActionSet(name="Work Actions", actions=[])
        action_set.add_action(ActionType.ADD_LABEL)
        action_set.add_action(ActionType.MOVE_TO_CATEGORY)
        assert len(action_set.actions) == 2
        
        action_set.remove_action(ActionType.ADD_LABEL)
        assert len(action_set.actions) == 1
        assert action_set.actions[0] == ActionType.MOVE_TO_CATEGORY
    
    def test_action_set_to_dict(self):
        """Test action set serialization."""
        action_set = ActionSet(
            name="Work Actions",
            actions=[ActionType.ADD_LABEL, ActionType.MOVE_TO_CATEGORY],
            description="Actions for work emails"
        )
        action_set_dict = action_set.to_dict()
        assert action_set_dict["name"] == "Work Actions"
        assert len(action_set_dict["actions"]) == 2
        assert action_set_dict["actions"] == ["add_label", "move_to_category"]
        assert action_set_dict["description"] == "Actions for work emails"


class TestProcessingConfig:
    """Tests for ProcessingConfig dataclass."""
    
    def test_processing_config_creation(self):
        """Test basic processing config creation."""
        config = Phase6ProcessingConfig()
        assert config.max_processing_time_ms == 30000
        assert config.max_actions_per_email == 10
        assert config.enable_attachments is True
        assert config.enable_llm is False
        assert config.enable_monitoring is True
        assert config.rule_sets == []
        assert config.action_sets == []
    
    def test_processing_config_to_dict(self):
        """Test processing config serialization."""
        config = Phase6ProcessingConfig(
            max_processing_time_ms=60000,
            max_actions_per_email=20,
            enable_attachments=False,
            enable_llm=True,
            enable_monitoring=False,
            rule_sets=[],
            action_sets=[]
        )
        config_dict = config.to_dict()
        assert config_dict["max_processing_time_ms"] == 60000
        assert config_dict["max_actions_per_email"] == 20
        assert config_dict["enable_attachments"] is False
        assert config_dict["enable_llm"] is True
        assert config_dict["enable_monitoring"] is False


class TestEmailMatch:
    """Tests for EmailMatch dataclass."""
    
    def test_email_match_creation(self):
        """Test basic email match creation."""
        match = EmailMatch(
            email_id="email-001",
            rule_name="Test Rule",
            match_type=RuleMatchType.CONTAINS,
            matched_value="test",
            confidence=0.95
        )
        assert match.email_id == "email-001"
        assert match.rule_name == "Test Rule"
        assert match.match_type == RuleMatchType.CONTAINS
        assert match.matched_value == "test"
        assert match.confidence == 0.95
    
    def test_email_match_to_dict(self):
        """Test email match serialization."""
        match = EmailMatch(
            email_id="email-001",
            rule_name="Test Rule",
            match_type=RuleMatchType.CONTAINS,
            matched_value="test",
            confidence=0.95
        )
        match_dict = match.to_dict()
        assert match_dict["email_id"] == "email-001"
        assert match_dict["rule_name"] == "Test Rule"
        assert match_dict["match_type"] == "contains"
        assert match_dict["matched_value"] == "test"
        assert match_dict["confidence"] == 0.95


class TestEmailProcessingResult:
    """Tests for EmailProcessingResult dataclass."""
    
    def test_email_processing_result_creation(self):
        """Test basic email processing result creation."""
        result = EmailProcessingResult(
            email_id="email-001",
            status="success",
            processing_time_ms=150.5,
            rules_matched=2,
            actions_executed=3,
            errors=[]
        )
        assert result.email_id == "email-001"
        assert result.status == "success"
        assert result.processing_time_ms == 150.5
        assert result.rules_matched == 2
        assert result.actions_executed == 3
        assert result.errors == []
    
    def test_email_processing_result_to_dict(self):
        """Test email processing result serialization."""
        result = EmailProcessingResult(
            email_id="email-001",
            status="success",
            processing_time_ms=150.5,
            rules_matched=2,
            actions_executed=3,
            errors=[],
            matched_rules=["rule-001", "rule-002"],
            executed_actions=["action-001", "action-002", "action-003"]
        )
        result_dict = result.to_dict()
        assert result_dict["email_id"] == "email-001"
        assert result_dict["status"] == "success"
        assert result_dict["processing_time_ms"] == 150.5
        assert result_dict["rules_matched"] == 2
        assert result_dict["actions_executed"] == 3
        assert result_dict["matched_rules"] == ["rule-001", "rule-002"]
        assert result_dict["executed_actions"] == ["action-001", "action-002", "action-003"]


class TestModelSerialization:
    """Tests for model serialization and deserialization."""
    
    def test_email_roundtrip(self):
        """Test email serialization and deserialization."""
        email = Email(
            id="test-001",
            from_addr="sender@example.com",
            to_addrs=["recipient@example.com"],
            subject="Test Subject",
            date=datetime(2024, 1, 1, 12, 0, 0),
            body_plain="Test body",
            labels=["work"]
        )
        email_dict = email.to_dict()
        email_restored = Email.from_dict(email_dict)
        assert email_restored.id == email.id
        assert email_restored.from_addr == email.from_addr
        assert email_restored.subject == email.subject
        assert email_restored.labels == email.labels
    
    def test_rule_roundtrip(self):
        """Test rule serialization and deserialization."""
        rule = Rule(
            name="Test Rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            priority=80,
            category="work",
            labels=["important"]
        )
        rule_dict = rule.to_dict()
        rule_restored = Rule.from_dict(rule_dict)
        assert rule_restored.name == rule.name
        assert rule_restored.rule_type == rule.rule_type
        assert rule_restored.pattern == rule.pattern
        assert rule_restored.priority == rule.priority
    
    def test_action_result_roundtrip(self):
        """Test action execution result serialization and deserialization."""
        result = ActionExecutionResult(
            action_type=ActionType.ADD_LABEL,
            success=True,
            message="Label added successfully",
            details={"label": "work"}
        )
        result_dict = result.to_dict()
        result_restored = ActionExecutionResult.from_dict(result_dict)
        assert result_restored.action_type == result.action_type
        assert result_restored.success == result.success
        assert result_restored.message == result.message
        assert result_restored.details == result.details


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
