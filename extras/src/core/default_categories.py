"""Default categories and rules for BudgetFlow Tracker."""

from __future__ import annotations

DEFAULT_CATEGORIES = [
    {"name": "Food & Drink", "description": "Groceries, restaurants, dining out", "is_income": False},
    {"name": "Transportation", "description": "Gas, public transit, rideshare", "is_income": False},
    {"name": "Housing", "description": "Rent, mortgage, utilities", "is_income": False},
    {"name": "Entertainment", "description": "Movies, games, hobbies", "is_income": False},
    {"name": "Shopping", "description": "Clothing, electronics, general purchases", "is_income": False},
    {"name": "Healthcare", "description": "Medical bills, prescriptions, insurance", "is_income": False},
    {"name": "Education", "description": "Tuition, books, courses", "is_income": False},
    {"name": "Salary", "description": "Regular employment income", "is_income": True},
    {"name": "Freelance", "description": "Contract work, side gigs", "is_income": True},
    {"name": "Investments", "description": "Dividends, interest, capital gains", "is_income": True},
    {"name": "Other Income", "description": "Miscellaneous income sources", "is_income": True},
    {"name": "Uncategorized", "description": "Transactions without a category", "is_income": False},
]
