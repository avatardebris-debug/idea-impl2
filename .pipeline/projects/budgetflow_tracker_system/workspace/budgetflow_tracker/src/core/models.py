"""Pydantic data models for BudgetFlow Tracker."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TransactionType(str, Enum):
    """Type of a financial transaction."""
    DEBIT = "debit"
    CREDIT = "credit"


class Category(BaseModel):
    """A spending/income category."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    is_income: bool = False
    is_active: bool = True
    parent_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Category name cannot be empty")
        return v.strip()


class Transaction(BaseModel):
    """A single financial transaction."""
    id: Optional[int] = None
    date: date = Field(..., description="Transaction date")
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0)
    transaction_type: TransactionType = TransactionType.DEBIT
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    account_id: Optional[int] = None
    merchant: Optional[str] = None
    confidence: Optional[float] = None  # Categorization confidence 0.0-1.0
    is_reconciled: bool = False
    imported_at: Optional[datetime] = None

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Transaction description cannot be empty")
        return v.strip()

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class Budget(BaseModel):
    """A budget for a category over a time period."""
    id: Optional[int] = None
    category_id: int = Field(..., gt=0)
    category_name: str = ""
    amount: Decimal = Field(..., gt=0)
    period: str = Field(..., pattern="^(monthly|weekly)$")
    start_date: date = Field(..., description="Budget period start date")
    is_active: bool = True
    rollover: bool = False
    rollover_amount: Decimal = 0

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Budget amount must be positive")
        return v


class TransactionRule(BaseModel):
    """A rule for auto-categorizing transactions."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    pattern: str = Field(..., min_length=1)
    pattern_type: str = Field(default="contains", pattern="^(contains|regex|exact)$")
    category_id: int = Field(..., gt=0)
    category_name: str = ""
    priority: int = Field(default=0, ge=0)
    is_active: bool = True
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rule name cannot be empty")
        return v.strip()


class Account(BaseModel):
    """A bank account."""
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    account_type: str = Field(default="checking", description="checking, savings, credit, etc.")
    is_active: bool = True
    created_at: Optional[datetime] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Account name cannot be empty")
        return v.strip()
