"""Tests for the organizer module."""

import os
import pytest
import tempfile
import yaml
from datetime import datetime
from email_tool.models import Email, Rule, RuleType
from email_tool.organizer import EmailOrganizer, OrganizerBuilder, create_organizer


class TestEmailOrganizer:
    """Tests for the EmailOrganizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = EmailOrganizer(
            base_path=self.temp_dir,
            dry_run=True,
            collision_strategy="rename"
        )
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test organizer initialization."""
        assert self.organizer.base_path == self.temp_dir
        assert self.organizer.dry_run is True
        assert self.organizer.collision_strategy == "rename"
    
    def test_load_rules_from_yaml(self):
        """Test loading rules from YAML file."""
        rules_config = {
            "rules": [
                {
                    "name": "test_rule",
                    "type": "subject_contains",
                    "pattern": "test",
                    "priority": 10,
                    "category": "general"
                }
            ]
        }
        
        rules_path = os.path.join(self.temp_dir, "rules.yaml")
        with open(rules_path, 'w') as f:
            yaml.dump(rules_config, f)
        
        rules = self.organizer.load_rules(rules_path)
        
        assert len(rules) == 1
        assert rules[0].name == "test_rule"
        assert rules[0].rule_type == RuleType.SUBJECT_CONTAINS
    
    def test_load_rules_from_dict(self):
        """Test loading rules from dictionary."""
        rules_dict = {
            "rules": [
                {
                    "name": "dict_rule",
                    "type": "from_exact",
                    "pattern": "test@example.com",
                    "priority": 5,
                    "category": "general"
                }
            ]
        }
        
        rules = self.organizer.load_rules_from_dict(rules_dict)
        
        assert len(rules) == 1
        assert rules[0].name == "dict_rule"
        assert rules[0].priority == 5
    
    def test_organize_email_with_match(self):
        """Test organizing an email that matches a rule."""
        # Create a test email file
        email_content = """Subject: Test Email Subject
From: sender@example.com
To: recipient@example.com
Date: 2024-01-01T12:00:00

Test email body"""
        
        email_path = os.path.join(self.temp_dir, "test_email.eml")
        with open(email_path, 'w') as f:
            f.write(email_content)
        
        # Create a matching rule
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="Test",
            priority=10,
            category="general"
        )
        
        # Organize the email
        result = self.organizer.organize_email(
            email_source=email_path,
            rules=[rule],
            output_format="eml"
        )
        
        assert result["success"] is True
        assert result["email_id"] is not None
        assert len(result["matches"]) == 1
        assert result["matches"][0]["rule_name"] == "test_rule"
    
    def test_organize_email_no_match(self):
        """Test organizing an email that doesn't match any rule."""
        # Create a test email file
        email_content = """Subject: Different Subject
From: sender@example.com
To: recipient@example.com
Date: 2024-01-01T12:00:00

Test email body"""
        
        email_path = os.path.join(self.temp_dir, "test_email.eml")
        with open(email_path, 'w') as f:
            f.write(email_content)
        
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="Test",
            priority=10,
            category="general"
        )
        
        result = self.organizer.organize_email(
            email_source=email_path,
            rules=[rule],
            output_format="eml"
        )
        
        assert result["success"] is False
        assert "No matching rules found" in result["errors"]
    
    def test_organize_email_empty_subject(self):
        """Test organizing an email with empty subject."""
        # Create a test email file
        email_content = """Subject: 
From: sender@example.com
To: recipient@example.com
Date: 2024-01-01T12:00:00

Test email body"""
        
        email_path = os.path.join(self.temp_dir, "test_email.eml")
        with open(email_path, 'w') as f:
            f.write(email_content)
        
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.FROM_EXACT,
            pattern="sender@example.com",
            priority=10,
            category="general"
        )
        
        result = self.organizer.organize_email(
            email_source=email_path,
            rules=[rule],
            output_format="eml"
        )
        
        assert result["success"] is True
        assert result["email_id"] is not None
    
    def test_organize_directory(self):
        """Test organizing all emails in a directory."""
        # Create test email files
        source_dir = tempfile.mkdtemp()
        try:
            for i in range(2):
                email_path = os.path.join(source_dir, f"email_{i}.eml")
                with open(email_path, 'w') as f:
                    f.write(f"Subject: Test Email {i}\n")
                    f.write(f"From: sender{i}@example.com\n\n")
                    f.write(f"Test email {i}")
            
            # Create a matching rule
            rule = Rule(
                name="test_rule",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="Test",
                priority=10,
                category="general"
            )
            
            # Organize directory
            result = self.organizer.organize_directory(
                source_dir=source_dir,
                rules=[rule],
                output_format="eml"
            )
            
            assert result["total_processed"] == 2
            assert result["successful"] == 2
            assert result["failed"] == 0
        finally:
            import shutil
            shutil.rmtree(source_dir)
    
    def test_organize_batch(self):
        """Test organizing multiple emails in batch."""
        # Create test email files
        email_paths = []
        for i in range(3):
            email_content = f"""Subject: Test Email {i}
From: sender{i}@example.com
To: recipient@example.com
Date: 2024-01-01T12:00:00

Test email {i}"""
            
            email_path = os.path.join(self.temp_dir, f"email_{i}.eml")
            with open(email_path, 'w') as f:
                f.write(email_content)
            email_paths.append(email_path)
        
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="Test",
            priority=10,
            category="general"
        )
        
        result = self.organizer.organize_batch(
            email_sources=email_paths,
            rules=[rule],
            output_format="eml"
        )
        
        assert result["total_processed"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
    
    def test_reset_statistics(self):
        """Test resetting statistics."""
        self.organizer.reset_statistics()
        stats = self.organizer.get_statistics()
        assert stats["processed"] == 0


class TestOrganizerBuilder:
    """Tests for the OrganizerBuilder class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_add_rule(self):
        """Test adding a single rule."""
        rule = Rule(
            name="test_rule",
            rule_type=RuleType.SUBJECT_CONTAINS,
            pattern="test",
            priority=10,
            category="general"
        )
        
        builder = OrganizerBuilder()
        builder.set_base_path(self.temp_dir)
        builder.add_rule(rule)
        
        organizer = builder.build()
        
        assert isinstance(organizer, EmailOrganizer)
    
    def test_add_rules(self):
        """Test adding multiple rules."""
        rules = [
            Rule(
                name=f"rule{i}",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern=f"test{i}",
                priority=10,
                category="general"
            )
            for i in range(3)
        ]
        
        builder = OrganizerBuilder()
        builder.set_base_path(self.temp_dir)
        builder.add_rules(rules)
        
        organizer = builder.build()
        
        assert isinstance(organizer, EmailOrganizer)
    
    def test_build(self):
        """Test building an organizer."""
        builder = OrganizerBuilder()
        builder.set_base_path(self.temp_dir)
        builder.set_dry_run(True)
        
        organizer = builder.build()
        
        assert isinstance(organizer, EmailOrganizer)
        assert organizer.base_path == self.temp_dir
        assert organizer.dry_run is True


class TestOrganizerIntegration:
    """Integration tests for the organizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.source_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        if os.path.exists(self.source_dir):
            shutil.rmtree(self.source_dir)
    
    def test_full_workflow(self):
        """Test complete email organization workflow."""
        # Create organizer
        organizer = EmailOrganizer(
            base_path=self.temp_dir,
            dry_run=False,
            collision_strategy="rename"
        )
        
        # Create rules
        rules = [
            Rule(
                name="inbox_rule",
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="Important",
                priority=10,
                category="general"
            ),
            Rule(
                name="spam_rule",
                rule_type=RuleType.FROM_EXACT,
                pattern="spam@spammer.com",
                priority=5,
                category="general"
            )
        ]
        
        # Create test emails
        test_emails = [
            {
                "subject": "Important Meeting",
                "from": "boss@company.com",
                "body": "Please attend the meeting"
            },
            {
                "subject": "Spam Offer",
                "from": "spam@spammer.com",
                "body": "Buy now!"
            },
            {
                "subject": "Regular Email",
                "from": "friend@example.com",
                "body": "How are you?"
            }
        ]
        
        # Save test emails
        for i, email_data in enumerate(test_emails):
            email_path = os.path.join(self.source_dir, f"email_{i}.eml")
            with open(email_path, 'w') as f:
                f.write(f"Subject: {email_data['subject']}\n")
                f.write(f"From: {email_data['from']}\n\n")
                f.write(email_data['body'])
        
        # Organize emails
        result = organizer.organize_directory(
            source_dir=self.source_dir,
            rules=rules,
            output_format="eml"
        )
        
        # Verify results
        assert result["total_processed"] == 3
        assert result["successful"] == 2  # 2 emails matched rules
        assert result["failed"] == 1  # 1 email didn't match
        
        # Verify batch results match expectations
        assert result["successful"] == 2
        assert result["failed"] == 1
