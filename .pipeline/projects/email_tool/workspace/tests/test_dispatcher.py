"""Tests for the dispatcher module."""

import os
import pytest
from datetime import datetime
from email_tool.models import Email, Rule, RuleType, RuleMatch, ActionType
from email_tool.dispatcher import ActionDispatcher, ActionBuilder, ActionExecutor


class TestDispatcher:
    """Test cases for ActionDispatcher class."""
    
    @pytest.fixture
    def sample_email(self):
        """Create a sample email for testing."""
        return Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test Email",
            date=datetime(2024, 3, 15, 10, 30, 0),
            body_plain="This is a test email body.",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
    
    @pytest.fixture
    def sample_rule(self):
        """Create a sample rule for testing."""
        return Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="test",
            priority=50,
            category="general",
            labels=["important"]
        )
    
    @pytest.fixture
    def sample_rule_match(self, sample_rule):
        """Create a sample rule match."""
        return RuleMatch(
            rule=sample_rule,
            match_type=RuleType.SUBJECT_EXACT,
            matched_value="test",
            confidence=0.95
        )
    
    def test_handle_move_dry_run(self, sample_email, sample_rule_match):
        """Test MOVE action in dry run mode."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        result = dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.MOVE,
            action_params={"destination": "/tmp/archive"}
        )
        
        assert result["success"] is True
        assert result["action"] == "MOVE"
    
    def test_handle_file_dry_run(self, sample_email, sample_rule_match):
        """Test FILE action in dry run mode."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        result = dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.FILE,
            action_params={"format": "md"}
        )
        
        assert result["success"] is True
        assert result["action"] == "FILE"
        assert result["details"]["format"] == "md"
    
    def test_handle_label(self, sample_email, sample_rule_match):
        """Test LABEL action."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        result = dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.LABEL,
            action_params={"labels": ["work", "urgent"]}
        )
        
        assert result["success"] is True
        assert result["action"] == "LABEL"
        assert "work" in result["details"]["labels"]
        assert "urgent" in result["details"]["labels"]
    
    def test_handle_unknown_action(self, sample_email, sample_rule_match):
        """Test handling unknown action type."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        result = dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action="UNKNOWN",
            action_params={}
        )
        
        assert result["success"] is False
        assert "Unknown action type" in result["error"]
    
    def test_operations_log(self, sample_email, sample_rule_match):
        """Test that operations are logged."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.MOVE,
            action_params={}
        )
        
        log = dispatcher.get_operations_log()
        assert len(log) == 1
        assert log[0]["action"] == "MOVE"
    
    def test_clear_operations_log(self, sample_email, sample_rule_match):
        """Test clearing operations log."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.MOVE,
            action_params={}
        )
        
        dispatcher.clear_operations_log()
        assert len(dispatcher.get_operations_log()) == 0
    
    def test_get_summary(self, sample_email, sample_rule_match):
        """Test getting operation summary."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        # Add multiple operations
        dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.MOVE,
            action_params={}
        )
        dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.FILE,
            action_params={"format": "md"}
        )
        
        summary = dispatcher.get_summary()
        
        assert summary["total_operations"] == 2
        assert summary["successful_operations"] == 2
        assert summary["by_action"]["MOVE"] == 1
        assert summary["by_action"]["FILE"] == 1
    
    def test_handle_multiple_actions(self, sample_email, sample_rule_match):
        """Test handling multiple actions."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        actions = [
            (ActionType.MOVE, {"destination": "/tmp/archive"}),
            (ActionType.FILE, {"format": "md"}),
            (ActionType.LABEL, {"labels": ["test"]})
        ]
        
        results = dispatcher.handle_multiple_actions(
            email=sample_email,
            actions=actions
        )
        
        assert len(results) == 3
        assert results[0].action_type == ActionType.MOVE
        assert results[1].action_type == ActionType.FILE
        assert results[2].action_type == ActionType.LABEL


class TestActionBuilder:
    """Test cases for ActionBuilder class."""
    
    def test_build_move_action(self):
        """Test building MOVE action."""
        builder = ActionBuilder()
        builder.add_move(destination="/tmp/archive")
        
        actions = builder.build()
        
        assert len(actions) == 1
        assert actions[0][0].value == "move"
        assert actions[0][1]["destination"] == "/tmp/archive"
    
    def test_build_file_action(self):
        """Test building FILE action."""
        builder = ActionBuilder()
        builder.add_file(format="pdf")
        
        actions = builder.build()
        
        assert len(actions) == 1
        assert actions[0][0].value == "file"
        assert actions[0][1]["format"] == "pdf"
    
    def test_build_label_action(self):
        """Test building LABEL action."""
        builder = ActionBuilder()
        builder.add_label(labels=["work", "urgent"])
        
        actions = builder.build()
        
        assert len(actions) == 1
        assert actions[0][0].value == "label"
        assert actions[0][1]["labels"] == ["work", "urgent"]
    
    def test_build_multiple_actions(self):
        """Test building multiple actions."""
        builder = ActionBuilder()
        builder.add_move(destination="/tmp/archive", priority=1)
        builder.add_file(format="md", priority=2)
        builder.add_label(labels=["test"], priority=3)
        
        actions = builder.build()
        
        assert len(actions) == 3
        # Should be sorted by priority (higher first)
        assert actions[0][0].value == "label"
        assert actions[1][0].value == "file"
        assert actions[2][0].value == "move"
    
    def test_build_empty(self):
        """Test building empty action list."""
        builder = ActionBuilder()
        actions = builder.build()
        
        assert len(actions) == 0


class TestActionExecutor:
    """Test cases for ActionExecutor class."""
    
    @pytest.fixture
    def mock_dispatcher(self):
        """Create a mock dispatcher."""
        return ActionDispatcher(dry_run=True)
    
    def test_execute_success(self, mock_dispatcher):
        """Test successful execution."""
        executor = ActionExecutor(mock_dispatcher)
        
        # Create mock objects
        from email_tool.models import Rule, RuleType, RuleMatch
        
        email = Email(
            from_addr="sender@example.com",
            to_addrs=["recipient@test.com"],
            subject="Test",
            date=datetime(2024, 3, 15),
            body_plain="Body",
            attachments=[],
            raw_headers={},
            labels=[],
            source_path="/tmp/test.eml"
        )
        
        rule = Rule(
            id="test_rule_001",
            name="test_rule",
            rule_type=RuleType.SUBJECT_EXACT,
            pattern="test",
            priority=50,
            category="general",
            labels=[]
        )
        
        rule_match = RuleMatch(
            rule=rule,
            match_type=RuleType.SUBJECT_EXACT,
            matched_value="test",
            confidence=0.95
        )
        
        actions = [
            (ActionType.MOVE, {"destination": "/tmp/archive"}),
            (ActionType.FILE, {"format": "md"})
        ]
        
        results = executor.execute(email, rule_match, actions)
        
        assert len(results) == 2
        assert all(r["success"] for r in results)
    
    def test_execute_with_retry(self, mock_dispatcher):
        """Test execution with retry logic."""
        # Make first attempt fail, second succeed
        call_count = [0]
        
        def mock_handle_action(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"success": False, "error": "Temporary error"}
            return {"success": True, "action": "MOVE"}
        
        original_handle_action = mock_dispatcher.handle_action
        mock_dispatcher.handle_action = mock_handle_action
        
        try:
            executor = ActionExecutor(mock_dispatcher, max_retries=3, retry_delay=0.01)
            
            # Create mock objects
            from email_tool.models import Rule, RuleType, RuleMatch
            
            email = Email(
                from_addr="sender@example.com",
                to_addrs=["recipient@test.com"],
                subject="Test",
                date=datetime(2024, 3, 15),
                body_plain="Body",
                attachments=[],
                raw_headers={},
                labels=[],
                source_path="/tmp/test.eml"
            )
            
            rule = Rule(
                id="test_rule",
                name="test_rule",
                rule_type=RuleType.SUBJECT_EXACT,
                pattern="test",
                priority=50,
                category="general",
                labels=[]
            )
            
            rule_match = RuleMatch(
                rule=rule,
                match_type=RuleType.SUBJECT_EXACT,
                matched_value="test",
                confidence=0.95
            )
            
            actions = [(ActionType.MOVE, {"destination": "/tmp/archive"})]
            
            results = executor.execute(email, rule_match, actions)
            
            assert len(results) == 1
            assert results[0]["success"] is True
            assert call_count[0] == 2  # Should have retried once
        finally:
            mock_dispatcher.handle_action = original_handle_action


class TestDispatcherCollision:
    """Test collision handling in dispatcher."""
    
    def test_collision_rename_strategy(self, tmp_path):
        """Test rename collision strategy."""
        dispatcher = ActionDispatcher(
            base_path=str(tmp_path),
            collision_strategy="rename"
        )
        
        # Create existing file
        existing_file = tmp_path / "test.eml"
        existing_file.write_text("existing content")
        
        # Resolve collision
        new_path = dispatcher._resolve_collision(str(existing_file))
        
        assert new_path != str(existing_file)
        assert "test.eml" in new_path
        assert "_20" in new_path  # timestamp
    
    def test_collision_number_strategy(self, tmp_path):
        """Test number collision strategy."""
        dispatcher = ActionDispatcher(
            base_path=str(tmp_path),
            collision_strategy="number"
        )
        
        # Create existing files
        (tmp_path / "test.eml").write_text("existing 1")
        (tmp_path / "test_1.eml").write_text("existing 2")
        
        # Resolve collision
        new_path = dispatcher._resolve_collision(str(tmp_path / "test.eml"))
        
        assert new_path == str(tmp_path / "test_2.eml")
    
    def test_collision_overwrite_strategy(self, tmp_path):
        """Test overwrite collision strategy."""
        dispatcher = ActionDispatcher(
            base_path=str(tmp_path),
            collision_strategy="overwrite"
        )
        
        # Create existing file
        existing_file = tmp_path / "test.eml"
        existing_file.write_text("existing content")
        
        # Resolve collision
        new_path = dispatcher._resolve_collision(str(existing_file))
        
        assert new_path == str(existing_file)


class TestDispatcherEdgeCases:
    """Edge case tests for dispatcher."""
    
    def test_empty_labels(self, sample_email, sample_rule_match):
        """Test LABEL action with empty labels."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        result = dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.LABEL,
            action_params={"labels": []}
        )
        
        assert result["success"] is True
        # Should still succeed even with empty labels
        assert result["action"] == "LABEL"
    
    def test_no_destination_for_move(self, sample_email, sample_rule_match):
        """Test MOVE action without destination."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        result = dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.MOVE,
            action_params={}
        )
        
        assert result["success"] is True
        # Should use base_path as default
    
    def test_invalid_format_for_file(self, sample_email, sample_rule_match):
        """Test FILE action with invalid format."""
        dispatcher = ActionDispatcher(dry_run=True)
        
        result = dispatcher.handle_action(
            email=sample_email,
            rule_match=sample_rule_match,
            action=ActionType.FILE,
            action_params={"format": "invalid"}
        )
        
        # Should still succeed in dry run
        assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
