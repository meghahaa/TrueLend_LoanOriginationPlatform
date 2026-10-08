"""
Repayments API — controllers only.
Routes:
  GET  /applications/{id}/schedule
  POST /applications/{id}/repayments
  POST /admin/jobs/eod-buckets
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import Actor, get_actor, require_role
from src.domain.exceptions import InvalidApplicationStateException
from src.domain.money import to_money
from src.services.repayment_service import RepaymentService


class ScheduleRowOut(BaseModel):
    installment_number: int
    due_date: str
    opening_balance: str
    principal_component: str
    interest_component: str
    emi_amount: str
    remaining_balance: str


class ScheduleResponse(BaseModel):
    application_id: str
    emi_amount: str
    total_principal: str
    total_interest: str
    total_payable: str
    rows: List[ScheduleRowOut]


class RepaymentRequest(BaseModel):
    amount: str
    paid_on: str


class AllocationOut(BaseModel):
    installment_number: int
    principal_allocated: str
    interest_allocated: str


class RepaymentResponse(BaseModel):
    application_id: str
    amount_paid: str
    paid_on: str
    outstanding_principal: str
    total_remaining_due: str
    dpd: int
    delinquency_bucket: str
    allocations: List[AllocationOut]


class EODJobRequest(BaseModel):
    as_of: Optional[str] = None


class EODJobResponse(BaseModel):
    as_of: str
    total_processed: int
    counts_by_bucket: Dict[str, int]


def make_repayments_router(repayment_service: RepaymentService) -> APIRouter:
    router = APIRouter(tags=["repayments"])

    @router.get("/applications/{app_id}/schedule", response_model=ScheduleResponse)
    def get_schedule(
        app_id: str,
        actor: Actor = Depends(get_actor),
    ) -> ScheduleResponse:
        try:
            schedule, app = repayment_service.get_schedule_for_actor(actor, app_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")

        rows_out = [
            ScheduleRowOut(
                installment_number=r.installment_number,
                due_date=r.due_date.isoformat(),
                opening_balance=str(r.opening_balance),
                principal_component=str(r.principal_component),
                interest_component=str(r.interest_component),
                emi_amount=str(r.emi_amount),
                remaining_balance=str(r.remaining_balance),
            )
            for r in schedule.rows
        ]

        return ScheduleResponse(
            application_id=app_id,
            emi_amount=str(schedule.emi_amount),
            total_principal=str(schedule.total_principal),
            total_interest=str(schedule.total_interest),
            total_payable=str(schedule.total_payable),
            rows=rows_out,
        )

    @router.post("/applications/{app_id}/repayments", response_model=RepaymentResponse)
    def post_repayment(
        app_id: str,
        body: RepaymentRequest,
        actor: Actor = Depends(get_actor),
    ) -> RepaymentResponse:
        try:
            amount_dec = to_money(body.amount)
            paid_on_date = date.fromisoformat(body.paid_on)
            result = repayment_service.process_repayment(
                actor=actor,
                application_id=app_id,
                amount=amount_dec,
                paid_on=paid_on_date,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied")
        except InvalidApplicationStateException as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        allocations_out = [
            AllocationOut(
                installment_number=a.installment_number,
                principal_allocated=str(a.principal_allocated),
                interest_allocated=str(a.interest_allocated),
            )
            for a in result.new_allocations
        ]

        return RepaymentResponse(
            application_id=result.application_id,
            amount_paid=str(result.amount_paid),
            paid_on=result.paid_on.isoformat(),
            outstanding_principal=str(result.outstanding_principal),
            total_remaining_due=str(result.total_remaining_due),
            dpd=result.dpd,
            delinquency_bucket=result.delinquency_bucket,
            allocations=allocations_out,
        )

    @router.post("/admin/jobs/eod-buckets", response_model=EODJobResponse)
    def run_eod_job(
        body: EODJobRequest = EODJobRequest(),
        actor: Actor = Depends(require_role("ADMIN")),
    ) -> EODJobResponse:
        try:
            as_of_date = date.fromisoformat(body.as_of) if body.as_of else None
            result = repayment_service.run_eod_job(actor=actor, as_of=as_of_date)
        except PermissionError:
            raise HTTPException(status_code=403, detail="Access denied: ADMIN required")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        return EODJobResponse(**result)

    return router
