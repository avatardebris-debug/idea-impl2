"""
Phase 6 Implementation

This module demonstrates the usage of Phase 6 email processing models.
"""

from datetime import datetime
from typing import List, Optional
from email_tool.models import (
    Email,
    Rule,
    RuleMatch,
    RuleType,
    RuleMatchType,
    Category,
    ActionType,
    ActionExecutionResult
)


def create_sample_email() -> Email:
    """Create a sample email for testing."""
    return Email(
        id="email-001",
        from_addr="sender@example.com",
        to_addrs=["recipient@example.com", "cc@example.com"],
        subject="Test Email Subject",
        date=datetime.now(),
        body_plain="This is the plain text body of the email.",
        body_html="<p>This is the HTML body of the email.</p>",
        attachments=["attachment1.pdf", "attachment2.docx"],
        raw_headers={
            "Message-ID": "<001@example.com>",
            "X-Priority": "1"
        },
        labels=["important", "work"],
        source_path="/path/to/email.eml"
    )


def create_sample_rule() -> Rule:
    """Create a sample rule for testing."""
    return Rule(
        name="Important Work Email",
        rule_type=RuleType.SUBJECT_CONTAINS,
        pattern="urgent",
        priority=80,
        category="work",
        labels=["work", "urgent"],
        description="Matches emails with 'urgent' in the subject"
    )


def create_sample_rule_match(rule: Rule, email: Email) -> RuleMatch:
    """Create a sample rule match."""
    return RuleMatch(
        rule=rule,
        match_type=RuleMatchType.CONTAINS,
        matched_value="urgent",
        confidence=0.95,
        rule_name=rule.name
    )


def create_sample_action_result() -> ActionExecutionResult:
    """Create a sample action execution result."""
    return ActionExecutionResult(
        action_type=ActionType.ADD_LABEL,
        success=True,
        message="Label 'work' added successfully",
        details={"label": "work", "email_id": "email-001"}
    )


def demonstrate_email_processing():
    """Demonstrate email processing with Phase 6 models."""
    print("=" * 60)
    print("Phase 6 Email Processing Demonstration")
    print("=" * 60)
    
    # Create sample email
    email = create_sample_email()
    print(f"\nCreated email: {email}")
    print(f"  From: {email.from_addr}")
    print(f"  To: {', '.join(email.to_addrs)}")
    print(f"  Subject: {email.subject}")
    print(f"  Labels: {email.labels}")
    
    # Create sample rule
    rule = create_sample_rule()
    print(f"\nCreated rule: {rule}")
    print(f"  Type: {rule.rule_type.value}")
    print(f"  Pattern: {rule.pattern}")
    print(f"  Priority: {rule.priority}")
    
    # Create rule match
    match = create_sample_rule_match(rule, email)
    print(f"\nCreated rule match: {match}")
    print(f"  Match type: {match.match_type.value}")
    print(f"  Matched value: {match.matched_value}")
    print(f"  Confidence: {match.confidence}")
    
    # Create action execution result
    result = create_sample_action_result()
    print(f"\nCreated action result: {result}")
    print(f"  Success: {result.success}")
    print(f"  Message: {result.message}")
    print(f"  Details: {result.details}")
    
    # Demonstrate email to EML conversion
    print(f"\nEmail as EML:")
    print(email.to_eml())
    
    print("\n" + "=" * 60)
    print("Demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_email_processing()
