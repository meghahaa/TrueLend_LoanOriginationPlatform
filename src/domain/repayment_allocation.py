"""
Repayment Allocation Waterfall — pure domain rules.
No IO, no float, no framework imports.
Allocates payment: oldest unpaid installment first, interest before principal.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Tuple

from src.domain.emi_calculator import ScheduleRow


@dataclass(frozen=True)
class RepaymentAllocation:
    installment_number: int
    interest_allocated: Decimal
    principal_allocated: Decimal


def allocate_repayment(
    schedule_rows: List[ScheduleRow],
    existing_allocations: List[RepaymentAllocation],
    payment_amount: Decimal,
) -> Tuple[List[RepaymentAllocation], Decimal]:
    """
    Waterfall allocation across schedule rows.
    Returns:
      - list of new RepaymentAllocation entries for this payment
      - remaining unallocated payment amount (if any)
    """
    if payment_amount < Decimal("0.00"):
        raise ValueError("Payment amount cannot be negative")

    # Aggregate existing paid amounts per installment
    paid_interest_by_inst: Dict[int, Decimal] = {}
    paid_principal_by_inst: Dict[int, Decimal] = {}

    for alloc in existing_allocations:
        paid_interest_by_inst[alloc.installment_number] = (
            paid_interest_by_inst.get(alloc.installment_number, Decimal("0.00")) + alloc.interest_allocated
        )
        paid_principal_by_inst[alloc.installment_number] = (
            paid_principal_by_inst.get(alloc.installment_number, Decimal("0.00")) + alloc.principal_allocated
        )

    new_allocations: List[RepaymentAllocation] = []
    remaining_payment = payment_amount

    for row in schedule_rows:
        if remaining_payment <= Decimal("0.00"):
            break

        inst_no = row.installment_number
        already_paid_int = paid_interest_by_inst.get(inst_no, Decimal("0.00"))
        already_paid_pr = paid_principal_by_inst.get(inst_no, Decimal("0.00"))

        interest_due = row.interest_component - already_paid_int
        principal_due = row.principal_component - already_paid_pr

        if interest_due <= Decimal("0.00") and principal_due <= Decimal("0.00"):
            continue

        # 1. Allocate interest first
        alloc_interest = Decimal("0.00")
        if interest_due > Decimal("0.00"):
            alloc_interest = min(remaining_payment, interest_due)
            remaining_payment -= alloc_interest

        # 2. Allocate principal next
        alloc_principal = Decimal("0.00")
        if principal_due > Decimal("0.00") and remaining_payment > Decimal("0.00"):
            alloc_principal = min(remaining_payment, principal_due)
            remaining_payment -= alloc_principal

        if alloc_interest > Decimal("0.00") or alloc_principal > Decimal("0.00"):
            new_allocations.append(
                RepaymentAllocation(
                    installment_number=inst_no,
                    interest_allocated=alloc_interest,
                    principal_allocated=alloc_principal,
                )
            )

    return new_allocations, remaining_payment
