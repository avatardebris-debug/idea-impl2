"""Template engine for generating YouTube video titles.

Provides a collection of pre-built templates organized by category,
with support for variable substitution and custom templates.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .config import Config


@dataclass
class Template:
    """A title template with a pattern and metadata.

    Attributes:
        name: Unique name for the template.
        category: Category of the template (e.g., "tutorial", "review").
        pattern: Template pattern with {variable} placeholders.
        variables: List of variables used in the pattern.
    """

    name: str
    category: str
    pattern: str
    variables: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Extract variables from pattern."""
        if not self.variables:
            self.variables = self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """Extract variable names from pattern."""
        import re
        return re.findall(r"\{(\w+)\}", self.pattern)

    def fill_in(self, **kwargs: Any) -> str:
        """Fill in template variables and return rendered title.

        Args:
            **kwargs: Variable values to substitute.

        Returns:
            Rendered title string.
        """
        result = self.pattern
        for var in self.variables:
            value = kwargs.get(var, f"{var.capitalize()}")
            result = result.replace(f"{{{var}}}", str(value))
        return result


# ── Built-in templates ────────────────────────────────────────────────────

BUILTIN_TEMPLATES: List[Dict[str, Any]] = [
    # Tutorial templates
    {
        "name": "tutorial_basic",
        "category": "tutorial",
        "pattern": "How to {topic} in {time} minutes",
    },
    {
        "name": "tutorial_beginner",
        "category": "tutorial",
        "pattern": "Learn {topic} for Beginners - Complete Guide",
    },
    {
        "name": "tutorial_advanced",
        "category": "tutorial",
        "pattern": "Advanced {topic} Techniques You Need to Know",
    },
    {
        "name": "tutorial_step_by_step",
        "category": "tutorial",
        "pattern": "{topic}: Step-by-Step Tutorial",
    },
    {
        "name": "tutorial_quick",
        "category": "tutorial",
        "pattern": "Quick {topic} Tutorial - Get Started Now",
    },

    # Review templates
    {
        "name": "review_basic",
        "category": "review",
        "pattern": "{topic} Review - Is It Worth It?",
    },
    {
        "name": "review_honest",
        "category": "review",
        "pattern": "Honest {topic} Review - Pros and Cons",
    },
    {
        "name": "review_comparison",
        "category": "review",
        "pattern": "{topic} vs Competitors - Which Is Better?",
    },
    {
        "name": "review_buying_guide",
        "category": "review",
        "pattern": "Best {topic} - Buying Guide 2024",
    },

    # Listicle templates
    {
        "name": "list_top_10",
        "category": "listicle",
        "pattern": "Top 10 {topic} Tips You Need to Know",
    },
    {
        "name": "list_top_5",
        "category": "listicle",
        "pattern": "5 Best {topic} Strategies for Success",
    },
    {
        "name": "list_mistakes",
        "category": "listicle",
        "pattern": "7 Common {topic} Mistakes to Avoid",
    },
    {
        "name": "list_secrets",
        "category": "listicle",
        "pattern": "10 {topic} Secrets Nobody Tells You",
    },

    # Question templates
    {
        "name": "question_what",
        "category": "question",
        "pattern": "What Is {topic}? Everything Explained",
    },
    {
        "name": "question_how",
        "category": "question",
        "pattern": "How Does {topic} Work? Complete Breakdown",
    },
    {
        "name": "question_why",
        "category": "question",
        "pattern": "Why {topic} Matters More Than You Think",
    },

    # How-to templates
    {
        "name": "howto_complete",
        "category": "howto",
        "pattern": "Complete Guide to {topic} - From Zero to Hero",
    },
    {
        "name": "howto_beginner",
        "category": "howto",
        "pattern": "{topic} for Complete Beginners",
    },
    {
        "name": "howto_pro",
        "category": "howto",
        "pattern": "Master {topic} Like a Pro",
    },

    # Update templates
    {
        "name": "update_new",
        "category": "update",
        "pattern": "New {topic} Features You Need to See",
    },
    {
        "name": "update_tips",
        "category": "update",
        "pattern": "Latest {topic} Tips and Tricks",
    },

    # Comparison templates
    {
        "name": "comparison_vs",
        "category": "comparison",
        "pattern": "{topic} vs {comparison} - The Ultimate Showdown",
    },
    {
        "name": "comparison_best",
        "category": "comparison",
        "pattern": "Best {topic} Options Compared",
    },

    # List templates
    {
        "name": "list_essentials",
        "category": "list",
        "pattern": "Essential {topic} Tools You Need",
    },
    {
        "name": "list_resources",
        "category": "list",
        "pattern": "Top {topic} Resources for 2024",
    },

    # Time-based templates
    {
        "name": "time_10min",
        "category": "time",
        "pattern": "Learn {topic} in 10 Minutes",
    },
    {
        "name": "time_30min",
        "category": "time",
        "pattern": "Master {topic} in 30 Minutes",
    },
    {
        "name": "time_1hour",
        "category": "time",
        "pattern": "Complete {topic} Course in 1 Hour",
    },

    # Problem-solution templates
    {
        "name": "problem_solution",
        "category": "problem",
        "pattern": "Solve {topic} Problems Once and for All",
    },
    {
        "name": "problem_fix",
        "category": "problem",
        "pattern": "Fix Your {topic} Issues - Easy Solutions",
    },

    # Benefit templates
    {
        "name": "benefit_transform",
        "category": "benefit",
        "pattern": "Transform Your {topic} Skills in Days",
    },
    {
        "name": "benefit_improve",
        "category": "benefit",
        "pattern": "Improve Your {topic} Game - Pro Tips",
    },
    {
        "name": "benefit_results",
        "category": "benefit",
        "pattern": "Get Better {topic} Results - Guaranteed",
    },

    # Trending templates
    {
        "name": "trending_now",
        "category": "trending",
        "pattern": "Why Everyone Is Talking About {topic}",
    },
    {
        "name": "trending_viral",
        "category": "trending",
        "pattern": "The {topic} Trend Explained",
    },

    # Ultimate templates
    {
        "name": "ultimate_complete",
        "category": "ultimate",
        "pattern": "The Ultimate {topic} Guide - Everything You Need",
    },
    {
        "name": "ultimate_master",
        "category": "ultimate",
        "pattern": "Ultimate {topic} Masterclass",
    },
]


class TemplateEngine:
    """Engine for generating titles using templates.

    Attributes:
        templates: List of available templates.
        custom_templates: List of user-defined templates.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize template engine.

        Args:
            config: Optional configuration for template selection.
        """
        self.config = config or Config()
        self.templates: List[Template] = []
        self.custom_templates: List[Template] = []
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        for template_data in BUILTIN_TEMPLATES:
            template = Template(
                name=template_data["name"],
                category=template_data["category"],
                pattern=template_data["pattern"],
            )
            self.templates.append(template)

    def add_template(self, name: str, category: str, pattern: str) -> None:
        """Add a custom template.

        Args:
            name: Unique template name.
            category: Template category.
            pattern: Template pattern with {variable} placeholders.
        """
        template = Template(name=name, category=category, pattern=pattern)
        self.custom_templates.append(template)

    def get_templates_by_category(self, category: str) -> List[Template]:
        """Get all templates in a category.

        Args:
            category: Category name to filter by.

        Returns:
            List of templates in the category.
        """
        all_templates = self.templates + self.custom_templates
        return [t for t in all_templates if t.category == category]

    def get_random_template(self, category: Optional[str] = None) -> Template:
        """Get a random template.

        Args:
            category: Optional category to filter by.

        Returns:
            Random template from available templates.
        """
        all_templates = self.templates + self.custom_templates

        if category:
            templates = [t for t in all_templates if t.category == category]
        else:
            templates = all_templates

        if not templates:
            templates = all_templates

        return random.choice(templates)

    def generate_title(self, topic: str, category: Optional[str] = None) -> str:
        """Generate a title using a random template.

        Args:
            topic: Topic to use in the title.
            category: Optional category to filter templates.

        Returns:
            Generated title string.
        """
        template = self.get_random_template(category)
        return template.fill_in(topic=topic)

    def generate_titles(
        self,
        topic: str,
        num_titles: int = 10,
        categories: Optional[List[str]] = None,
    ) -> List[str]:
        """Generate multiple unique titles.

        Args:
            topic: Topic to use in titles.
            num_titles: Number of titles to generate.
            categories: Optional list of categories to use.

        Returns:
            List of unique generated titles.
        """
        titles: Set[str] = set()
        attempts = 0
        max_attempts = num_titles * 10

        while len(titles) < num_titles and attempts < max_attempts:
            category = random.choice(categories) if categories else None
            title = self.generate_title(topic, category)
            titles.add(title)
            attempts += 1

        return list(titles)

    def get_categories(self) -> List[str]:
        """Get all available template categories.

        Returns:
            List of category names.
        """
        all_templates = self.templates + self.custom_templates
        categories: Set[str] = {t.category for t in all_templates}
        return sorted(list(categories))
