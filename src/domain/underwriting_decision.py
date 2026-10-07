"""
Automated underwriting decision — pure domain function.
No IO, no framework imports, no float.

Rules (specs/underwriting_spec.md §AC-04):
  FOIR = EMI(amount, policy_rate, tenure) / monthly_income  (Decimal, 4 dp)
  1. has_default → AUTO_REJECT + PRIOR_DEFAULT (+ SCORE_BELOW_REJECT if also applies)
  2. score < reject_score → AUTO_REJECT + SCORE_BELOW_REJECT
  3. score >= approve_score AND FOIR <= max_foir → AUTO_APPROVE + SCORE_ABOVE_APPROVE
  4. otherwise → MANUAL_REVIEW (SCORE_IN_REVIEW_BAND if in band; FOIR_EXCEEDED if FOIR > max_foir)

Status mapping:
  AUTO_APPROVE  → APPROVED
  AUTO_REJECT   → REJECTED
  MANUAL_REVIEW → MANUAL_REVIEW
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from src.domain.emi_calculator import calculate_emi
from src.domain.models import ProductPolicy


@dataclass(frozen=True)
class UnderwritingResult:
    decision: str          # AUTO_APPROVE | AUTO_REJECT | MANUAL_REVIEW
    status: str            # APPROVED | REJECTED | MANUAL_REVIEW
    reason_codes: List[str]
    foir: Decimal


def make_underwriting_decision(
    *,
    policy: ProductPolicy,
    score: int,
    monthly_income: Decimal,
    amount: Decimal,
    tenure_months: int,
    has_default: bool,
) -> UnderwritingResult:
    """
    Apply automated underwriting rules and return a decision.
    All comparisons use Decimal; FOIR rounded to 4 dp with ROUND_HALF_UP.
    """
    emi = calculate_emi(amount, policy.annual_rate_percent, tenure_months)
    foir = (emi / monthly_income).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    reason_codes: List[str] = []

    # Rule 1: prior default → AUTO_REJECT
    if has_default:
        reason_codes.append("PRIOR_DEFAULT")
        if score < policy.reject_score:
            reason_codes.append("SCORE_BELOW_REJECT")
        return UnderwritingResult(
            decision="AUTO_REJECT",
            status="REJECTED",
            reason_codes=reason_codes,
            foir=foir,
        )

    # Rule 2: score below reject threshold → AUTO_REJECT
    if score < policy.reject_score:
        reason_codes.append("SCORE_BELOW_REJECT")
        return UnderwritingResult(
            decision="AUTO_REJECT",
            status="REJECTED",
            reason_codes=reason_codes,
            foir=foir,
        )

    # Rule 3: score >= approve_score AND FOIR <= max_foir → AUTO_APPROVE
    if score >= policy.approve_score and foir <= policy.max_foir:
        reason_codes.append("SCORE_ABOVE_APPROVE")
        return UnderwritingResult(
            decision="AUTO_APPROVE",
            status="APPROVED",
            reason_codes=reason_codes,
            foir=foir,
        )

    # Rule 4: MANUAL_REVIEW — collect all sub-reasons
    if policy.reject_score <= score < policy.approve_score:
        reason_codes.append("SCORE_IN_REVIEW_BAND")
    if foir > policy.max_foir:
        reason_codes.append("FOIR_EXCEEDED")

    return UnderwritingResult(
        decision="MANUAL_REVIEW",
        status="MANUAL_REVIEW",
        reason_codes=reason_codes,
        foir=foir,
    )
