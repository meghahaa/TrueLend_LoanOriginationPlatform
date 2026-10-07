"""
Domain dataclasses for policy and product. Pure; no framework or IO imports.
Money fields stored as Decimal; age/tenure as int.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List


@dataclass(frozen=True)
class ProductPolicy:
    """Thresholds and requirements for one loan product."""

    product_code: str          # e.g. "PERSONAL"
    display_name: str
    min_monthly_income: Decimal
    min_age: int
    max_age: int
    min_amount: Decimal
    max_amount: Decimal
    min_tenure_months: int
    max_tenure_months: int
    annual_rate_percent: Decimal
    approve_score: int
    reject_score: int
    max_foir: Decimal
    required_documents: List[str]


@dataclass(frozen=True)
class LoanPolicy:
    """The active (highest version) policy document."""

    version: int
    effective_from: str         # ISO-8601 date string
    created_by: str
    change_note: str
    products: Dict[str, ProductPolicy]  # keyed by product_code
    bucket_thresholds: Dict[str, int]
