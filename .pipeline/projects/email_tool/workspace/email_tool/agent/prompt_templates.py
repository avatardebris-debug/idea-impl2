"""Prompt templates for LLM-powered email processing."""

from typing import Any, Dict, List, Optional


class PromptTemplates:
    """
    Manages prompt templates for LLM interactions.
    
    All prompts are configurable and version-controlled to ensure
    consistency and reproducibility across different runs.
    """
    
    # Version tracking for prompt templates
    VERSION = "1.0.0"
    
    # Rule generation prompt template
    RULE_GENERATION_PROMPT = """You are an email organization assistant. Your task is to generate email filtering rules based on a natural language description. Generate email rules that match the user's requirements.

Available rule types:
- from_exact: Match exact sender email address
- from_pattern: Match sender using regex pattern
- subject_exact: Match exact subject line
- subject_contains: Match if subject contains specific text
- subject_pattern: Match subject using regex pattern
- body_contains_exact: Match if body contains specific text
- body_contains_contains: Match if body contains specific text (case-insensitive)
- body_contains_pattern: Match body using regex pattern (case-sensitive)
- has_attachment: Match emails with attachments

Rule properties:
- name: Unique identifier for the rule
- type: One of the rule types listed above
- pattern: The pattern or value to match (required for most rule types)
- priority: Integer from 0-100 (higher = more important)
- category: Category name for the email (e.g., "invoices", "receipts", "personal")
- description: Human-readable description of the rule

Sample emails for reference:
{sample_emails}

User description:
{description}

Generate rules in JSON format as a list. Each rule should have: name, type, pattern, priority, category, and description.

Example output format:
[
  {{
    "name": "amazon_invoices",
    "type": "from_exact",
    "pattern": "orders@amazon.com",
    "priority": 80,
    "category": "invoices",
    "description": "Amazon invoice emails"
  }}
]

Only return the JSON array, no additional text."""
    
    # Categorization prompt template
    CATEGORIZATION_PROMPT = """You are an email categorization assistant. Your task is to suggest categories for emails that don't match any existing rules. suggest categories based on email content.

Existing categories in use:
{existing_categories}

Sample uncategorized emails:
{sample_emails}

For each email, suggest a category that best describes its content. Categories should be:
- Descriptive of the email content
- Consistent with existing categories when possible
- Specific enough to be useful for organization

Output format: JSON array with email_id and suggested_category.

Example output format:
[
  {{
    "email_id": "email_123",
    "suggested_category": "receipts",
    "reason": "Email contains purchase confirmation from Amazon"
  }}
]

Only return the JSON array, no additional text."""
    
    # Summarization prompt template
    SUMMARIZATION_PROMPT = """You are an email organization assistant. Your task is to generate a summary of inbox organization status.

Email analysis:
{email_summary}

Active rules:
{rules_summary}

Rule matches:
{matches_summary}

Generate a concise summary that includes:
1. Total number of emails analyzed
2. Count of emails matching each category
3. Count of emails not matching any rule (unclassified)
4. Any notable patterns or recommendations

Example output format:
"You have 15 unread invoices, 8 receipts from Amazon, 3 meeting requests, and 12 unclassified emails."

Only return the summary text, no additional formatting."""
    
    # Few-shot examples for rule generation
    RULE_GENERATION_EXAMPLES = """Here are some examples of good rule generation:

User: "Organize all invoices from vendors"
Rules: [
  {{"name": "vendor_invoices", "type": "subject_contains", "pattern": "invoice", "priority": 70, "category": "invoices", "description": "Invoice emails from vendors"}},
  {{"name": "vendor_invoices_2", "type": "from_pattern", "pattern": "@.*\\.com$", "priority": 60, "category": "invoices", "description": "Invoices from any email address"}}
]

User: "Move all meeting requests to a folder"
Rules: [
  {{"name": "meeting_requests", "type": "subject_contains", "pattern": "meeting", "priority": 75, "category": "meetings", "description": "Meeting request emails"}}
]

User: "Flag urgent emails from my boss"
Rules: [
  {{"name": "boss_urgent", "type": "from_exact", "pattern": "boss@company.com", "priority": 90, "category": "urgent", "description": "Urgent emails from boss"}}
]"""
    
    # Few-shot examples for categorization
    CATEGORIZATION_EXAMPLES = """Here are some examples of good categorization:

Email: "Your order #12345 has shipped" from orders@amazon.com
Suggested category: "receipts"
Reason: Email contains order confirmation and shipping information

Email: "Team lunch on Friday" from sarah@company.com
Suggested category: "personal"
Reason: Personal communication about team activities

Email: "Project Alpha status update" from mike@company.com
Suggested category: "work"
Reason: Work-related project update"""
    
    # Few-shot examples for summarization
    SUMMARIZATION_EXAMPLES = """Here are some examples of good summarization:

Example 1:
You have 15 unread invoices, 8 receipts from Amazon, 3 meeting requests, and 12 unclassified emails.

Example 2:
Your inbox contains 25 emails total. 18 are categorized (10 work, 5 personal, 3 invoices), and 7 are unclassified. Consider creating rules for the unclassified emails.

Example 3:
Inbox organization status: 42 emails analyzed. 30 emails match rules (15 work, 10 personal, 5 invoices), 12 emails are unclassified. Top categories: work (15), personal (10), invoices (5)."""
    
    def __init__(self, 
                 rule_generation_prompt: Optional[str] = None,
                 categorization_prompt: Optional[str] = None,
                 summarization_prompt: Optional[str] = None,
                 enable_few_shot: bool = True):
        """
        Initialize prompt templates.
        
        Args:
            rule_generation_prompt: Custom prompt for rule generation.
            categorization_prompt: Custom prompt for categorization.
            summarization_prompt: Custom prompt for summarization.
            enable_few_shot: Whether to include few-shot examples.
        """
        self.rule_generation_prompt = rule_generation_prompt or self.RULE_GENERATION_PROMPT
        self.categorization_prompt = categorization_prompt or self.CATEGORIZATION_PROMPT
        self.summarization_prompt = summarization_prompt or self.SUMMARIZATION_PROMPT
        self.enable_few_shot = enable_few_shot
    
    def get_rule_generation_prompt(self, 
                                   description: str, 
                                   sample_emails: List[Dict[str, Any]],
                                   few_shot: bool = True,
                                   custom_prompt: Optional[str] = None) -> str:
        """
        Get the rule generation prompt with filled variables.
        
        Args:
            description: Natural language description of desired rules.
            sample_emails: Sample emails to inform rule generation.
            few_shot: Whether to include few-shot examples.
            custom_prompt: Custom prompt template to use instead of default.
        
        Returns:
            Formatted prompt string.
        """
        sample_emails_str = self._format_emails_for_prompt(sample_emails)
        
        prompt_template = custom_prompt or self.rule_generation_prompt
        
        prompt = prompt_template.format(
            description=description,
            sample_emails=sample_emails_str
        )
        
        if few_shot and self.enable_few_shot:
            prompt += "\n\n" + self.RULE_GENERATION_EXAMPLES
        
        return prompt
    
    def get_categorization_prompt(self,
                                  emails: List[Dict[str, Any]],
                                  rules: List[Dict[str, Any]] = None,
                                  few_shot: bool = True,
                                  custom_prompt: Optional[str] = None,
                                  existing_categories: Optional[List[str]] = None) -> str:
        """
        Get the categorization prompt with filled variables.
        
        Args:
            emails: List of emails to categorize.
            rules: List of rules that matched emails.
            few_shot: Whether to include few-shot examples.
            custom_prompt: Custom prompt template to use instead of default.
            existing_categories: List of existing categories.
        
        Returns:
            Formatted prompt string.
        """
        sample_emails_str = self._format_emails_for_prompt(emails)
        
        # Build existing categories string
        if existing_categories:
            categories_str = "\n".join([f"- {cat}" for cat in existing_categories])
        elif rules:
            categories_str = "\n".join([f"- {rule.get('name', 'Unnamed')}: {rule.get('type', 'unknown')} -> {rule.get('category', 'uncategorized')}" for rule in rules])
        else:
            categories_str = "No existing categories"
        
        prompt_template = custom_prompt or self.categorization_prompt
        
        prompt = prompt_template.format(
            existing_categories=categories_str,
            sample_emails=sample_emails_str
        )
        
        if few_shot and self.enable_few_shot:
            prompt += "\n\n" + self.CATEGORIZATION_EXAMPLES
        
        return prompt
    
    def get_summarization_prompt(self,
                                 emails: List[Dict[str, Any]],
                                 rules: List[Dict[str, Any]],
                                 matches: List[Dict[str, Any]],
                                 few_shot: bool = True,
                                 custom_prompt: Optional[str] = None) -> str:
        """
        Get the summarization prompt with filled variables.
        
        Args:
            emails: List of emails to summarize.
            rules: List of rules that matched emails.
            matches: Rule-match information.
            few_shot: Whether to include few-shot examples.
            custom_prompt: Custom prompt template to use instead of default.
        
        Returns:
            Formatted prompt string.
        """
        # Build email summary
        if not emails:
            return "No emails in inbox to summarize."
        
        email_summary = f"Total emails: {len(emails)}\n"
        for email in emails[:5]:  # Show first 5 emails
            email_summary += f"- Email {email.get('id', 'unknown')}: {email.get('subject', 'No subject')} from {email.get('from', 'Unknown')}\n"
        
        # Build rules summary
        rules_summary = f"Active rules: {len(rules)}\n"
        for rule in rules[:5]:  # Show first 5 rules
            rules_summary += f"- {rule.get('name', 'Unnamed')}: {rule.get('type', 'unknown')} -> {rule.get('category', 'uncategorized')}\n"
        
        # Build matches summary
        matches_summary = f"Rule matches: {len(matches)}\n"
        for match in matches[:5]:  # Show first 5 matches
            matches_summary += f"- Email {match.get('email_id', 'unknown')} matched {match.get('rule_name', 'unknown')} with confidence {match.get('confidence', 0)}\n"
        
        prompt_template = custom_prompt or self.summarization_prompt
        
        prompt = prompt_template.format(
            email_summary=email_summary,
            rules_summary=rules_summary,
            matches_summary=matches_summary
        )
        
        if few_shot and self.enable_few_shot:
            prompt += "\n\n" + self.SUMMARIZATION_EXAMPLES
        
        return prompt
    
    def inbox_summarization(self,
                           emails: List[Dict[str, Any]],
                           rules: List[Dict[str, Any]],
                           matches: List[Dict[str, Any]],
                           few_shot: bool = True) -> str:
        """
        Generate inbox summarization prompt.
        
        Args:
            emails: List of emails to summarize.
            rules: List of rules that matched emails.
            matches: Rule-match information.
            few_shot: Whether to include few-shot examples.
        
        Returns:
            Formatted prompt string.
        """
        # Build email summary
        email_summary = f"Total emails: {len(emails)}\n"
        for email in emails[:5]:  # Show first 5 emails
            email_summary += f"- Email {email.get('id', 'unknown')}: {email.get('subject', 'No subject')}\n"
        
        # Build rules summary
        rules_summary = f"Active rules: {len(rules)}\n"
        for rule in rules[:5]:  # Show first 5 rules
            rules_summary += f"- {rule.get('name', 'Unnamed')}: {rule.get('type', 'unknown')} -> {rule.get('category', 'uncategorized')}\n"
        
        # Build matches summary
        matches_summary = f"Rule matches: {len(matches)}\n"
        for match in matches[:5]:  # Show first 5 matches
            matches_summary += f"- Email {match.get('email_id', 'unknown')} matched {match.get('rule_name', 'unknown')}\n"
        
        # Generate prompt
        prompt = """You are an email organization assistant. Your task is to summarize the inbox organization status.

Email Summary:
{email_summary}

Rules Summary:
{rules_summary}

Rule Matches:
{matches_summary}

Please provide a concise summary of the inbox organization status, including:
1. Total number of emails
2. How many emails are categorized vs uncategorized
3. Which categories have the most emails
4. Any recommendations for improving organization

Provide your response in plain text."""
        
        return prompt.format(
            email_summary=email_summary,
            rules_summary=rules_summary,
            matches_summary=matches_summary
        )
    
    def _format_emails_for_prompt(self, emails: List[Dict[str, Any]]) -> str:
        """
        Format emails for inclusion in prompts.
        
        Args:
            emails: List of email dictionaries.
        
        Returns:
            Formatted string suitable for LLM prompts.
        """
        if not emails:
            return "No sample emails provided."
        
        formatted = []
        for i, email in enumerate(emails[:5]):  # Limit to 5 for context
            email_str = f"Email {i+1}:\n"
            email_str += f"  From: {email.get('from', 'Unknown')}\n"
            email_str += f"  Subject: {email.get('subject', 'No subject')}\n"
            email_str += f"  Date: {email.get('date', 'Unknown date')}\n"
            email_str += f"  Has attachments: {email.get('has_attachments', False)}\n"
            if email.get('body'):
                body_preview = email['body'][:150] + "..." if len(email['body']) > 150 else email['body']
                email_str += f"  Body preview: {body_preview}\n"
            formatted.append(email_str)
        
        if len(emails) > 5:
            formatted.append(f"... and {len(emails) - 5} more emails")
        
        return "\n".join(formatted)
    
    def get_version(self) -> str:
        """Get the version of the prompt templates."""
        return self.VERSION
