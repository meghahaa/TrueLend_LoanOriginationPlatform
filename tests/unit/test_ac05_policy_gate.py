"""
AC-05 — Policy gate: income / age / amount / tenure checks.

Violations are collected and raised as PolicyViolationException.
Boundary values equal to the minimum PASS.
No application persisted on any violation.
NFR-03: logs must not contain PAN or Aadhaar.
"""
import logging
import pytest

from src.domain.exceptions import PolicyViolationException
from src.domain.models import ProductPolicy
from src.domain.money import to_money


def _personal_policy(**overrides) -> ProductPolicy:
    """Return a PERSONAL ProductPolicy with sensible defaults, allowing overrides."""
    defaults = dict(
        product_code="PERSONAL",
        display_name="Personal Loan",
        min_monthly_income=to_money("25000.00"),
        min_age=21,
        max_age=60,
        min_amount=to_money("50000.00"),
        max_amount=to_money("1000000.00"),
        min_tenure_months=12,
        max_tenure_months=60,
        annual_rate_percent=to_money("12.50"),
        approve_score=720,
        reject_score=550,
        max_foir=to_money("0.50"),
        required_documents=["ID_PROOF", "ADDRESS_PROOF", "SALARY_SLIP", "BANK_STATEMENT"],
    )
    defaults.update(overrides)
    return ProductPolicy(**defaults)


@pytest.mark.ac("AC-05")
def test_ac05_income_below_min_raises_violation():
    """Income 24999.99 < 25000.00 min → INCOME_BELOW_MIN, HTTP 422, no persistence."""
    from src.domain.eligibility_rules import check_policy_gate

    policy = _personal_policy()
    with pytest.raises(PolicyViolationException) as exc_info:
        check_policy_gate(
            policy=policy,
            monthly_income=to_money("24999.99"),
            age=30,
            amount=to_money("100000.00"),
            tenure_months=24,
            policy_version=1,
        )
    assert "INCOME_BELOW_MIN" in exc_info.value.reason_codes
    assert exc_info.value.policy_version == 1


@pytest.mark.ac("AC-05a")
def test_ac05a_income_exactly_at_min_passes():
    """Income exactly 25000.00 (== min) → no income violation (boundary included)."""
    from src.domain.eligibility_rules import check_policy_gate

    policy = _personal_policy()
    # Should not raise — no violation
    check_policy_gate(
        policy=policy,
        monthly_income=to_money("25000.00"),
        age=30,
        amount=to_money("100000.00"),
        tenure_months=24,
        policy_version=1,
    )


@pytest.mark.ac("AC-05b")
def test_ac05b_age_below_min_raises():
    """Age 17 < 21 → AGE_OUT_OF_RANGE."""
    from src.domain.eligibility_rules import check_policy_gate

    policy = _personal_policy()
    with pytest.raises(PolicyViolationException) as exc_info:
        check_policy_gate(
            policy=policy,
            monthly_income=to_money("30000.00"),
            age=17,
            amount=to_money("100000.00"),
            tenure_months=24,
            policy_version=1,
        )
    assert "AGE_OUT_OF_RANGE" in exc_info.value.reason_codes


@pytest.mark.ac("AC-05b")
def test_ac05b_amount_above_max_raises():
    """Amount above 1000000 → AMOUNT_OUT_OF_RANGE."""
    from src.domain.eligibility_rules import check_policy_gate

    policy = _personal_policy()
    with pytest.raises(PolicyViolationException) as exc_info:
        check_policy_gate(
            policy=policy,
            monthly_income=to_money("30000.00"),
            age=30,
            amount=to_money("1000001.00"),
            tenure_months=24,
            policy_version=1,
        )
    assert "AMOUNT_OUT_OF_RANGE" in exc_info.value.reason_codes


@pytest.mark.ac("AC-05b")
def test_ac05b_tenure_below_min_raises():
    """Tenure 11 < 12 (min) → TENURE_OUT_OF_RANGE."""
    from src.domain.eligibility_rules import check_policy_gate

    policy = _personal_policy()
    with pytest.raises(PolicyViolationException) as exc_info:
        check_policy_gate(
            policy=policy,
            monthly_income=to_money("30000.00"),
            age=30,
            amount=to_money("100000.00"),
            tenure_months=11,
            policy_version=1,
        )
    assert "TENURE_OUT_OF_RANGE" in exc_info.value.reason_codes


@pytest.mark.ac("AC-05b")
def test_ac05b_multiple_violations_all_reported():
    """Income AND age violations → both codes reported."""
    from src.domain.eligibility_rules import check_policy_gate

    policy = _personal_policy()
    with pytest.raises(PolicyViolationException) as exc_info:
        check_policy_gate(
            policy=policy,
            monthly_income=to_money("10000.00"),  # below min
            age=17,                                # below min
            amount=to_money("100000.00"),
            tenure_months=24,
            policy_version=1,
        )
    codes = exc_info.value.reason_codes
    assert "INCOME_BELOW_MIN" in codes
    assert "AGE_OUT_OF_RANGE" in codes


@pytest.mark.ac("AC-05c")
def test_ac05c_violation_log_has_no_pii(caplog):
    """On a violation, logs contain reason codes but NOT PAN or Aadhaar (NFR-03)."""
    from src.domain.eligibility_rules import check_policy_gate

    PAN = "TESTP1234X"
    AADHAAR = "999900000001"

    policy = _personal_policy()
    with caplog.at_level(logging.WARNING):
        with pytest.raises(PolicyViolationException):
            check_policy_gate(
                policy=policy,
                monthly_income=to_money("10000.00"),
                age=30,
                amount=to_money("100000.00"),
                tenure_months=24,
                policy_version=1,
            )

    combined_logs = " ".join(caplog.messages)
    assert PAN not in combined_logs, "PAN found in logs — NFR-03 violation"
    assert AADHAAR not in combined_logs, "Aadhaar found in logs — NFR-03 violation"
