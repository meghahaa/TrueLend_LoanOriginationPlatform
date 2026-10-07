"""
AC-09 — Repayment Posting & Delinquency Bucket Recalculation

RED test: asserts that posting a repayment allocates payment oldest-first,
reduces outstanding principal, and recalculates DPD / delinquency bucket.
"""
from datetime import date
from decimal import Decimal
import pytest

from src.domain.emi_calculator import generate_repayment_schedule


@pytest.mark.ac("AC-09")
def test_ac09_repayment_posting_one_emi():
    """Posting exactly one EMI allocates interest then principal for the first installment."""
    from src.services.repayment_service import RepaymentService

    schedule = generate_repayment_schedule(
        principal=Decimal("300000.00"),
        annual_rate_percent=Decimal("12.50"),
        tenure_months=36,
        start_date=date(2026, 1, 1),
    )
    # Month 1 installment: emi=10036.09, interest=3125.00, principal=6911.09
    service = RepaymentService()
    result = service.post_repayment(
        application_id="app-300",
        amount=Decimal("10036.09"),
        paid_on=date(2026, 2, 1),
        as_of=date(2026, 2, 1),
        schedule=schedule,
        existing_allocations=[],
    )

    assert result.outstanding_principal == Decimal("300000.00") - Decimal("6911.09")
    assert result.dpd == 0
    assert result.delinquency_bucket == "CURRENT"
    assert len(result.new_allocations) == 1
    assert result.new_allocations[0].principal_allocated == Decimal("6911.09")
    assert result.new_allocations[0].interest_allocated == Decimal("3125.00")
