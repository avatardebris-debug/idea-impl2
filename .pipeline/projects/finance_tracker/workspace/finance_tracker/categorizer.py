"""
categorizer.py — Merchant-pattern-based transaction categorizer.

Maps merchant name patterns to spending categories using a keyword ruleset.
Fast, offline, no LLM needed.

Categories:
    groceries, dining, transport, fuel, utilities, subscriptions,
    health, shopping, travel, entertainment, income, transfer, other
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any

# Category rule: pattern → category (checked case-insensitively)
_RULES: list[tuple[str, str]] = [
    # Income
    (r"\b(payroll|salary|direct.?dep|employer|wages?|freelance.?pay)\b", "income"),
    (r"\b(transfer.?in|deposit|refund|cashback|reimburs)\b",              "income"),

    # Groceries
    (r"\b(walmart|target|costco|kroger|whole.?foods|trader.?joe|aldi|publix|safeway|wegmans|lidl)\b", "groceries"),
    (r"\b(grocery|supermarket|food.?mart|super.?center|piggly)\b",         "groceries"),

    # Dining
    (r"\b(mcdonald|burger.?king|subway|pizza|starbucks|chipotle|dominos|wendys|taco.?bell)\b", "dining"),
    (r"\b(doordash|ubereats|grubhub|postmates|seamless|delivery)\b",       "dining"),
    (r"\b(restaurant|cafe|diner|bistro|grill|eatery|sushi|ramen|thai|bbq|bar.?&|pub)\b", "dining"),

    # Transport
    (r"\b(uber|lyft|taxi|cab|transit|metro|mta|bart|caltrain|amtrak|greyhound)\b", "transport"),
    (r"\b(parking|toll|ez.?pass|pikepass|fastrak)\b",                      "transport"),

    # Fuel
    (r"\b(shell|chevron|exxon|exxonmobil|bp.?gas|mobil|marathon|speedway|circle.?k|7.?eleven.?gas)\b", "fuel"),
    (r"\b(gas.?station|fuel|petrol)\b",                                    "fuel"),

    # Utilities
    (r"\b(electric|power.?company|utility|pge|con.?ed|duke.?energy|national.?grid)\b", "utilities"),
    (r"\b(internet|comcast|xfinity|at&t|verizon|spectrum|t-?mobile|sprint|charter)\b", "utilities"),
    (r"\b(water.?bill|gas.?bill|waste.?manage|sanitation)\b",              "utilities"),

    # Subscriptions
    (r"\b(netflix|hulu|disney|spotify|apple.?music|amazon.?prime|youtube.?premium)\b", "subscriptions"),
    (r"\b(subscription|monthly.?fee|annual.?fee|membership|patreon|substack)\b",       "subscriptions"),
    (r"\b(adobe|microsoft.?365|google.?one|dropbox|notion|slack)\b",       "subscriptions"),

    # Health
    (r"\b(pharmacy|cvs|walgreens|rite.?aid|health|medical|dental|vision|clinic|hospital|urgent.?care)\b", "health"),
    (r"\b(insurance|anthem|aetna|cigna|humana|unitedhealthcare|blue.?cross)\b", "health"),
    (r"\b(gym|fitness|planet.?fitness|anytime.?fitness|crossfit|yoga|pilates)\b", "health"),

    # Shopping
    (r"\b(amazon|ebay|etsy|shein|zara|h&m|gap|old.?navy|nordstrom|macys|best.?buy)\b", "shopping"),
    (r"\b(online.?store|e.?commerce|shop\.)\b",                            "shopping"),

    # Travel
    (r"\b(airline|delta|united|southwest|american.?airlines|jetblue|frontier|spirit)\b", "travel"),
    (r"\b(hotel|marriott|hilton|hyatt|airbnb|vrbo|expedia|hotels\.com)\b", "travel"),
    (r"\b(rental.?car|hertz|enterprise|avis|budget.?rent)\b",              "travel"),

    # Entertainment
    (r"\b(cinema|movie|amc|regal|theater|concert|ticketmaster|stubhub|eventbrite)\b", "entertainment"),
    (r"\b(steam|playstation|xbox|nintendo|twitch|audible|kindle)\b",       "entertainment"),

    # Transfer
    (r"\b(zelle|venmo|paypal|cashapp|wire.?transfer|transfer.?out|ach.?debit)\b", "transfer"),
]

_COMPILED: list[tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), cat) for pattern, cat in _RULES
]


def categorize(merchant: str, description: str = "") -> str:
    """Return the spending category for a merchant / description string."""
    combined = f"{merchant} {description}"
    for pattern, category in _COMPILED:
        if pattern.search(combined):
            return category
    return "other"


@dataclass
class Transaction:
    date:        str
    description: str
    amount:      float           # negative = debit (spending), positive = credit (income)
    category:    str = "other"
    merchant:    str = ""
    raw:         dict = field(default_factory=dict)


def parse_csv(csv_text: str) -> list[Transaction]:
    """Parse CSV text into a list of Transaction objects.

    Supports common bank CSV formats:
    - Date, Description, Amount
    - Date, Merchant, Debit, Credit
    - Date, Description, Debit Amount, Credit Amount
    - OFX-style numeric amounts (negative = debit)
    """
    import csv, io
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows:
        return []

    # Normalise header names to lowercase
    def h(row: dict, *candidates: str) -> str:
        for c in candidates:
            for k in row:
                if c.lower() in k.lower():
                    return row[k].strip()
        return ""

    transactions = []
    for row in rows:
        raw_date  = h(row, "date", "transaction date", "posted")
        raw_desc  = h(row, "description", "memo", "merchant", "name", "narration")
        raw_amt   = h(row, "amount", "transaction amount")
        raw_debit = h(row, "debit", "withdrawal", "debit amount")
        raw_credit= h(row, "credit", "deposit", "credit amount")

        # Parse amount
        amount = 0.0
        if raw_amt:
            amount = _parse_amount(raw_amt)
        elif raw_debit or raw_credit:
            debit  = _parse_amount(raw_debit)  if raw_debit  else 0.0
            credit = _parse_amount(raw_credit) if raw_credit else 0.0
            amount = credit - debit   # positive = income

        if not raw_date and not raw_desc:
            continue  # skip empty rows

        t = Transaction(
            date=raw_date,
            description=raw_desc,
            amount=amount,
            merchant=raw_desc[:40],
            raw=dict(row),
        )
        t.category = categorize(t.merchant, t.description)
        transactions.append(t)

    return transactions


def _parse_amount(s: str) -> float:
    """Parse amount string to float, handling $, commas, parentheses for negative."""
    s = s.strip().replace(",", "").replace("$", "").replace(" ", "")
    negative = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.lstrip("-(").rstrip(")")
    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return 0.0
