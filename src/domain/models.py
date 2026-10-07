"""
Domain dataclasses for policy, product, documents, loans, and disbursements.
Pure; no framework or IO imports.
Money fields stored as Decimal; age/tenure as int.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional


class DocumentStatus(str, Enum):
    MISSING = "MISSING"
    UPLOADED = "UPLOADED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ApplicationStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"


@dataclass(frozen=True)
class Document:
    doc_type: str
    filename: Optional[str] = None
    status: DocumentStatus = DocumentStatus.MISSING
    rejection_reason: Optional[str] = None


@dataclass(frozen=True)
class AuditEntry:
    actor_user_id: str
    action: str
    application_id: Optional[str] = None
    doc_type: Optional[str] = None
    reason: Optional[str] = None
    comment: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass(frozen=True)
class DisbursementRecord:
    disbursement_id: str
    application_id: str
    amount: Decimal
    funding_source: str = "STUB_FUNDING_ACCOUNT_01"
    reference: str = ""
    disbursed_at: str = ""
    released_by: str = ""
    status: str = "SUCCESS"


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
