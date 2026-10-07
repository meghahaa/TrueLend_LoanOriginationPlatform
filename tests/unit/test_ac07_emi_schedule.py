"""
AC-07 — EMI Amortization Schedule Invariant Formula

Tests covering:
- AC-07: Reference loan P=300,000, r=12.50%, tenure=36m
- AC-07a: Reference loans (12m, 0%, 84m)
- AC-07b: Invariant assertions across a grid of loans
- AC-07c: Zero interest rate calculations
- AC-07e: Month-end clamping (e.g., Jan 31 -> Feb 28)
- NFR-01: AST check for no float in money/EMI modules
"""
import ast
from datetime import date
from decimal import Decimal
import pytest

from src.domain.emi_calculator import calculate_emi, generate_repayment_schedule


@pytest.mark.ac("AC-07")
def test_ac07_reference_loan_300k_12_5pct_36m():
    """
    P=300000, 12.50%, 36m -> EMI 10036.09, last installment 10035.97,
    total payable 361299.12, interest 61299.12, sum(principal)=300000.00, final balance=0.00.
    """
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


@pytest.mark.ac("AC-07a")
def test_ac07a_reference_loan_120k_12pct_12m():
    """P=120000, 12 %, 12 m -> EMI 10661.85, last 10661.91, total 127942.26."""
    schedule = generate_repayment_schedule(
        principal=Decimal("120000.00"),
        annual_rate_percent=Decimal("12.00"),
        tenure_months=12,
        start_date=date(2026, 1, 1),
    )
    assert schedule.emi_amount == Decimal("10661.85")
    assert schedule.rows[-1].emi_amount == Decimal("10661.91")
    assert schedule.total_payable == Decimal("127942.26")
    assert schedule.total_principal == Decimal("120000.00")


@pytest.mark.ac("AC-07a")
def test_ac07a_reference_loan_100k_0pct_10m():
    """P=100000, 0 %, 10 m -> EMI 10000.00, total 100000.00."""
    schedule = generate_repayment_schedule(
        principal=Decimal("100000.00"),
        annual_rate_percent=Decimal("0.00"),
        tenure_months=10,
        start_date=date(2026, 1, 1),
    )
    assert schedule.emi_amount == Decimal("10000.00")
    assert schedule.total_interest == Decimal("0.00")
    assert schedule.total_payable == Decimal("100000.00")
    assert schedule.total_principal == Decimal("100000.00")


@pytest.mark.ac("AC-07a")
def test_ac07a_reference_loan_1m_9_5pct_84m():
    """P=1000000, 9.5 %, 84 m -> EMI 16343.98, total 1372894.56."""
    schedule = generate_repayment_schedule(
        principal=Decimal("1000000.00"),
        annual_rate_percent=Decimal("9.50"),
        tenure_months=84,
        start_date=date(2026, 1, 1),
    )
    assert schedule.emi_amount == Decimal("16343.98")
    assert schedule.total_payable == Decimal("1372894.56")
    assert schedule.total_principal == Decimal("1000000.00")
    assert schedule.rows[-1].remaining_balance == Decimal("0.00")


@pytest.mark.ac("AC-07b")
@pytest.mark.parametrize("principal,rate,tenure", [
    (Decimal("50000.00"), Decimal("8.50"), 12),
    (Decimal("150000.00"), Decimal("10.00"), 24),
    (Decimal("500000.00"), Decimal("14.50"), 60),
    (Decimal("2500000.00"), Decimal("9.50"), 84),
    (Decimal("4000000.00"), Decimal("11.00"), 120),
    (Decimal("75000.00"), Decimal("0.00"), 15),
])
def test_ac07b_invariants_hold_over_grid(principal, rate, tenure):
    """Invariants: sum(principal) == P, final balance == 0, total_payable == sum(principal) + sum(interest)."""
    schedule = generate_repayment_schedule(
        principal=principal,
        annual_rate_percent=rate,
        tenure_months=tenure,
        start_date=date(2026, 3, 15),
    )
    assert len(schedule.rows) == tenure
    assert schedule.total_principal == principal
    assert schedule.rows[-1].remaining_balance == Decimal("0.00")
    assert schedule.total_payable == schedule.total_principal + schedule.total_interest

    sum_p = sum((r.principal_component for r in schedule.rows), Decimal("0.00"))
    sum_i = sum((r.interest_component for r in schedule.rows), Decimal("0.00"))
    sum_emi = sum((r.emi_amount for r in schedule.rows), Decimal("0.00"))

    assert sum_p == principal
    assert sum_p + sum_i == schedule.total_payable
    assert sum_emi == schedule.total_payable

    for row in schedule.rows:
        assert row.principal_component >= Decimal("0.00")
        assert row.interest_component >= Decimal("0.00")
        assert row.emi_amount > Decimal("0.00")


@pytest.mark.ac("AC-07c")
def test_ac07c_zero_interest_rate():
    """Given 0% rate, EMI = P/n and total interest 0.00."""
    p = Decimal("60000.00")
    n = 12
    schedule = generate_repayment_schedule(
        principal=p,
        annual_rate_percent=Decimal("0.00"),
        tenure_months=n,
        start_date=date(2026, 1, 1),
    )
    assert schedule.emi_amount == Decimal("5000.00")
    assert schedule.total_interest == Decimal("0.00")
    assert schedule.total_payable == p


@pytest.mark.ac("AC-07e")
def test_ac07e_month_end_clamping_jan31_to_feb():
    """Given approval on Jan 31, first due date is Feb 28 (or 29 on leap year)."""
    schedule = generate_repayment_schedule(
        principal=Decimal("100000.00"),
        annual_rate_percent=Decimal("10.00"),
        tenure_months=3,
        start_date=date(2026, 1, 31),
    )
    # 2026 is non-leap year -> Feb has 28 days
    assert schedule.rows[0].due_date == date(2026, 2, 28)
    assert schedule.rows[1].due_date == date(2026, 3, 31)
    assert schedule.rows[2].due_date == date(2026, 4, 30)


@pytest.mark.ac("NFR-01")
def test_nfr01_no_float_in_emi_calculator():
    """AST check: ensure no float literals or float casts exist in emi_calculator.py."""
    with open("src/domain/emi_calculator.py", "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            pytest.fail(f"Found float constant {node.value} in emi_calculator.py (NFR-01 violation)")
        if isinstance(node, ast.Name) and node.id == "float":
            pytest.fail("Found use of 'float' identifier in emi_calculator.py (NFR-01 violation)")
