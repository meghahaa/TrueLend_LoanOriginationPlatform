"""
AC-07 — EMI Amortization Schedule Invariant Formula

RED test: asserts EMI calculation and repayment schedule generation
for P=300,000, r=12.50%, tenure=36 months matching exact reference values.
"""
from datetime import date
from decimal import Decimal
import pytest


@pytest.mark.ac("AC-07")
def test_ac07_reference_loan_300k_12_5pct_36m():
    """
    P=300000, 12.50%, 36m -> EMI 10036.09, last installment 10035.97,
    total payable 361299.12, interest 61299.12, sum(principal)=300000.00, final balance=0.00.
    """
    from src.domain.emi_calculator import generate_repayment_schedule

    schedule = generate_repayment_schedule(
        principal=Decimal("300000.00"),
        annual_rate_percent=Decimal("12.50"),
        tenure_months=36,
        start_date=date(2026, 1, 1),
    )

    assert len(schedule.rows) == 36
    assert schedule.emi_amount == Decimal("10036.09")
    assert schedule.rows[0].emi_amount == Decimal("10036.09")
    assert schedule.rows[-1].emi_amount == Decimal("10035.97")
    assert schedule.total_interest == Decimal("61299.12")
    assert schedule.total_payable == Decimal("361299.12")
    assert schedule.total_principal == Decimal("300000.00")
    assert schedule.rows[-1].remaining_balance == Decimal("0.00")
