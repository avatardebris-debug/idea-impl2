"""Unit tests for the email processor module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from email_tool.processor import (
    EmailProcessor,
    PipelineBuilder,
    PipelineExecutor,
    PipelineMonitor,
    PipelineConfig
)
from email_tool.models import Rule, RuleMatch, ActionType


class TestEmailProcessorInitialization:
    """Tests for EmailProcessor initialization."""

    def test_processor_initialization_defaults(self):
        """Test EmailProcessor with default parameters."""
        processor = EmailProcessor()
        assert processor.base_path == "./archive"
        assert processor.dry_run is False
        assert processor.collision_strategy == "rename"
        assert processor.max_retries == 3
        assert processor.retry_delay == 1.0
        assert processor.stats["total_processed"] == 0
        assert processor.stats["total_matched"] == 0
        assert processor.stats["total_failed"] == 0

    def test_processor_initialization_custom(self):
        """Test EmailProcessor with custom parameters."""
        processor = EmailProcessor(
            base_path="/tmp/test",
            dry_run=True,
            collision_strategy="skip",
            max_retries=5,
            retry_delay=2.0
        )
        assert processor.base_path == "/tmp/test"
        assert processor.dry_run is True
        assert processor.collision_strategy == "skip"
        assert processor.max_retries == 5
        assert processor.retry_delay == 2.0

    def test_processor_components_initialized(self):
        """Test that processor components are initialized."""
        processor = EmailProcessor()
        assert processor.parser is not None
        assert processor.matcher is not None
        assert processor.dispatcher is not None
        assert processor.executor is not None


class TestEmailProcessorProcessing:
    """Tests for email processing."""

    def test_process_email_success(self):
        """Test successful email processing."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[]):
                result = processor.process_email(
                    email_source="test.eml",
                    rules=[],
                    actions=[]
                )
                
                assert result["success"] is True
                assert result["email_id"] == "test_email_123"
                assert processor.stats["total_processed"] == 1

    def test_process_email_with_matches(self):
        """Test processing email with rule matches."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    result = processor.process_email(
                        email_source="test.eml",
                        rules=[mock_rule],
                        actions=[]
                    )
                    
                    assert result["success"] is True
                    assert len(result["matches"]) == 1
                    assert processor.stats["total_matched"] == 1
                    assert processor.stats["by_rule"]["test_rule"] == 1

    def test_process_email_with_error(self):
        """Test processing email with error."""
        processor = EmailProcessor()
        
        with patch.object(processor.parser, 'parse', side_effect=Exception("Parse error")):
            result = processor.process_email(
                email_source="test.eml",
                rules=[],
                actions=[]
            )
            
            assert result["success"] is False
            assert len(result["errors"]) == 1
            assert "Parse error" in result["errors"][0]
            assert processor.stats["total_failed"] == 1

    def test_process_email_with_actions(self):
        """Test processing email with actions."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        mock_action_result = {
            "action": "move",
            "success": True,
            "details": "Moved to folder"
        }
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[mock_action_result]):
                    result = processor.process_email(
                        email_source="test.eml",
                        rules=[mock_rule],
                        actions=[(ActionType.MOVE, {"destination": "inbox"})]
                    )
                    
                    assert result["success"] is True
                    assert len(result["actions_performed"]) == 1
                    assert processor.stats["by_action"]["move"] == 1


class TestEmailProcessorBatchProcessing:
    """Tests for batch email processing."""

    def test_process_batch(self):
        """Test processing multiple emails."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    results = processor.process_batch(
                        email_sources=["test1.eml", "test2.eml", "test3.eml"],
                        rules=[],
                        actions=[]
                    )
                    
                    assert len(results) == 3
                    assert all(r["success"] is True for r in results)
                    assert processor.stats["total_processed"] == 3

    def test_process_batch_with_failures(self):
        """Test batch processing with some failures."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        call_count = [0]
        
        def parse_side_effect(source):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Parse error")
            return mock_email
        
        with patch.object(processor.parser, 'parse', side_effect=parse_side_effect):
            with patch.object(processor.matcher, 'match', return_value=[]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    results = processor.process_batch(
                        email_sources=["test1.eml", "test2.eml", "test3.eml"],
                        rules=[],
                        actions=[]
                    )
                    
                    assert len(results) == 3
                    assert results[0]["success"] is True
                    assert results[1]["success"] is False
                    assert results[2]["success"] is True
                    assert processor.stats["total_processed"] == 3
                    assert processor.stats["total_failed"] == 1


class TestEmailProcessorDirectoryProcessing:
    """Tests for directory-based email processing."""

    def test_process_directory(self, tmp_path):
        """Test processing all emails in a directory."""
        processor = EmailProcessor()
        
        # Create test email files
        for i in range(3):
            (tmp_path / f"test{i}.eml").write_text(f"Email {i}")
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    results = processor.process_directory(
                        source_dir=str(tmp_path),
                        rules=[],
                        actions=[],
                        file_pattern="*.eml"
                    )
                    
                    assert len(results) == 3
                    assert all(r["success"] is True for r in results)


class TestEmailProcessorStats:
    """Tests for processor statistics."""

    def test_get_stats(self):
        """Test getting processor statistics."""
        processor = EmailProcessor()
        
        stats = processor.get_stats()
        assert stats["total_processed"] == 0
        assert stats["total_matched"] == 0
        assert stats["total_failed"] == 0
        assert stats["by_rule"] == {}
        assert stats["by_action"] == {}

    def test_reset_stats(self):
        """Test resetting processor statistics."""
        processor = EmailProcessor()
        
        # Simulate some processing
        processor.stats["total_processed"] = 10
        processor.stats["total_matched"] = 5
        processor.stats["total_failed"] = 2
        processor.stats["by_rule"] = {"rule1": 3, "rule2": 2}
        processor.stats["by_action"] = {"move": 4, "archive": 1}
        
        processor.reset_stats()
        
        assert processor.stats["total_processed"] == 0
        assert processor.stats["total_matched"] == 0
        assert processor.stats["total_failed"] == 0
        assert processor.stats["by_rule"] == {}
        assert processor.stats["by_action"] == {}

    def test_stats_incremented_on_processing(self):
        """Test that stats are incremented during processing."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    processor.process_email(
                        email_source="test.eml",
                        rules=[mock_rule],
                        actions=[]
                    )
                    
                    stats = processor.get_stats()
                    assert stats["total_processed"] == 1
                    assert stats["total_matched"] == 1
                    assert stats["by_rule"]["test_rule"] == 1


class TestEmailProcessorDispatcherLog:
    """Tests for dispatcher log operations."""

    def test_get_dispatcher_log(self):
        """Test getting dispatcher log."""
        processor = EmailProcessor()
        
        log = processor.get_dispatcher_log()
        assert isinstance(log, list)

    def test_clear_dispatcher_log(self):
        """Test clearing dispatcher log."""
        processor = EmailProcessor()
        
        processor.clear_dispatcher_log()
        log = processor.get_dispatcher_log()
        assert isinstance(log, list)


class TestPipelineBuilder:
    """Tests for PipelineBuilder class."""

    def test_builder_default_values(self):
        """Test builder with default values."""
        builder = PipelineBuilder()
        processor = builder.build()
        
        assert processor.base_path == "./archive"
        assert processor.dry_run is False
        assert processor.collision_strategy == "rename"

    def test_builder_chaining(self):
        """Test builder method chaining."""
        builder = PipelineBuilder()
        
        processor = (builder
            .set_base_path("/tmp/test")
            .set_dry_run(True)
            .set_collision_strategy("skip")
            .set_retry_config(max_retries=5, retry_delay=2.0)
            .build())
        
        assert processor.base_path == "/tmp/test"
        assert processor.dry_run is True
        assert processor.collision_strategy == "skip"
        assert processor.max_retries == 5
        assert processor.retry_delay == 2.0

    def test_builder_add_rule(self):
        """Test adding rules via builder."""
        builder = PipelineBuilder()
        
        mock_rule = MagicMock()
        builder.add_rule(mock_rule)
        
        processor = builder.build()
        assert len(processor.rules) == 1
        assert processor.rules[0] == mock_rule

    def test_builder_add_rules(self):
        """Test adding multiple rules via builder."""
        builder = PipelineBuilder()
        
        mock_rule1 = MagicMock()
        mock_rule2 = MagicMock()
        builder.add_rules([mock_rule1, mock_rule2])
        
        processor = builder.build()
        assert len(processor.rules) == 2

    def test_builder_add_action(self):
        """Test adding actions via builder."""
        builder = PipelineBuilder()
        
        builder.add_action(ActionType.MOVE, {"destination": "inbox"})
        
        processor = builder.build()
        assert len(processor.actions) == 1
        assert processor.actions[0] == (ActionType.MOVE, {"destination": "inbox"})

    def test_builder_add_actions(self):
        """Test adding multiple actions via builder."""
        builder = PipelineBuilder()
        
        actions = [
            (ActionType.MOVE, {"destination": "inbox"}),
            (ActionType.ARCHIVE, {"folder": "archive"})
        ]
        builder.add_actions(actions)
        
        processor = builder.build()
        assert len(processor.actions) == 2


class TestPipelineExecutor:
    """Tests for PipelineExecutor class."""

    def test_execute_with_callback(self):
        """Test execution with progress callback."""
        processor = EmailProcessor()
        
        progress_updates = []
        
        def progress_callback(current, total, result):
            progress_updates.append((current, total, result))
        
        executor = PipelineExecutor(processor, progress_callback=progress_callback)
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    results = executor.execute(
                        email_sources=["test1.eml", "test2.eml"],
                        rules=[],
                        actions=[]
                    )
                    
                    assert len(results) == 2
                    assert len(progress_updates) == 2
                    assert progress_updates[0][0] == 1
                    assert progress_updates[1][0] == 2

    def test_execute_directory(self, tmp_path):
        """Test executing on directory."""
        processor = EmailProcessor()
        
        # Create test email files
        for i in range(2):
            (tmp_path / f"test{i}.eml").write_text(f"Email {i}")
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    executor = PipelineExecutor(processor)
                    results = executor.execute_directory(
                        source_dir=str(tmp_path),
                        rules=[],
                        actions=[],
                        file_pattern="*.eml"
                    )
                    
                    assert len(results) == 2


class TestPipelineMonitor:
    """Tests for PipelineMonitor class."""

    def test_get_status(self):
        """Test getting pipeline status."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    processor.process_email(
                        email_source="test.eml",
                        rules=[mock_rule],
                        actions=[]
                    )
        
        monitor = PipelineMonitor(processor)
        status = monitor.get_status()
        
        assert status["total_processed"] == 1
        assert status["total_matched"] == 1
        assert status["total_failed"] == 0
        assert "success_rate" in status
        assert "last_updated" in status

    def test_calculate_success_rate(self):
        """Test success rate calculation."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    processor.process_email(
                        email_source="test.eml",
                        rules=[mock_rule],
                        actions=[]
                    )
        
        monitor = PipelineMonitor(processor)
        status = monitor.get_status()
        
        assert status["success_rate"] == 100.0

    def test_get_rule_performance(self):
        """Test getting rule performance metrics."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule1 = MagicMock()
        mock_rule1.name = "rule1"
        
        mock_rule2 = MagicMock()
        mock_rule2.name = "rule2"
        
        mock_match1 = RuleMatch(
            rule_name="rule1",
            rule=mock_rule1,
            confidence=0.95
        )
        
        mock_match2 = RuleMatch(
            rule_name="rule2",
            rule=mock_rule2,
            confidence=0.85
        )
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match1, mock_match2]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    processor.process_email(
                        email_source="test.eml",
                        rules=[mock_rule1, mock_rule2],
                        actions=[]
                    )
        
        monitor = PipelineMonitor(processor)
        performance = monitor.get_rule_performance()
        
        assert "rule1" in performance
        assert "rule2" in performance
        assert performance["rule1"]["matches"] == 1
        assert performance["rule2"]["matches"] == 1

    def test_get_action_performance(self):
        """Test getting action performance metrics."""
        processor = EmailProcessor()
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        mock_action_result = {
            "action": "move",
            "success": True,
            "details": "Moved to folder"
        }
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[mock_action_result]):
                    processor.process_email(
                        email_source="test.eml",
                        rules=[mock_rule],
                        actions=[(ActionType.MOVE, {"destination": "inbox"})]
                    )
        
        monitor = PipelineMonitor(processor)
        performance = monitor.get_action_performance()
        
        assert "move" in performance
        assert performance["move"]["count"] == 1


class TestPipelineConfig:
    """Tests for PipelineConfig class."""

    def test_config_default_values(self):
        """Test config with default values."""
        config = PipelineConfig()
        
        assert config.base_path == "./archive"
        assert config.dry_run is False
        assert config.collision_strategy == "rename"
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_config_to_processor(self):
        """Test converting config to processor."""
        config = PipelineConfig(
            base_path="/tmp/test",
            dry_run=True,
            collision_strategy="skip",
            max_retries=5,
            retry_delay=2.0
        )
        
        processor = config.to_processor()
        
        assert processor.base_path == "/tmp/test"
        assert processor.dry_run is True
        assert processor.collision_strategy == "skip"
        assert processor.max_retries == 5
        assert processor.retry_delay == 2.0

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "base_path": "/tmp/test",
            "dry_run": True,
            "collision_strategy": "skip",
            "max_retries": 5,
            "retry_delay": 2.0
        }
        
        config = PipelineConfig.from_dict(config_dict)
        
        assert config.base_path == "/tmp/test"
        assert config.dry_run is True
        assert config.collision_strategy == "skip"
        assert config.max_retries == 5
        assert config.retry_delay == 2.0

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = PipelineConfig(
            base_path="/tmp/test",
            dry_run=True,
            collision_strategy="skip",
            max_retries=5,
            retry_delay=2.0
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["base_path"] == "/tmp/test"
        assert config_dict["dry_run"] is True
        assert config_dict["collision_strategy"] == "skip"
        assert config_dict["max_retries"] == 5
        assert config_dict["retry_delay"] == 2.0

    def test_config_from_dict_defaults(self):
        """Test creating config from dictionary with defaults."""
        config_dict = {}
        
        config = PipelineConfig.from_dict(config_dict)
        
        assert config.base_path == "./archive"
        assert config.dry_run is False
        assert config.collision_strategy == "rename"
        assert config.max_retries == 3
        assert config.retry_delay == 1.0


class TestEmailProcessorIntegration:
    """Integration tests for the email processor."""

    def test_full_processing_pipeline(self, tmp_path):
        """Test full processing pipeline."""
        processor = EmailProcessor()
        
        # Create test email file
        test_email_path = tmp_path / "test.eml"
        test_email_path.write_text("Test email content")
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        mock_action_result = {
            "action": "move",
            "success": True,
            "details": "Moved to folder"
        }
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[mock_action_result]):
                    result = processor.process_email(
                        email_source=str(test_email_path),
                        rules=[mock_rule],
                        actions=[(ActionType.MOVE, {"destination": "inbox"})]
                    )
                    
                    assert result["success"] is True
                    assert result["email_id"] == "test_email_123"
                    assert len(result["matches"]) == 1
                    assert len(result["actions_performed"]) == 1
                    
                    stats = processor.get_stats()
                    assert stats["total_processed"] == 1
                    assert stats["total_matched"] == 1
                    assert stats["by_rule"]["test_rule"] == 1
                    assert stats["by_action"]["move"] == 1

    def test_processor_with_multiple_emails(self, tmp_path):
        """Test processor with multiple emails."""
        processor = EmailProcessor()
        
        # Create test email files
        for i in range(5):
            (tmp_path / f"test{i}.eml").write_text(f"Email {i}")
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        with patch.object(processor.parser, 'parse', return_value=mock_email):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    results = processor.process_batch(
                        email_sources=[str(tmp_path / f"test{i}.eml") for i in range(5)],
                        rules=[mock_rule],
                        actions=[]
                    )
                    
                    assert len(results) == 5
                    assert all(r["success"] is True for r in results)
                    
                    stats = processor.get_stats()
                    assert stats["total_processed"] == 5
                    assert stats["total_matched"] == 5

    def test_processor_error_recovery(self, tmp_path):
        """Test processor error recovery."""
        processor = EmailProcessor()
        
        # Create test email files
        for i in range(3):
            (tmp_path / f"test{i}.eml").write_text(f"Email {i}")
        
        mock_email = MagicMock()
        mock_email.id = "test_email_123"
        
        call_count = [0]
        
        def parse_side_effect(source):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Parse error")
            return mock_email
        
        mock_rule = MagicMock()
        mock_rule.name = "test_rule"
        
        mock_match = RuleMatch(
            rule_name="test_rule",
            rule=mock_rule,
            confidence=0.95
        )
        
        with patch.object(processor.parser, 'parse', side_effect=parse_side_effect):
            with patch.object(processor.matcher, 'match', return_value=[mock_match]):
                with patch.object(processor.executor, 'execute', return_value=[]):
                    results = processor.process_batch(
                        email_sources=[str(tmp_path / f"test{i}.eml") for i in range(3)],
                        rules=[mock_rule],
                        actions=[]
                    )
                    
                    assert len(results) == 3
                    assert results[0]["success"] is True
                    assert results[1]["success"] is False
                    assert results[2]["success"] is True
                    
                    stats = processor.get_stats()
                    assert stats["total_processed"] == 3
                    assert stats["total_failed"] == 1
                    assert stats["total_matched"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
