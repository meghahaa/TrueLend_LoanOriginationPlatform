"""
Policy validator — validates a policy document dict.
Pure domain function; no IO, no framework.

Validation rules (from specs/product-catalog_spec.md):
  - min < max for age/amount/tenure
  - reject_score < approve_score
  - 300 ≤ scores ≤ 900
  - rate > 0
  - max_foir in (0, 1]
  - non-empty required_documents
  - bucket_thresholds strictly increasing
  - money fields parse as non-negative Decimal
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple


class PolicyValidationError(ValueError):
    """Raised when a policy document fails validation."""

    def __init__(self, messages: List[str]) -> None:
        self.messages = messages
        super().__init__("; ".join(messages))


def validate_policy_document(doc: dict) -> None:
    """
    Validate a policy document dict.
    Raises PolicyValidationError (with all collected messages) on failure.
    """
    errors: List[str] = []

    # ── bucket_thresholds ────────────────────────────────────────────────
    thresholds = doc.get("bucket_thresholds", {})
    _validate_bucket_thresholds(thresholds, errors)

    # ── products ─────────────────────────────────────────────────────────
    products = doc.get("products", {})
    if not products:
        errors.append("products: must contain at least one product")

    for code, p in products.items():
        prefix = f"products.{code}"
        _validate_product(prefix, p, errors)

    if errors:
        raise PolicyValidationError(errors)


# ──────────────────────────────────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────────────────────────────────

def _parse_decimal(value: str, field: str, errors: List[str]) -> Decimal | None:
    try:
        d = Decimal(str(value))
        if d < 0:
            errors.append(f"{field}: must be non-negative, got {value!r}")
            return None
        return d
    except InvalidOperation:
        errors.append(f"{field}: not a valid decimal, got {value!r}")
        return None


def _validate_product(prefix: str, p: dict, errors: List[str]) -> None:
    # Money fields
    min_income = _parse_decimal(p.get("min_monthly_income", "0"), f"{prefix}.min_monthly_income", errors)
    min_amount = _parse_decimal(p.get("min_amount", "0"), f"{prefix}.min_amount", errors)
    max_amount = _parse_decimal(p.get("max_amount", "0"), f"{prefix}.max_amount", errors)
    rate = _parse_decimal(p.get("annual_rate_percent", "0"), f"{prefix}.annual_rate_percent", errors)
    max_foir = _parse_decimal(p.get("max_foir", "0"), f"{prefix}.max_foir", errors)

    # rate > 0
    if rate is not None and rate <= 0:
        errors.append(f"{prefix}.annual_rate_percent: must be > 0")

    # max_foir in (0, 1]
    if max_foir is not None:
        if max_foir <= 0 or max_foir > 1:
            errors.append(f"{prefix}.max_foir: must be in (0, 1], got {max_foir}")

    # age ranges
    min_age = p.get("min_age")
    max_age = p.get("max_age")
    if min_age is not None and max_age is not None:
        if min_age >= max_age:
            errors.append(f"{prefix}: min_age ({min_age}) must be < max_age ({max_age})")

    # amount ranges
    if min_amount is not None and max_amount is not None:
        if min_amount >= max_amount:
            errors.append(f"{prefix}: min_amount must be < max_amount")

    # tenure ranges
    min_t = p.get("min_tenure_months")
    max_t = p.get("max_tenure_months")
    if min_t is not None and max_t is not None:
        if min_t >= max_t:
            errors.append(f"{prefix}: min_tenure_months ({min_t}) must be < max_tenure_months ({max_t})")

    # scores
    approve = p.get("approve_score")
    reject = p.get("reject_score")
    for score_name, score_val in [("approve_score", approve), ("reject_score", reject)]:
        if score_val is not None and not (300 <= score_val <= 900):
            errors.append(f"{prefix}.{score_name}: must be in [300, 900], got {score_val}")
    if approve is not None and reject is not None:
        if reject >= approve:
            errors.append(f"{prefix}: reject_score ({reject}) must be < approve_score ({approve})")

    # required_documents
    docs = p.get("required_documents", [])
    if not docs:
        errors.append(f"{prefix}.required_documents: must be non-empty")


def _validate_bucket_thresholds(thresholds: dict, errors: List[str]) -> None:
    if not thresholds:
        return
    prev_val = None
    prev_key = None
    for key, val in thresholds.items():
        if prev_val is not None and val <= prev_val:
            errors.append(
                f"bucket_thresholds: {key} ({val}) must be > {prev_key} ({prev_val})"
            )
        prev_val = val
        prev_key = key
