"""Inbox summarizer module for email organization."""

from typing import List, Dict, Any, Optional
from email_tool.agent.base import AgentResult


class InboxSummarizer:
    """Summarizes inbox organization status."""
    
    def __init__(self):
        """Initialize the inbox summarizer."""
        self.enabled = True
    
    def summarize_inbox(
        self,
        emails: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        matches: List[Dict[str, Any]]
    ) -> AgentResult:
        """
        Summarize inbox organization status.
        
        Args:
            emails: List of email dictionaries.
            rules: List of rule dictionaries.
            matches: List of match dictionaries.
            
        Returns:
            AgentResult with summary data.
        """
        if not emails:
            return AgentResult(
                success=True,
                data="No emails in inbox.",
                metadata={
                    "total_emails": 0,
                    "matched_emails": 0,
                    "unclassified_emails": 0,
                    "category_counts": {},
                    "rule_counts": {}
                }
            )
        
        # Count categorized emails (those with a valid category, not "uncategorized")
        categorized_count = 0
        uncategorized_count = 0
        category_counts = {}
        
        for email in emails:
            category = email.get("category")
            if category and category not in ("uncategorized", "unclassified"):
                categorized_count += 1
                category_counts[category] = category_counts.get(category, 0) + 1
            else:
                uncategorized_count += 1
        
        # Count active rules
        active_rules_count = len(rules)
        
        # Count matched emails
        matched_emails_count = len(matches)
        
        # Build summary
        summary_parts = []
        
        # Email count
        summary_parts.append(f"You have {len(emails)} emails.")
        
        # Categorization summary (use singular when count is 1)
        if categorized_count > 0:
            if categorized_count == 1:
                summary_parts.append("1 categorized.")
            else:
                summary_parts.append(f"{categorized_count} categorized.")
        
        if uncategorized_count == 0:
            summary_parts.append("0 uncategorized.")
        elif uncategorized_count == 1:
            summary_parts.append("1 uncategorized.")
        else:
            summary_parts.append(f"{uncategorized_count} uncategorized.")
        
        # Category breakdown
        if category_counts:
            category_parts = []
            for cat, count in sorted(category_counts.items()):
                if count == 1:
                    category_parts.append("1 " + cat)
                else:
                    category_parts.append(f"{count} {cat}")
            if category_parts:
                summary_parts.append(f"Categories: {', '.join(category_parts)}.")
        
        # Rules summary (use singular when count is 1)
        if active_rules_count == 1:
            summary_parts.append("1 active rule.")
        else:
            summary_parts.append(f"{active_rules_count} active rules.")
        
        # Matches summary (use singular when count is 1)
        if matched_emails_count == 1:
            summary_parts.append("1 matched.")
        else:
            summary_parts.append(f"{matched_emails_count} matched.")
        
        # Top rules
        if rules:
            top_rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)[:3]
            rule_names = [r.get("name", "unknown") for r in top_rules]
            summary_parts.append(f"Top rules: {', '.join(rule_names)}.")
        
        summary = " ".join(summary_parts)
        
        return AgentResult(
            success=True,
            data=summary,
            metadata={
                "total_emails": len(emails),
                "matched_emails": matched_emails_count,
                "unclassified_emails": uncategorized_count,
                "category_counts": category_counts,
                "rule_counts": {r.get("name", "unknown"): 1 for r in rules}
            }
        )
