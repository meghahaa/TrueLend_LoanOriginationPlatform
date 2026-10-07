"""
Repayment Service — orchestrates repayment posting, waterfall allocation, and delinquency recalculation.
Pure service layer; no framework imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from src.domain.dpd_bucket import calculate_dpd, resolve_delinquency_bucket
from src.domain.emi_calculator import RepaymentSchedule
from src.domain.repayment_allocation import RepaymentAllocation, allocate_repayment


@dataclass(frozen=True)
class RepaymentPostingResult:
    application_id: str
    amount_paid: Decimal
    paid_on: date
    outstanding_principal: Decimal
    total_remaining_due: Decimal
    dpd: int
    delinquency_bucket: str
    new_allocations: List[RepaymentAllocation]


class RepaymentService:
    def post_repayment(
        self,
        *,
        application_id: str,
        amount: Decimal,
        paid_on: date,
        as_of: Optional[date] = None,
        schedule: RepaymentSchedule,
        existing_allocations: List[RepaymentAllocation],
        bucket_thresholds: Optional[Dict[str, int]] = None,
    ) -> RepaymentPostingResult:
        """
        Post a customer repayment:
          - Validate amount > 0 and amount <= total remaining due
          - Allocate via waterfall (oldest unpaid first, interest before principal)
          - Update outstanding principal (P - sum(principal allocated))
          - Recalculate DPD and delinquency bucket
        """
        if amount <= Decimal("0.00"):
            raise ValueError("Repayment amount must be positive.")

        # Calculate already paid total
        total_already_paid = sum(
            (a.interest_allocated + a.principal_allocated for a in existing_allocations),
            Decimal("0.00"),
        )
        total_remaining_due = schedule.total_payable - total_already_paid

        if amount > total_remaining_due:
            raise ValueError(
                f"AMOUNT_EXCEEDS_OUTSTANDING: Payment {amount} exceeds remaining balance {total_remaining_due}"
            )

        new_allocations, _ = allocate_repayment(
            schedule_rows=schedule.rows,
            existing_allocations=existing_allocations,
            payment_amount=amount,
        )

        all_allocations = list(existing_allocations) + new_allocations
        total_principal_allocated = sum(
            (a.principal_allocated for a in all_allocations),
            Decimal("0.00"),
        )
        outstanding_principal = schedule.total_principal - total_principal_allocated

        # Determine oldest unpaid installment
        paid_per_inst: Dict[int, Decimal] = {}
        for a in all_allocations:
            paid_per_inst[a.installment_number] = (
                paid_per_inst.get(a.installment_number, Decimal("0.00"))
                + a.interest_allocated
                + a.principal_allocated
            )

        oldest_unpaid_due_date: Optional[date] = None
        for row in schedule.rows:
            paid_amount = paid_per_inst.get(row.installment_number, Decimal("0.00"))
            if paid_amount < row.emi_amount:
                oldest_unpaid_due_date = row.due_date
                break

        eval_date = as_of or paid_on
        dpd = calculate_dpd(eval_date, oldest_unpaid_due_date)
        bucket = resolve_delinquency_bucket(dpd, bucket_thresholds)

        new_total_remaining = total_remaining_due - amount
        if new_total_remaining == Decimal("0.00"):
            outstanding_principal = Decimal("0.00")
            dpd = 0
            bucket = "CURRENT"

        return RepaymentPostingResult(
            application_id=application_id,
            amount_paid=amount,
            paid_on=paid_on,
            outstanding_principal=outstanding_principal,
            total_remaining_due=new_total_remaining,
            dpd=dpd,
            delinquency_bucket=bucket,
            new_allocations=new_allocations,
        )

    def recalculate_delinquency(
        self,
        *,
        as_of: date,
        schedule: RepaymentSchedule,
        all_allocations: List[RepaymentAllocation],
        bucket_thresholds: Optional[Dict[str, int]] = None,
    ) -> tuple[int, str]:
        """Recalculate DPD and delinquency bucket as of a given date (e.g. for EOD job)."""
        paid_per_inst: Dict[int, Decimal] = {}
        for a in all_allocations:
            paid_per_inst[a.installment_number] = (
                paid_per_inst.get(a.installment_number, Decimal("0.00"))
                + a.interest_allocated
                + a.principal_allocated
            )

        oldest_unpaid_due_date: Optional[date] = None
        for row in schedule.rows:
            paid_amount = paid_per_inst.get(row.installment_number, Decimal("0.00"))
            if paid_amount < row.emi_amount:
                oldest_unpaid_due_date = row.due_date
                break

        dpd = calculate_dpd(as_of, oldest_unpaid_due_date)
        bucket = resolve_delinquency_bucket(dpd, bucket_thresholds)
        return dpd, bucket
