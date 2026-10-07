"""
AC-09 — Repayment Posting & Delinquency Bucket Recalculation

Unit tests covering:
- AC-09: Exact one EMI payment reduces outstanding principal by installment principal
- AC-09a: Partial payment smaller than interest portion allocates only interest; principal unchanged
- AC-09b: Multi-installment waterfall payment allocates oldest-first, interest before principal
- AC-09c: DPD bucket boundaries (29 -> CURRENT, 30 -> DPD-30, 75 -> DPD-60, 90 -> DPD-90, 200 -> NPA)
- AC-09d: Catching up overdue payments returns bucket to CURRENT
- AC-09e: Invalid payment amounts (<= 0, > remaining due) raise errors
- AC-09f: Idempotent EOD recalculation
"""
from datetime import date, timedelta
from decimal import Decimal
import pytest

from src.domain.dpd_bucket import calculate_dpd, resolve_delinquency_bucket
from src.domain.emi_calculator import generate_repayment_schedule
from src.domain.repayment_allocation import RepaymentAllocation
from src.services.repayment_service import RepaymentService


@pytest.fixture
def sample_schedule():
    # P=300000, 12.5%, 36m -> EMI 10036.09 (Month 1: interest 3125.00, principal 6911.09)
    # Month 2: opening=293088.91, interest=3053.01, principal=6983.08
    return generate_repayment_schedule(
        principal=Decimal("300000.00"),
        annual_rate_percent=Decimal("12.50"),
        tenure_months=36,
        start_date=date(2026, 1, 1),
    )


@pytest.mark.ac("AC-09")
def test_ac09_repayment_posting_one_emi(sample_schedule):
    """Posting exactly one EMI reduces principal by month 1 principal component."""
    service = RepaymentService()
    result = service.post_repayment(
        application_id="app-300",
        amount=Decimal("10036.09"),
        paid_on=date(2026, 2, 1),
        as_of=date(2026, 2, 1),
        schedule=sample_schedule,
        existing_allocations=[],
    )

    assert result.outstanding_principal == Decimal("300000.00") - Decimal("6911.09")
    assert result.dpd == 0
    assert result.delinquency_bucket == "CURRENT"
    assert len(result.new_allocations) == 1
    assert result.new_allocations[0].principal_allocated == Decimal("6911.09")
    assert result.new_allocations[0].interest_allocated == Decimal("3125.00")


@pytest.mark.ac("AC-09a")
def test_ac09a_partial_payment_less_than_interest(sample_schedule):
    """Partial payment smaller than interest component allocates only interest; principal unchanged."""
    service = RepaymentService()
    result = service.post_repayment(
        application_id="app-300",
        amount=Decimal("2000.00"),  # Month 1 interest is 3125.00
        paid_on=date(2026, 2, 1),
        as_of=date(2026, 2, 1),
        schedule=sample_schedule,
        existing_allocations=[],
    )

    assert result.outstanding_principal == Decimal("300000.00")
    assert len(result.new_allocations) == 1
    assert result.new_allocations[0].interest_allocated == Decimal("2000.00")
    assert result.new_allocations[0].principal_allocated == Decimal("0.00")


@pytest.mark.ac("AC-09b")
def test_ac09b_waterfall_covers_two_installments_and_part_of_third(sample_schedule):
    """Payment covering 2 full installments + part of 3rd allocates oldest-first, interest before principal."""
    # Inst 1: int 3125.00, princ 6911.09 (total 10036.09)
    # Inst 2: int 3053.01, princ 6983.08 (total 10036.09)
    # Inst 3: interest component is ~2980.19, principal ~7055.90
    # Let's pay 10036.09 + 10036.09 + 4000.00 = 24072.18
    service = RepaymentService()
    result = service.post_repayment(
        application_id="app-300",
        amount=Decimal("24072.18"),
        paid_on=date(2026, 4, 1),
        as_of=date(2026, 4, 1),
        schedule=sample_schedule,
        existing_allocations=[],
    )

    assert len(result.new_allocations) == 3
    # Inst 1 fully paid
    assert result.new_allocations[0].interest_allocated == Decimal("3125.00")
    assert result.new_allocations[0].principal_allocated == Decimal("6911.09")
    # Inst 2 fully paid
    assert result.new_allocations[1].interest_allocated == Decimal("3053.01")
    assert result.new_allocations[1].principal_allocated == Decimal("6983.08")
    # Inst 3 partial payment: interest first (interest is ~2980.19), remaining to principal
    inst3_int = sample_schedule.rows[2].interest_component
    assert result.new_allocations[2].interest_allocated == inst3_int
    assert result.new_allocations[2].principal_allocated == Decimal("4000.00") - inst3_int


@pytest.mark.ac("AC-09c")
@pytest.mark.parametrize("overdue_days,expected_bucket", [
    (0, "CURRENT"),
    (29, "CURRENT"),
    (30, "DPD-30"),
    (59, "DPD-30"),
    (60, "DPD-60"),
    (75, "DPD-60"),
    (89, "DPD-60"),
    (90, "DPD-90"),
    (179, "DPD-90"),
    (200, "NPA"),
])
def test_ac09c_dpd_bucket_boundaries(overdue_days, expected_bucket):
    """Boundary tests for delinquency bucket thresholds."""
    due = date(2026, 2, 1)
    as_of = due + timedelta(days=overdue_days)
    dpd = calculate_dpd(as_of, due)
    assert dpd == overdue_days
    bucket = resolve_delinquency_bucket(dpd)
    assert bucket == expected_bucket


@pytest.mark.ac("AC-09d")
def test_ac09d_paying_overdue_brings_bucket_back_to_current(sample_schedule):
    """Overdue loan (DPD-60) returns to CURRENT once overdue installment is paid."""
    service = RepaymentService()
    # As of April 15 (due date Feb 1 was 73 days ago -> DPD-60)
    # Customer pays Month 1, Month 2, and Month 3 (due April 1)
    full_pay = Decimal("10036.09") * 3
    result = service.post_repayment(
        application_id="app-300",
        amount=full_pay,
        paid_on=date(2026, 4, 15),
        as_of=date(2026, 4, 15),
        schedule=sample_schedule,
        existing_allocations=[],
    )
    # Since Months 1, 2, 3 are fully paid, next due date is May 1 (not overdue as of Apr 15)
    assert result.dpd == 0
    assert result.delinquency_bucket == "CURRENT"


@pytest.mark.ac("AC-09e")
def test_ac09e_zero_or_negative_amount_raises_error(sample_schedule):
    """Zero or negative repayment amount raises ValueError."""
    service = RepaymentService()
    with pytest.raises(ValueError, match="positive"):
        service.post_repayment(
            application_id="app-300",
            amount=Decimal("0.00"),
            paid_on=date(2026, 2, 1),
            schedule=sample_schedule,
            existing_allocations=[],
        )


@pytest.mark.ac("AC-09e")
def test_ac09e_amount_exceeding_remaining_due_raises_error(sample_schedule):
    """Amount exceeding total remaining due raises ValueError."""
    service = RepaymentService()
    excess = sample_schedule.total_payable + Decimal("100.00")
    with pytest.raises(ValueError, match="AMOUNT_EXCEEDS_OUTSTANDING"):
        service.post_repayment(
            application_id="app-300",
            amount=excess,
            paid_on=date(2026, 2, 1),
            schedule=sample_schedule,
            existing_allocations=[],
        )


@pytest.mark.ac("AC-09f")
def test_ac09f_eod_recalculation_is_idempotent(sample_schedule):
    """EOD recalculation on the same date produces the exact same DPD and bucket."""
    service = RepaymentService()
    as_of = date(2026, 4, 15)
    dpd1, bucket1 = service.recalculate_delinquency(
        as_of=as_of,
        schedule=sample_schedule,
        all_allocations=[],
    )
    dpd2, bucket2 = service.recalculate_delinquency(
        as_of=as_of,
        schedule=sample_schedule,
        all_allocations=[],
    )
    assert dpd1 == dpd2 == 73
    assert bucket1 == bucket2 == "DPD-60"
