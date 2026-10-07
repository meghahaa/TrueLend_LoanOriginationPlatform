"""
Eligibility rules (policy gate) — pure domain function.
Collects ALL violations before raising, never short-circuits.
No IO, no framework imports, no float.

Reason codes (AC-05):
  INCOME_BELOW_MIN, AGE_OUT_OF_RANGE, AMOUNT_OUT_OF_RANGE, TENURE_OUT_OF_RANGE
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import List

from src.domain.exceptions import PolicyViolationException
from src.domain.models import ProductPolicy

_log = logging.getLogger(__name__)


def check_policy_gate(
    *,
    policy: ProductPolicy,
    monthly_income: Decimal,
    age: int,
    amount: Decimal,
    tenure_months: int,
    policy_version: int,
) -> None:
    """
    Validate applicant data against policy thresholds.
    Raises PolicyViolationException with ALL collected codes on any violation.
    Boundary values equal to the minimum PASS (≥ min is OK).
    Logs only codes and policy_version — never PAN/Aadhaar (NFR-03).
    """
    violations: List[str] = []

    if monthly_income < policy.min_monthly_income:
        violations.append("INCOME_BELOW_MIN")

    if not (policy.min_age <= age <= policy.max_age):
        violations.append("AGE_OUT_OF_RANGE")

    if not (policy.min_amount <= amount <= policy.max_amount):
        violations.append("AMOUNT_OUT_OF_RANGE")

    if not (policy.min_tenure_months <= tenure_months <= policy.max_tenure_months):
        violations.append("TENURE_OUT_OF_RANGE")

    if violations:
        _log.warning(
            "Policy gate failed: codes=%s policy_version=%s",
            violations,
            policy_version,
        )
        raise PolicyViolationException(
            reason_codes=violations,
            policy_version=policy_version,
        )
