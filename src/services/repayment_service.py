"""
Repayment Service — orchestrates repayment posting, waterfall allocation, and delinquency recalculation.
Pure service layer; receives repos and Actor by dependency injection.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.domain.dpd_bucket import calculate_dpd, resolve_delinquency_bucket
from src.domain.emi_calculator import RepaymentSchedule
from src.domain.exceptions import InvalidApplicationStateException
from src.domain.models import Actor
from src.domain.repayment_allocation import RepaymentAllocation, allocate_repayment
from src.repositories.application_repository import ApplicationRepository
from src.repositories.policy_repository import PolicyRepository


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
    def __init__(
        self,
        app_repo: Optional[ApplicationRepository] = None,
        policy_repo: Optional[PolicyRepository] = None,
    ) -> None:
        self._app_repo = app_repo
        self._policy_repo = policy_repo

    def get_schedule_for_actor(
        self,
        actor: Actor,
        application_id: str,
    ) -> Tuple[RepaymentSchedule, Dict[str, Any]]:
        """Retrieve the schedule for an application ensuring ownership/role authorization."""
        if self._app_repo is None:
            raise RuntimeError("ApplicationRepository not configured on RepaymentService")

        app = self._app_repo.get_application(application_id)
        if app is None:
            raise KeyError(f"Application {application_id!r} not found")

        if actor.role == "CUSTOMER" and app["owner_user_id"] != actor.user_id:
            raise PermissionError("Access denied")

        schedule = self._app_repo.get_schedule(application_id)
        if schedule is None:
            raise KeyError(f"Schedule for application {application_id!r} not found")

        return schedule, app

    def process_repayment(
        self,
        *,
        actor: Actor,
        application_id: str,
        amount: Decimal,
        paid_on: date,
        as_of: Optional[date] = None,
    ) -> RepaymentPostingResult:
        """Process repayment from API: verifies ownership and disbursed status, applies waterfall."""
        if self._app_repo is None or self._policy_repo is None:
            raise RuntimeError("Repositories not configured on RepaymentService")

        app = self._app_repo.get_application(application_id)
        if app is None:
            raise KeyError(f"Application {application_id!r} not found")

        if actor.role == "CUSTOMER" and app["owner_user_id"] != actor.user_id:
            raise PermissionError("Access denied")

        if app["status"] != "DISBURSED":
            raise InvalidApplicationStateException(
                f"Repayment can only be posted for DISBURSED loans (current status: {app['status']!r})"
            )

        schedule = self._app_repo.get_schedule(application_id)
        if schedule is None:
            raise KeyError(f"Schedule for application {application_id!r} not found")

        existing_allocations = self._app_repo.get_allocations(application_id)
        policy = self._policy_repo.get_active_policy()

        result = self.post_repayment(
            application_id=application_id,
            amount=amount,
            paid_on=paid_on,
            as_of=as_of,
            schedule=schedule,
            existing_allocations=existing_allocations,
            bucket_thresholds=policy.bucket_thresholds,
        )

        self._app_repo.save_repayment_with_allocations(
            application_id=application_id,
            amount_paid=amount,
            paid_on=paid_on,
            allocations=result.new_allocations,
            outstanding_principal=result.outstanding_principal,
            delinquency_bucket=result.delinquency_bucket,
            dpd=result.dpd,
        )

        self._app_repo.write_audit(
            actor_user_id=actor.user_id,
            action="POST_REPAYMENT",
            application_id=application_id,
            comment=f"Repayment of {amount} posted",
        )

        return result

    def run_eod_job(
        self,
        *,
        actor: Actor,
        as_of: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Recalculate delinquency buckets for all DISBURSED loans as of a specific date."""
        if self._app_repo is None or self._policy_repo is None:
            raise RuntimeError("Repositories not configured on RepaymentService")

        if actor.role != "ADMIN":
            raise PermissionError("Access denied: ADMIN role required")

        eval_date = as_of or date.today()
        disbursed_apps = self._app_repo.list_disbursed_applications()
        policy = self._policy_repo.get_active_policy()

        counts: Dict[str, int] = {}
        for app in disbursed_apps:
            schedule = self._app_repo.get_schedule(app["id"])
            if not schedule:
                continue
            allocations = self._app_repo.get_allocations(app["id"])
            dpd, bucket = self.recalculate_delinquency(
                as_of=eval_date,
                schedule=schedule,
                all_allocations=allocations,
                bucket_thresholds=policy.bucket_thresholds,
            )
            self._app_repo.update_application_status(
                app_id=app["id"],
                status="DISBURSED",
                delinquency_bucket=bucket,
                dpd=dpd,
            )
            counts[bucket] = counts.get(bucket, 0) + 1

        return {
            "as_of": eval_date.isoformat(),
            "total_processed": len(disbursed_apps),
            "counts_by_bucket": counts,
        }

    # ------------------------------------------------------------------ #
    # Pure calculation methods                                             #
    # ------------------------------------------------------------------ #

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
