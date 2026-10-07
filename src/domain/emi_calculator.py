"""
EMI and Amortization Schedule Calculator — pure domain rules.
No float, no framework/IO imports.
Uses Decimal throughout with ROUND_HALF_UP rounding to 2 decimal places.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import List

# Ensure Decimal context precision is high
getcontext().prec = 35


@dataclass(frozen=True)
class ScheduleRow:
    installment_number: int
    due_date: date
    opening_balance: Decimal
    principal_component: Decimal
    interest_component: Decimal
    emi_amount: Decimal
    remaining_balance: Decimal


@dataclass(frozen=True)
class RepaymentSchedule:
    emi_amount: Decimal
    total_principal: Decimal
    total_interest: Decimal
    total_payable: Decimal
    rows: List[ScheduleRow]


def _quantize_money(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _add_months_clamped(start_date: date, months: int) -> date:
    """Calculate due date n months from start_date, clamped to the end of the month if necessary."""
    total_month = start_date.month - 1 + months
    year = start_date.year + total_month // 12
    month = total_month % 12 + 1
    max_days = calendar.monthrange(year, month)[1]
    day = min(start_date.day, max_days)
    return date(year, month, day)


def calculate_emi(
    principal: Decimal,
    annual_rate_percent: Decimal,
    tenure_months: int,
) -> Decimal:
    """
    Calculate monthly EMI using standard formula:
    r = annual_rate_percent / 12 / 100
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    if r == 0: EMI = P / n
    Rounded to 2 decimal places with ROUND_HALF_UP.
    """
    if tenure_months <= 0:
        raise ValueError("tenure_months must be positive")

    if annual_rate_percent == Decimal("0"):
        return _quantize_money(principal / Decimal(tenure_months))

    r = annual_rate_percent / Decimal("1200")
    one_plus_r = Decimal("1") + r
    pow_factor = one_plus_r ** Decimal(tenure_months)

    numerator = principal * r * pow_factor
    denominator = pow_factor - Decimal("1")
    raw_emi = numerator / denominator
    return _quantize_money(raw_emi)


def generate_repayment_schedule(
    principal: Decimal,
    annual_rate_percent: Decimal,
    tenure_months: int,
    start_date: date,
) -> RepaymentSchedule:
    """
    Generate the full amortization schedule.
    Invariants strictly preserved:
      - sum(principal_components) == principal
      - final remaining_balance == 0.00
      - sum(principal_components) + sum(interest_components) == total_payable
    """
    if tenure_months <= 0:
        raise ValueError("tenure_months must be positive")

    emi = calculate_emi(principal, annual_rate_percent, tenure_months)
    monthly_rate = annual_rate_percent / Decimal("1200") if annual_rate_percent > 0 else Decimal("0")

    rows: List[ScheduleRow] = []
    opening_balance = principal
    sum_interest = Decimal("0.00")
    sum_principal = Decimal("0.00")

    for k in range(1, tenure_months + 1):
        due_date = _add_months_clamped(start_date, k)
        interest_k = _quantize_money(opening_balance * monthly_rate)

        if k == tenure_months:
            # Last installment absorbs any fractional-cent rounding
            principal_k = opening_balance
            emi_k = principal_k + interest_k
            closing_balance = Decimal("0.00")
        else:
            principal_k = emi - interest_k
            emi_k = emi
            closing_balance = opening_balance - principal_k

        rows.append(
            ScheduleRow(
                installment_number=k,
                due_date=due_date,
                opening_balance=opening_balance,
                principal_component=principal_k,
                interest_component=interest_k,
                emi_amount=emi_k,
                remaining_balance=closing_balance,
            )
        )

        sum_interest += interest_k
        sum_principal += principal_k
        opening_balance = closing_balance

    total_payable = sum_principal + sum_interest

    return RepaymentSchedule(
        emi_amount=emi,
        total_principal=sum_principal,
        total_interest=sum_interest,
        total_payable=total_payable,
        rows=rows,
    )
